"""
Model Registry - Central registry for ML model versions

This module provides centralized management of ML model versions,
performance tracking, and deployment lifecycle.
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStage(str, Enum):
    """Model deployment stages"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    """Represents a specific version of a model"""
    id: UUID
    model_name: str
    version: str
    artifact_path: str
    stage: ModelStage
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModelRegistration:
    """Result of model registration"""
    model_id: UUID
    model_name: str
    version: str
    registered_at: datetime


@dataclass
class PerformanceRecord:
    """Model performance evaluation record"""
    id: UUID
    model_name: str
    model_version: str
    metric_name: str
    metric_value: float
    evaluation_date: date
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    Central registry for all ML model versions.
    
    Manages model lifecycle, versioning, and performance tracking.
    """
    
    def __init__(self):
        """Initialize model registry"""
        self._models: Dict[str, Dict[str, ModelVersion]] = {}  # model_name -> {version -> ModelVersion}
        self._active_models: Dict[str, str] = {}  # model_name -> active_version
        self._performance_history: List[PerformanceRecord] = []
        logger.info("ModelRegistry initialized")
    
    def register_model(
        self,
        model_name: str,
        model_version: str,
        model_artifact_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelRegistration:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model (e.g., "sentiment_classifier")
            model_version: Version string (e.g., "1.0.0", "2023-12-01")
            model_artifact_path: Path to model artifact
            metadata: Optional metadata (framework, hyperparameters, etc.)
            
        Returns:
            ModelRegistration with registration details
        """
        if model_name not in self._models:
            self._models[model_name] = {}
        
        if model_version in self._models[model_name]:
            logger.warning(f"Model {model_name} version {model_version} already registered")
            return ModelRegistration(
                model_id=self._models[model_name][model_version].id,
                model_name=model_name,
                version=model_version,
                registered_at=self._models[model_name][model_version].created_at
            )
        
        model_id = uuid4()
        model = ModelVersion(
            id=model_id,
            model_name=model_name,
            version=model_version,
            artifact_path=model_artifact_path,
            stage=ModelStage.DEVELOPMENT,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self._models[model_name][model_version] = model
        
        # Set as active if it's the first version
        if model_name not in self._active_models:
            self._active_models[model_name] = model_version
            logger.info(f"Set {model_name} v{model_version} as active (first version)")
        
        logger.info(f"Registered model {model_name} version {model_version}")
        
        return ModelRegistration(
            model_id=model_id,
            model_name=model_name,
            version=model_version,
            registered_at=model.created_at
        )
    
    def get_active_model(self, model_name: str) -> Optional[ModelVersion]:
        """
        Get the currently active model version.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Active ModelVersion or None if not found
        """
        if model_name not in self._active_models:
            logger.warning(f"No active model found for {model_name}")
            return None
        
        active_version = self._active_models[model_name]
        return self._models[model_name].get(active_version)
    
    def list_model_versions(self, model_name: str) -> List[ModelVersion]:
        """
        List all versions of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of ModelVersion objects, sorted by creation date (newest first)
        """
        if model_name not in self._models:
            logger.warning(f"Model {model_name} not found in registry")
            return []
        
        versions = list(self._models[model_name].values())
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions
    
    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: str
    ) -> None:
        """
        Promote a model to a different stage.
        
        Args:
            model_name: Name of the model
            version: Version to promote
            stage: Target stage (staging, production)
            
        Raises:
            ValueError: If model or version not found, or invalid stage
        """
        if model_name not in self._models:
            raise ValueError(f"Model {model_name} not found in registry")
        
        if version not in self._models[model_name]:
            raise ValueError(f"Version {version} not found for model {model_name}")
        
        try:
            target_stage = ModelStage(stage)
        except ValueError:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {[s.value for s in ModelStage]}")
        
        model = self._models[model_name][version]
        old_stage = model.stage
        model.stage = target_stage
        
        # If promoting to production, set as active
        if target_stage == ModelStage.PRODUCTION:
            self._active_models[model_name] = version
            logger.info(f"Set {model_name} v{version} as active (promoted to production)")
        
        logger.info(f"Promoted {model_name} v{version} from {old_stage.value} to {target_stage.value}")
    
    def record_model_performance(
        self,
        model_name: str,
        version: str,
        metrics: Dict[str, float],
        evaluation_date: Optional[date] = None
    ) -> None:
        """
        Record performance metrics for a model version.
        
        Args:
            model_name: Name of the model
            version: Model version
            metrics: Dictionary of metric_name -> metric_value
            evaluation_date: Date of evaluation (defaults to today)
        """
        if model_name not in self._models:
            logger.warning(f"Model {model_name} not found, creating performance record anyway")
        elif version not in self._models[model_name]:
            logger.warning(f"Version {version} not found for {model_name}, creating performance record anyway")
        
        eval_date = evaluation_date or date.today()
        
        for metric_name, metric_value in metrics.items():
            record = PerformanceRecord(
                id=uuid4(),
                model_name=model_name,
                model_version=version,
                metric_name=metric_name,
                metric_value=metric_value,
                evaluation_date=eval_date,
                metadata={}
            )
            self._performance_history.append(record)
        
        # Update model's performance metrics if model exists
        if model_name in self._models and version in self._models[model_name]:
            self._models[model_name][version].performance_metrics.update(metrics)
        
        logger.info(f"Recorded performance for {model_name} v{version}: {metrics}")
    
    def get_performance_history(
        self,
        model_name: str,
        version: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100
    ) -> List[PerformanceRecord]:
        """
        Get performance history for a model.
        
        Args:
            model_name: Name of the model
            version: Optional version filter
            metric_name: Optional metric name filter
            limit: Maximum number of records to return
            
        Returns:
            List of PerformanceRecord objects, sorted by date (newest first)
        """
        records = [
            r for r in self._performance_history
            if r.model_name == model_name
            and (version is None or r.model_version == version)
            and (metric_name is None or r.metric_name == metric_name)
        ]
        
        records.sort(key=lambda r: r.evaluation_date, reverse=True)
        return records[:limit]
    
    def get_model_by_version(
        self,
        model_name: str,
        version: str
    ) -> Optional[ModelVersion]:
        """
        Get a specific model version.
        
        Args:
            model_name: Name of the model
            version: Version string
            
        Returns:
            ModelVersion or None if not found
        """
        if model_name not in self._models:
            return None
        return self._models[model_name].get(version)
    
    def list_all_models(self) -> List[str]:
        """
        List all registered model names.
        
        Returns:
            List of model names
        """
        return list(self._models.keys())
    
    def get_latest_version(self, model_name: str) -> Optional[ModelVersion]:
        """
        Get the latest version of a model (by creation date).
        
        Args:
            model_name: Name of the model
            
        Returns:
            Latest ModelVersion or None if not found
        """
        versions = self.list_model_versions(model_name)
        return versions[0] if versions else None
