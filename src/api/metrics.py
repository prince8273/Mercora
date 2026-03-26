"""Metrics API endpoint for Prometheus scraping and JSON summary"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.observability.metrics import get_metrics_collector

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics():
    """Prometheus metrics endpoint — raw text format for scraping."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/summary")
async def metrics_summary():
    """Human-readable JSON summary of system performance stats."""
    collector = get_metrics_collector()
    return collector.get_summary()
