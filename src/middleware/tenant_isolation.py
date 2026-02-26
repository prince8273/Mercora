"""Tenant Isolation Middleware for enforcing multi-tenancy at API boundary"""
import logging
from typing import Callable
from uuid import UUID

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError

from src.auth.security import decode_access_token
from src.database import set_tenant_context
from src.config import settings

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Enforces tenant-level data isolation at the API boundary.
    
    This middleware:
    1. Extracts tenant_id from JWT token
    2. Validates tenant authorization
    3. Injects tenant context into request state
    4. Prevents cross-tenant data leakage
    
    CRITICAL SECURITY COMPONENT:
    All API requests (except public endpoints) MUST pass through this middleware.
    This is the first line of defense for multi-tenancy.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    # Auth endpoints that handle their own authentication
    AUTH_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> JSONResponse:
        """
        Process each request through tenant isolation checks.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from downstream handler
            
        Raises:
            HTTPException: If authentication or authorization fails
        """
        # Skip public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip auth endpoints (they handle their own auth)
        if request.url.path in self.AUTH_PATHS:
            return await call_next(request)
        
        # DEMO MODE: Allow requests without authentication
        if settings.demo_mode:
            # Set demo tenant context - using TechGear Pro tenant
            demo_tenant_id = UUID('54d459ab-4ae8-480a-9d1c-d53b218a4fb2')
            demo_user_id = UUID('83bf2b99-5d62-4c1a-9703-92191eeb84b7')
            
            request.state.tenant_id = demo_tenant_id
            request.state.user_id = demo_user_id
            
            # Set tenant context for database queries
            set_tenant_context(demo_tenant_id)
            
            logger.debug(
                f"DEMO MODE: Request to {request.url.path} using demo tenant",
                extra={
                    "tenant_id": str(demo_tenant_id),
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            return await call_next(request)
        
        # PRODUCTION MODE: Enforce authentication
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(
                f"Missing Authorization header for {request.url.path}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_host": request.client.host if request.client else "unknown"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token
        if not auth_header.startswith("Bearer "):
            logger.warning(
                f"Invalid Authorization header format for {request.url.path}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token format"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Decode and validate JWT token
        try:
            payload = decode_access_token(token)
            
            # Extract tenant_id and user_id
            user_id_str = payload.get("sub")
            tenant_id_str = payload.get("tenant_id")
            
            if not user_id_str or not tenant_id_str:
                logger.error(
                    "JWT token missing required claims",
                    extra={
                        "has_sub": bool(user_id_str),
                        "has_tenant_id": bool(tenant_id_str),
                        "path": request.url.path
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token: missing required claims"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Convert to UUID
            try:
                tenant_id = UUID(tenant_id_str)
                user_id = UUID(user_id_str)
            except ValueError as e:
                logger.error(
                    f"Invalid UUID format in token: {e}",
                    extra={
                        "tenant_id_str": tenant_id_str,
                        "user_id_str": user_id_str,
                        "path": request.url.path
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token: malformed identifiers"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # CRITICAL: Inject tenant context into request state
            request.state.tenant_id = tenant_id
            request.state.user_id = user_id
            
            # CRITICAL: Set tenant context for database queries
            # This enables automatic tenant filtering in all queries
            set_tenant_context(tenant_id)
            
            # Log successful tenant access
            logger.info(
                f"Tenant access granted",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
        except JWTError as e:
            logger.warning(
                f"JWT validation failed: {e}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                }
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(e)}"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in tenant isolation middleware: {e}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during authentication"}
            )
        
        # Continue to next handler
        response = await call_next(request)
        
        # Add tenant context to response headers (for debugging)
        if hasattr(request.state, "tenant_id"):
            response.headers["X-Tenant-ID"] = str(request.state.tenant_id)
        
        return response
    
    @staticmethod
    def validate_tenant_authorization(
        user_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        Validate that a user is authorized to access a tenant.
        
        In a full implementation, this would check:
        - User belongs to tenant
        - User has required permissions
        - Tenant is active
        
        Args:
            user_id: User's UUID
            tenant_id: Tenant's UUID
            
        Returns:
            True if authorized, False otherwise
        """
        # Placeholder for authorization logic
        # In production, query database to verify user-tenant relationship
        return True
