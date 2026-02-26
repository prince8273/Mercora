"""Validation result schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Individual validation error"""
    field: str = Field(..., description="Field that failed validation")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Error message")


class ValidationWarning(BaseModel):
    """Individual validation warning"""
    field: str = Field(..., description="Field with warning")
    warning_type: str = Field(..., description="Type of warning")
    message: str = Field(..., description="Warning message")


class DataValidationResult(BaseModel):
    """Result of data validation"""
    is_valid: bool = Field(..., description="Whether data passed validation")
    record_id: Optional[str] = Field(None, description="ID of validated record")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationWarning] = Field(default_factory=list, description="Validation warnings")
    validated_data: Optional[Dict[str, Any]] = Field(None, description="Validated and cleaned data")


class BatchValidationResult(BaseModel):
    """Result of batch validation"""
    total_records: int = Field(..., ge=0, description="Total records processed")
    valid_records: int = Field(..., ge=0, description="Number of valid records")
    invalid_records: int = Field(..., ge=0, description="Number of invalid records")
    validation_results: List[DataValidationResult] = Field(default_factory=list, description="Individual results")
    summary: Dict[str, int] = Field(default_factory=dict, description="Error type counts")


class NormalizationResult(BaseModel):
    """Result of SKU normalization"""
    original_sku: str = Field(..., description="Original SKU")
    normalized_sku: str = Field(..., description="Normalized SKU")
    marketplace: Optional[str] = Field(None, description="Marketplace")
    normalization_applied: bool = Field(..., description="Whether normalization changed the SKU")


class ProductMapping(BaseModel):
    """Product equivalence mapping"""
    sku1: str = Field(..., description="First product SKU")
    normalized_sku1: str = Field(..., description="Normalized first SKU")
    marketplace1: str = Field(..., description="First marketplace")
    sku2: str = Field(..., description="Second product SKU")
    normalized_sku2: str = Field(..., description="Normalized second SKU")
    marketplace2: str = Field(..., description="Second marketplace")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping confidence")
    mapping_type: str = Field(..., description="Type of mapping (exact, similarity, weak)")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="SKU similarity score")


class DeduplicationResult(BaseModel):
    """Result of deduplication"""
    original_count: int = Field(..., ge=0, description="Original record count")
    deduplicated_count: int = Field(..., ge=0, description="Deduplicated record count")
    duplicates_removed: int = Field(..., ge=0, description="Number of duplicates removed")
    duplicate_groups: int = Field(..., ge=0, description="Number of duplicate groups found")


class MissingDataReport(BaseModel):
    """Report on missing data"""
    record_id: Optional[str] = Field(None, description="Record ID")
    missing_fields: List[str] = Field(default_factory=list, description="Missing optional fields")
    critical_missing: List[str] = Field(default_factory=list, description="Missing critical fields")
    has_missing_data: bool = Field(..., description="Whether record has any missing data")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    defaults_applied: List[str] = Field(default_factory=list, description="Fields with defaults applied")
    interpolated_fields: List[str] = Field(default_factory=list, description="Fields that were interpolated")


class DataProcessingReport(BaseModel):
    """Complete data processing report"""
    validation_result: BatchValidationResult = Field(..., description="Validation results")
    deduplication_result: DeduplicationResult = Field(..., description="Deduplication results")
    missing_data_summary: Dict[str, int] = Field(default_factory=dict, description="Missing data summary")
    spam_filtered: int = Field(default=0, ge=0, description="Number of spam records filtered")
    processing_timestamp: str = Field(..., description="When processing occurred")
