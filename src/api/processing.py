"""API endpoints for data processing pipeline"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from src.processing.pipeline import ProcessingPipeline
from src.processing.spam_filter import SpamFilter


router = APIRouter(prefix="/processing", tags=["processing"])


# Request/Response Models
class ProductProcessingRequest(BaseModel):
    """Request to process product data"""
    products: List[Dict[str, Any]] = Field(..., description="List of raw product data")
    source: str = Field(default="api", description="Data source name")
    skip_validation: bool = Field(default=False, description="Skip validation stage")
    skip_deduplication: bool = Field(default=False, description="Skip deduplication stage")


class ReviewProcessingRequest(BaseModel):
    """Request to process review data"""
    reviews: List[Dict[str, Any]] = Field(..., description="List of raw review data")
    source: str = Field(default="api", description="Data source name")
    skip_validation: bool = Field(default=False, description="Skip validation stage")
    skip_spam_filtering: bool = Field(default=False, description="Skip spam filtering stage")
    skip_deduplication: bool = Field(default=False, description="Skip deduplication stage")


class SpamCheckRequest(BaseModel):
    """Request to check reviews for spam"""
    reviews: List[Dict[str, Any]] = Field(..., description="List of reviews to check")


class LineageRequest(BaseModel):
    """Request to get pipeline lineage"""
    pipeline_id: str = Field(..., description="Pipeline execution ID")


# Dependency: Get pipeline instance
def get_pipeline(tenant_id: UUID = None) -> ProcessingPipeline:
    """Get processing pipeline instance"""
    if tenant_id is None:
        tenant_id = uuid4()  # Default tenant for MVP
    return ProcessingPipeline(tenant_id=tenant_id)


@router.post("/products")
async def process_products(
    request: ProductProcessingRequest,
    pipeline: ProcessingPipeline = Depends(get_pipeline)
) -> Dict[str, Any]:
    """
    Process product data through the complete pipeline.
    
    Pipeline stages:
    1. Validation - Validate against schema
    2. Normalization - Normalize SKUs
    3. Deduplication - Remove duplicates
    4. Missing Data Handling - Handle missing fields
    
    Returns processed products with lineage information.
    """
    try:
        result = pipeline.process_products(
            products=request.products,
            source=request.source,
            skip_validation=request.skip_validation,
            skip_deduplication=request.skip_deduplication
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/reviews")
async def process_reviews(
    request: ReviewProcessingRequest,
    pipeline: ProcessingPipeline = Depends(get_pipeline)
) -> Dict[str, Any]:
    """
    Process review data through the complete pipeline.
    
    Pipeline stages:
    1. Validation - Validate against schema
    2. Spam Filtering - Remove spam reviews
    3. Deduplication - Remove duplicates
    4. Missing Data Handling - Handle missing fields
    
    Returns processed reviews with lineage information.
    """
    try:
        result = pipeline.process_reviews(
            reviews=request.reviews,
            source=request.source,
            skip_validation=request.skip_validation,
            skip_spam_filtering=request.skip_spam_filtering,
            skip_deduplication=request.skip_deduplication
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/spam-check")
async def check_spam(request: SpamCheckRequest) -> Dict[str, Any]:
    """
    Check reviews for spam without full pipeline processing.
    
    Returns spam detection results with confidence scores.
    """
    try:
        spam_filter = SpamFilter(spam_threshold=0.5)
        result = spam_filter.batch_check_spam(request.reviews)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spam check failed: {str(e)}")


@router.get("/lineage/{pipeline_id}")
async def get_pipeline_lineage(
    pipeline_id: str,
    pipeline: ProcessingPipeline = Depends(get_pipeline)
) -> Dict[str, Any]:
    """
    Get complete lineage for a pipeline execution.
    
    Returns:
    - All transformation nodes
    - All transformation edges
    - Pipeline statistics
    """
    try:
        lineage = pipeline.get_lineage_for_pipeline(pipeline_id)
        if 'error' in lineage:
            raise HTTPException(status_code=404, detail=lineage['error'])
        return lineage
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@router.get("/lineage/export")
async def export_lineage_graph(
    pipeline: ProcessingPipeline = Depends(get_pipeline)
) -> Dict[str, Any]:
    """
    Export complete lineage graph for visualization.
    
    Returns graph data with all nodes and edges.
    """
    try:
        graph = pipeline.export_lineage_graph()
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export lineage: {str(e)}")


@router.get("/statistics")
async def get_pipeline_statistics(
    pipeline: ProcessingPipeline = Depends(get_pipeline)
) -> Dict[str, Any]:
    """
    Get overall pipeline statistics.
    
    Returns:
    - Total pipelines executed
    - Total records processed
    - Spam filter statistics
    - All pipeline summaries
    """
    try:
        stats = pipeline.get_pipeline_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "processing-pipeline"}
