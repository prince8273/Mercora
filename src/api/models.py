"""Model management API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.database import get_db
from src.ml.model_registry import ModelRegistry
from src.ml.drift_detector import DriftDetector
from src.ml.retraining_service import RetrainingService
from src.models.model_registry import ModelType

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/versions")
async def list_model_versions(
    tenant_id: str = Query(..., description="Tenant ID"),
    model_type: Optional[str] = Query(None, description="Model type filter"),
    limit: int = Query(10, description="Maximum number of versions"),
    db: Session = Depends(get_db)
):
    """
    List model versions.
    
    Returns list of registered model versions with metadata.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        registry = ModelRegistry(db, tenant_uuid)
        
        # Parse model type
        model_type_enum = None
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model type: {model_type}"
                )
        
        versions = registry.get_model_versions(model_type_enum, limit)
        
        return {
            "success": True,
            "versions": [
                {
                    "id": str(v.id),
                    "model_type": v.model_type.value,
                    "model_name": v.model_name,
                    "version": v.version,
                    "framework": v.framework,
                    "algorithm": v.algorithm,
                    "status": v.status.value,
                    "is_active": v.is_active,
                    "metrics": v.metrics,
                    "trained_at": v.trained_at.isoformat() if v.trained_at else None,
                    "created_at": v.created_at.isoformat()
                }
                for v in versions
            ],
            "total": len(versions)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_models(
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db)
):
    """
    Get currently active models for all types.
    
    Returns the active model version for each model type.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        registry = ModelRegistry(db, tenant_uuid)
        
        active_models = {}
        
        for model_type in ModelType:
            model = registry.get_active_model(model_type)
            if model:
                active_models[model_type.value] = {
                    "id": str(model.id),
                    "version": model.version,
                    "model_name": model.model_name,
                    "framework": model.framework,
                    "algorithm": model.algorithm,
                    "metrics": model.metrics,
                    "trained_at": model.trained_at.isoformat() if model.trained_at else None
                }
        
        return {
            "success": True,
            "active_models": active_models
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{model_version_id}/promote")
async def promote_model(
    model_version_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db)
):
    """
    Promote a model version to active status.
    
    Demotes any currently active model of the same type.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        version_uuid = UUID(model_version_id)
        
        registry = ModelRegistry(db, tenant_uuid)
        promoted_model = registry.promote_model(version_uuid)
        
        return {
            "success": True,
            "model": {
                "id": str(promoted_model.id),
                "model_type": promoted_model.model_type.value,
                "version": promoted_model.version,
                "status": promoted_model.status.value,
                "is_active": promoted_model.is_active
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{model_version_id}")
async def get_performance_history(
    model_version_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    days: int = Query(30, description="Days of history"),
    db: Session = Depends(get_db)
):
    """
    Get performance history for a model version.
    
    Returns time-series performance metrics.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        version_uuid = UUID(model_version_id)
        
        registry = ModelRegistry(db, tenant_uuid)
        history = registry.get_performance_history(version_uuid, days)
        
        return {
            "success": True,
            "model_version_id": model_version_id,
            "history": [
                {
                    "evaluation_date": p.evaluation_date.isoformat(),
                    "metrics": p.metrics,
                    "predictions_count": p.predictions_count,
                    "actuals_count": p.actuals_count,
                    "improvement_over_baseline": p.improvement_over_baseline
                }
                for p in history
            ],
            "total_records": len(history)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/alerts")
async def get_drift_alerts(
    tenant_id: str = Query(..., description="Tenant ID"),
    model_type: Optional[str] = Query(None, description="Model type filter"),
    unresolved_only: bool = Query(True, description="Only unresolved alerts"),
    db: Session = Depends(get_db)
):
    """
    Get drift alerts.
    
    Returns list of detected drift events.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        registry = ModelRegistry(db, tenant_uuid)
        
        # Parse model type
        model_type_enum = None
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model type: {model_type}"
                )
        
        alerts = registry.get_drift_alerts(model_type_enum, unresolved_only)
        
        return {
            "success": True,
            "alerts": [
                {
                    "id": str(a.id),
                    "model_version_id": str(a.model_version_id),
                    "detected_at": a.detected_at.isoformat(),
                    "drift_type": a.drift_type,
                    "metric_name": a.metric_name,
                    "baseline_value": a.baseline_value,
                    "current_value": a.current_value,
                    "drift_percentage": a.drift_percentage,
                    "severity": a.severity,
                    "resolved": a.resolved
                }
                for a in alerts
            ],
            "total": len(alerts)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drift/check")
async def check_drift(
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db)
):
    """
    Check for drift in all active models.
    
    Runs drift detection and returns results.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        detector = DriftDetector(db, tenant_uuid)
        
        results = detector.check_all_models()
        
        return {
            "success": True,
            "drift_check_results": results
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retraining/jobs")
async def list_retraining_jobs(
    tenant_id: str = Query(..., description="Tenant ID"),
    model_type: Optional[str] = Query(None, description="Model type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    limit: int = Query(10, description="Maximum number of jobs"),
    db: Session = Depends(get_db)
):
    """
    List retraining jobs.
    
    Returns list of retraining jobs with status.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        registry = ModelRegistry(db, tenant_uuid)
        
        # Parse model type
        model_type_enum = None
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model type: {model_type}"
                )
        
        jobs = registry.get_retraining_jobs(model_type_enum, status, limit)
        
        return {
            "success": True,
            "jobs": [
                {
                    "id": str(j.id),
                    "model_type": j.model_type.value,
                    "trigger_reason": j.trigger_reason,
                    "status": j.status,
                    "created_at": j.created_at.isoformat(),
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "duration_seconds": j.duration_seconds,
                    "new_model_version_id": str(j.new_model_version_id) if j.new_model_version_id else None,
                    "metrics": j.metrics,
                    "error_message": j.error_message
                }
                for j in jobs
            ],
            "total": len(jobs)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retraining/trigger")
async def trigger_retraining(
    tenant_id: str = Query(..., description="Tenant ID"),
    model_type: str = Query(..., description="Model type"),
    reason: str = Query("manual", description="Trigger reason"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger model retraining.
    
    Creates a retraining job for the specified model type.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        
        # Parse model type
        try:
            model_type_enum = ModelType(model_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {model_type}"
            )
        
        registry = ModelRegistry(db, tenant_uuid)
        job = registry.trigger_retraining(model_type_enum, reason)
        
        return {
            "success": True,
            "job": {
                "id": str(job.id),
                "model_type": job.model_type.value,
                "trigger_reason": job.trigger_reason,
                "status": job.status,
                "created_at": job.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retraining/check-and-trigger")
async def check_and_trigger_retraining(
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db)
):
    """
    Check all models and trigger retraining if needed.
    
    Automatically triggers retraining for models below performance thresholds.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        service = RetrainingService(db, tenant_uuid)
        
        results = service.check_and_trigger_retraining()
        
        return {
            "success": True,
            "results": results
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_models(
    model_a_id: str = Query(..., description="First model version ID"),
    model_b_id: str = Query(..., description="Second model version ID"),
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db)
):
    """
    Compare two model versions (A/B testing).
    
    Returns performance comparison between two models.
    """
    try:
        tenant_uuid = UUID(tenant_id)
        model_a_uuid = UUID(model_a_id)
        model_b_uuid = UUID(model_b_id)
        
        service = RetrainingService(db, tenant_uuid)
        comparison = service.compare_models_ab_test(model_a_uuid, model_b_uuid)
        
        return {
            "success": True,
            "comparison": comparison
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
