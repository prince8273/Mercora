"""Data lineage API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from uuid import UUID

from src.processing.lineage_tracker import LineageTracker

router = APIRouter(prefix="/api/lineage", tags=["lineage"])

# In-memory lineage tracker (in production, this would be persistent)
_lineage_trackers = {}


def get_lineage_tracker(tenant_id: UUID) -> LineageTracker:
    """Get or create lineage tracker for tenant"""
    if tenant_id not in _lineage_trackers:
        _lineage_trackers[tenant_id] = LineageTracker(tenant_id)
    return _lineage_trackers[tenant_id]


@router.get("/pipelines")
async def list_pipelines(
    tenant_id: str = Query(..., description="Tenant ID")
):
    """
    List all pipeline executions with summary statistics.
    
    Returns summary information for all tracked pipeline executions.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        tracker = get_lineage_tracker(tenant_uuid)
        pipelines = tracker.get_all_pipelines()
        
        return {
            "success": True,
            "pipelines": pipelines,
            "total_pipelines": len(pipelines)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline_lineage(
    pipeline_id: str,
    tenant_id: str = Query(..., description="Tenant ID")
):
    """
    Get complete lineage for a specific pipeline execution.
    
    Returns all nodes, edges, and statistics for the pipeline.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        tracker = get_lineage_tracker(tenant_uuid)
        lineage = tracker.get_pipeline_lineage(pipeline_id)
        
        if not lineage.get('nodes'):
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        return {
            "success": True,
            "lineage": lineage
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}")
async def get_node_lineage(
    node_id: str,
    tenant_id: str = Query(..., description="Tenant ID")
):
    """
    Get lineage for a specific data node.
    
    Returns the node, its ancestors, and all transformations in its lineage.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        tracker = get_lineage_tracker(tenant_uuid)
        lineage = tracker.get_lineage_for_node(node_id)
        
        if 'error' in lineage:
            raise HTTPException(status_code=404, detail=lineage['error'])
        
        return {
            "success": True,
            "lineage": lineage
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph")
async def export_lineage_graph(
    tenant_id: str = Query(..., description="Tenant ID")
):
    """
    Export complete lineage graph for visualization.
    
    Returns all nodes and edges in a format suitable for graph visualization.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        tracker = get_lineage_tracker(tenant_uuid)
        graph = tracker.export_lineage_graph()
        
        return {
            "success": True,
            "graph": graph
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_lineage_statistics(
    tenant_id: str = Query(..., description="Tenant ID")
):
    """
    Get overall lineage tracking statistics.
    
    Returns aggregate statistics across all pipelines.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        tracker = get_lineage_tracker(tenant_uuid)
        pipelines = tracker.get_all_pipelines()
        
        # Calculate aggregate statistics
        total_records_in = sum(p['records_in'] for p in pipelines)
        total_records_out = sum(p['records_out'] for p in pipelines)
        total_transformations = sum(p['transformation_count'] for p in pipelines)
        
        avg_retention_rate = (
            sum(p['retention_rate'] for p in pipelines) / len(pipelines)
            if pipelines else 0.0
        )
        
        return {
            "success": True,
            "statistics": {
                "total_pipelines": len(pipelines),
                "total_records_in": total_records_in,
                "total_records_out": total_records_out,
                "total_data_loss": total_records_in - total_records_out,
                "total_transformations": total_transformations,
                "average_retention_rate": avg_retention_rate
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
