"""Metrics API endpoint for Prometheus scraping"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
