"""WebSocket API endpoints for real-time updates"""
import json
import logging
from datetime import datetime
from uuid import UUID
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.exceptions import WebSocketException

from src.auth.dependencies import get_current_user_from_token

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Map of query_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> (user_id, tenant_id) for authorization
        self.connection_auth: Dict[WebSocket, tuple] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        query_id: str,
        user_id: UUID,
        tenant_id: UUID
    ):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            query_id: Query ID to subscribe to
            user_id: User ID for authorization
            tenant_id: Tenant ID for isolation
        """
        await websocket.accept()
        
        if query_id not in self.active_connections:
            self.active_connections[query_id] = set()
        
        self.active_connections[query_id].add(websocket)
        self.connection_auth[websocket] = (user_id, tenant_id)
        
        logger.info(
            f"WebSocket connected: query_id={query_id}, "
            f"user_id={user_id}, tenant_id={tenant_id}"
        )
    
    def disconnect(self, websocket: WebSocket, query_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            query_id: Query ID the connection was subscribed to
        """
        if query_id in self.active_connections:
            self.active_connections[query_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[query_id]:
                del self.active_connections[query_id]
        
        if websocket in self.connection_auth:
            user_id, tenant_id = self.connection_auth[websocket]
            del self.connection_auth[websocket]
            
            logger.info(
                f"WebSocket disconnected: query_id={query_id}, "
                f"user_id={user_id}, tenant_id={tenant_id}"
            )
    
    async def send_progress_update(
        self,
        query_id: str,
        message: Dict,
        tenant_id: UUID
    ):
        """
        Send progress update to all connections subscribed to a query.
        
        Only sends to connections belonging to the same tenant.
        
        Args:
            query_id: Query ID to send update for
            message: Progress update message
            tenant_id: Tenant ID for isolation
        """
        if query_id not in self.active_connections:
            return
        
        # Filter connections by tenant
        connections_to_notify = [
            ws for ws in self.active_connections[query_id]
            if ws in self.connection_auth
            and self.connection_auth[ws][1] == tenant_id
        ]
        
        # Send to all authorized connections
        disconnected = []
        for connection in connections_to_notify:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, query_id)
    
    async def broadcast_to_tenant(
        self,
        tenant_id: UUID,
        message: Dict
    ):
        """
        Broadcast a message to all connections for a tenant.
        
        Args:
            tenant_id: Tenant ID to broadcast to
            message: Message to broadcast
        """
        # Find all connections for this tenant
        connections_to_notify = [
            ws for ws, (_, ws_tenant_id) in self.connection_auth.items()
            if ws_tenant_id == tenant_id
        ]
        
        # Send to all connections
        disconnected = []
        for connection in connections_to_notify:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            # Find query_id for this connection
            for query_id, connections in self.active_connections.items():
                if connection in connections:
                    self.disconnect(connection, query_id)
                    break


# Global connection manager
manager = ConnectionManager()


@router.websocket("/query/{query_id}")
async def websocket_query_updates(
    websocket: WebSocket,
    query_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time query execution updates.
    
    Clients can connect to this endpoint to receive progress updates
    during query execution, including:
    - Agent execution status
    - Intermediate results
    - Completion notifications
    - Error notifications
    
    Args:
        websocket: WebSocket connection
        query_id: Query ID to subscribe to updates for
        token: JWT authentication token (passed as query parameter)
    
    Example client usage:
        ```javascript
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/query/${queryId}?token=${jwtToken}`);
        
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Progress update:', update);
        };
        ```
    """
    try:
        # Authenticate user from token
        user = await get_current_user_from_token(token)
        
        if not user:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token"
            )
        
        # Connect WebSocket
        await manager.connect(
            websocket,
            query_id,
            user.id,
            user.tenant_id
        )
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "query_id": query_id,
            "message": "Connected to query updates"
        })
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for messages from client (e.g., ping/pong)
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "query_id": query_id
                    })
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, query_id)
            logger.info(f"WebSocket disconnected normally: query_id={query_id}")
        
    except WebSocketException:
        # Re-raise WebSocket exceptions
        raise
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


# Helper function to send progress updates (to be called from query execution)
async def send_query_progress(
    query_id: str,
    tenant_id: UUID,
    progress_type: str,
    message: str,
    data: Dict = None
):
    """
    Send a progress update for a query.
    
    This function should be called from the query execution logic
    to send real-time updates to connected clients.
    
    Args:
        query_id: Query ID
        tenant_id: Tenant ID for isolation
        progress_type: Type of progress update (e.g., 'agent_started', 'agent_completed', 'error')
        message: Human-readable progress message
        data: Optional additional data
    """
    update = {
        "type": progress_type,
        "query_id": query_id,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data:
        update["data"] = data
    
    await manager.send_progress_update(query_id, update, tenant_id)


# Export manager for use in other modules
__all__ = ["router", "manager", "send_query_progress"]
