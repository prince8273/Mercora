"""Query history API endpoints"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


# Mock query history storage (in-memory for now)
# In full implementation, this would be stored in database
_query_history: List[Dict[str, Any]] = []


@router.get("")
async def get_query_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get query history with pagination
    """
    try:
        # Sort by timestamp (most recent first)
        sorted_history = sorted(
            _query_history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_history[offset:offset + limit]
        
        return {
            "total": len(_query_history),
            "limit": limit,
            "offset": offset,
            "queries": paginated
        }
        
    except Exception as e:
        logger.error(f"Error fetching query history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch query history: {str(e)}")


@router.post("")
async def add_query_to_history(
    query_text: str,
    analysis_type: str,
    confidence_score: float,
    execution_time: float = 0.0
) -> Dict[str, Any]:
    """
    Add a query to history
    """
    try:
        query_entry = {
            "id": str(uuid4()),
            "query": query_text,
            "analysis_type": analysis_type,
            "confidence": confidence_score,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        _query_history.append(query_entry)
        
        # Keep only last 1000 queries in memory
        if len(_query_history) > 1000:
            _query_history.pop(0)
        
        return query_entry
        
    except Exception as e:
        logger.error(f"Error adding query to history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add query to history: {str(e)}")


@router.get("/{query_id}")
async def get_query_details(query_id: str) -> Dict[str, Any]:
    """
    Get details of a specific query from history
    """
    try:
        for query in _query_history:
            if query.get("id") == query_id:
                return query
        
        raise HTTPException(status_code=404, detail="Query not found in history")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching query details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch query details: {str(e)}")


# Initialize with some mock data for demonstration
def _initialize_mock_history():
    """Initialize with some mock query history"""
    if not _query_history:
        mock_queries = [
            {
                "id": str(uuid4()),
                "query": "Why is product SKU-123 underperforming?",
                "analysis_type": "all",
                "confidence": 0.89,
                "execution_time": 2.3,
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "query": "What are customers saying about our new product line?",
                "analysis_type": "sentiment",
                "confidence": 0.92,
                "execution_time": 1.8,
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "query": "How do our prices compare to competitors?",
                "analysis_type": "pricing",
                "confidence": 0.85,
                "execution_time": 2.1,
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "query": "Which products are at risk of stockout?",
                "analysis_type": "all",
                "confidence": 0.78,
                "execution_time": 1.5,
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "query": "Analyze pricing and customer sentiment",
                "analysis_type": "all",
                "confidence": 0.91,
                "execution_time": 2.7,
                "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            },
        ]
        _query_history.extend(mock_queries)


# Initialize mock data on module load
_initialize_mock_history()
