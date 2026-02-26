"""Data quality schemas for QA Agent"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class Anomaly(BaseModel):
    """Detected anomaly in data"""
    type: str = Field(..., description="Type of anomaly (e.g., price_outlier, missing_field)")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    description: str = Field(..., description="Human-readable description of the anomaly")
    affected_entities: List[str] = Field(default_factory=list, description="IDs of affected entities")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in anomaly detection")


class MissingData(BaseModel):
    """Missing data information"""
    field: str = Field(..., description="Name of missing field")
    impact: str = Field(..., description="Impact level: low, medium, high, critical")
    affected_count: int = Field(..., ge=0, description="Number of entities affected")
    recommendation: Optional[str] = Field(None, description="Recommendation to fix")


class QualityDimension(BaseModel):
    """Individual quality dimension score"""
    score: float = Field(..., ge=0.0, le=1.0, description="Dimension score")
    issues_count: int = Field(default=0, ge=0, description="Number of issues found")
    details: Optional[str] = Field(None, description="Additional details")


class DataQualityDimensions(BaseModel):
    """Quality scores across different dimensions"""
    completeness: QualityDimension = Field(..., description="Data completeness score")
    validity: QualityDimension = Field(..., description="Data validity score")
    freshness: QualityDimension = Field(..., description="Data freshness score")
    consistency: QualityDimension = Field(..., description="Data consistency score")
    accuracy: QualityDimension = Field(..., description="Data accuracy score")


class DataQualityReport(BaseModel):
    """Complete data quality assessment report"""
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    dimensions: DataQualityDimensions = Field(..., description="Quality dimension scores")
    anomalies: List[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    missing_data: List[MissingData] = Field(default_factory=list, description="Missing data issues")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    entities_assessed: int = Field(..., ge=0, description="Number of entities assessed")
    assessment_timestamp: str = Field(..., description="When assessment was performed")


class ProductQualityMetadata(BaseModel):
    """Quality metadata for a single product"""
    product_id: UUID
    quality_score: float = Field(..., ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ReviewQualityMetadata(BaseModel):
    """Quality metadata for reviews"""
    product_id: UUID
    total_reviews: int
    quality_score: float = Field(..., ge=0.0, le=1.0)
    spam_detected: int = Field(default=0)
    low_quality_count: int = Field(default=0)
    issues: List[str] = Field(default_factory=list)
