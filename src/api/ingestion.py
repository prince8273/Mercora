"""Data ingestion API endpoints"""
import logging
import io
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.database import get_db
from src.models.product import Product
from src.models.review import Review
from src.models.user import User
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.scheduled_service import get_scheduled_service
from src.auth.dependencies import get_current_active_user, get_tenant_id
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionJobResponse(BaseModel):
    """Response for ingestion job"""
    job_id: str
    status: str
    message: str
    records_processed: int = 0


class IngestionStatusResponse(BaseModel):
    """Response for ingestion status"""
    job_id: str
    status: str
    records_ingested: int
    records_validated: int
    records_rejected: int
    errors: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# In-memory job tracking (in production, use database or Redis)
ingestion_jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/upload/products", response_model=IngestionJobResponse)
async def upload_products_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload products via CSV file (TENANT-ISOLATED).
    
    CSV Format:
    sku,name,category,price,currency,marketplace,inventory_level
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    job_id = str(uuid4())
    
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        products_data = []
        for row in csv_reader:
            products_data.append(row)
        
        logger.info(f"Received CSV with {len(products_data)} products")
        
        # Create job record
        ingestion_jobs[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'records_ingested': len(products_data),
            'records_validated': 0,
            'records_rejected': 0,
            'errors': [],
            'started_at': datetime.utcnow(),
            'completed_at': None
        }
        
        # Process in background
        if background_tasks:
            background_tasks.add_task(
                _process_products_data,
                job_id,
                products_data,
                tenant_id,
                db
            )
        else:
            # Process synchronously if no background tasks
            await _process_products_data(job_id, products_data, tenant_id, db)
        
        return IngestionJobResponse(
            job_id=job_id,
            status="processing",
            message=f"Processing {len(products_data)} products",
            records_processed=len(products_data)
        )
        
    except Exception as e:
        logger.error(f"Failed to process CSV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.post("/upload/reviews", response_model=IngestionJobResponse)
async def upload_reviews_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload reviews via CSV file (TENANT-ISOLATED).
    
    CSV Format:
    product_sku,rating,review_text,reviewer_name,review_date
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    job_id = str(uuid4())
    
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        reviews_data = []
        for row in csv_reader:
            reviews_data.append(row)
        
        logger.info(f"Received CSV with {len(reviews_data)} reviews")
        
        # Create job record
        ingestion_jobs[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'records_ingested': len(reviews_data),
            'records_validated': 0,
            'records_rejected': 0,
            'errors': [],
            'started_at': datetime.utcnow(),
            'completed_at': None
        }
        
        # Process in background
        if background_tasks:
            background_tasks.add_task(
                _process_reviews_data,
                job_id,
                reviews_data,
                tenant_id,
                db
            )
        else:
            await _process_reviews_data(job_id, reviews_data, tenant_id, db)
        
        return IngestionJobResponse(
            job_id=job_id,
            status="processing",
            message=f"Processing {len(reviews_data)} reviews",
            records_processed=len(reviews_data)
        )
        
    except Exception as e:
        logger.error(f"Failed to process CSV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.post("/upload/json", response_model=IngestionJobResponse)
async def upload_json_data(
    file: UploadFile = File(...),
    data_type: str = "products",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload data via JSON file (TENANT-ISOLATED).
    
    Supports: products, reviews
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")
    
    job_id = str(uuid4())
    
    try:
        # Read JSON file
        contents = await file.read()
        json_data = json.loads(contents.decode('utf-8'))
        
        if not isinstance(json_data, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of objects")
        
        logger.info(f"Received JSON with {len(json_data)} {data_type} records")
        
        # Create job record
        ingestion_jobs[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'records_ingested': len(json_data),
            'records_validated': 0,
            'records_rejected': 0,
            'errors': [],
            'started_at': datetime.utcnow(),
            'completed_at': None
        }
        
        # Process based on data type
        if data_type == "products":
            if background_tasks:
                background_tasks.add_task(_process_products_data, job_id, json_data, tenant_id, db)
            else:
                await _process_products_data(job_id, json_data, tenant_id, db)
        elif data_type == "reviews":
            if background_tasks:
                background_tasks.add_task(_process_reviews_data, job_id, json_data, tenant_id, db)
            else:
                await _process_reviews_data(job_id, json_data, tenant_id, db)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported data type: {data_type}")
        
        return IngestionJobResponse(
            job_id=job_id,
            status="processing",
            message=f"Processing {len(json_data)} {data_type} records",
            records_processed=len(json_data)
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process JSON upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/status/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(job_id: str):
    """Get status of an ingestion job"""
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = ingestion_jobs[job_id]
    
    return IngestionStatusResponse(
        job_id=job['job_id'],
        status=job['status'],
        records_ingested=job['records_ingested'],
        records_validated=job['records_validated'],
        records_rejected=job['records_rejected'],
        errors=job['errors'],
        started_at=job['started_at'],
        completed_at=job['completed_at']
    )


@router.get("/jobs")
async def list_ingestion_jobs(limit: int = 50):
    """List recent ingestion jobs"""
    jobs = list(ingestion_jobs.values())
    jobs.sort(key=lambda x: x['started_at'], reverse=True)
    return {
        "total": len(jobs),
        "jobs": jobs[:limit]
    }


async def _process_products_data(job_id: str, products_data: List[Dict[str, Any]], tenant_id: UUID, db: AsyncSession):
    """Process products data and insert into database (TENANT-ISOLATED)"""
    try:
        validated = 0
        rejected = 0
        errors = []
        
        for product_data in products_data:
            try:
                # Create product with tenant_id
                product = Product(
                    id=uuid4(),
                    tenant_id=tenant_id,  # Use authenticated user's tenant
                    sku=product_data.get('sku'),
                    normalized_sku=product_data.get('sku', '').upper(),
                    name=product_data.get('name'),
                    category=product_data.get('category'),
                    price=float(product_data.get('price', 0)),
                    currency=product_data.get('currency', 'USD'),
                    marketplace=product_data.get('marketplace', 'unknown'),
                    inventory_level=int(product_data.get('inventory_level', 0))
                )
                
                db.add(product)
                validated += 1
                
            except Exception as e:
                rejected += 1
                errors.append(f"Row error: {str(e)}")
                logger.error(f"Failed to process product: {str(e)}")
        
        # Commit all products
        await db.commit()
        
        # Update job status
        ingestion_jobs[job_id].update({
            'status': 'completed',
            'records_validated': validated,
            'records_rejected': rejected,
            'errors': errors,
            'completed_at': datetime.utcnow()
        })
        
        logger.info(f"Job {job_id} completed: {validated} validated, {rejected} rejected")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        ingestion_jobs[job_id].update({
            'status': 'failed',
            'errors': [str(e)],
            'completed_at': datetime.utcnow()
        })


async def _process_reviews_data(job_id: str, reviews_data: List[Dict[str, Any]], tenant_id: UUID, db: AsyncSession):
    """Process reviews data and insert into database (TENANT-ISOLATED)"""
    try:
        from sqlalchemy import select
        
        validated = 0
        rejected = 0
        errors = []
        
        for review_data in reviews_data:
            try:
                # Find product by SKU (TENANT-FILTERED)
                product_sku = review_data.get('product_sku')
                result = await db.execute(
                    select(Product).where(
                        Product.sku == product_sku,
                        Product.tenant_id == tenant_id  # TENANT ISOLATION
                    )
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    rejected += 1
                    errors.append(f"Product not found for SKU: {product_sku}")
                    continue
                
                # Create review with tenant_id
                review = Review(
                    id=uuid4(),
                    tenant_id=tenant_id,  # Use authenticated user's tenant
                    product_id=product.id,
                    rating=int(review_data.get('rating', 0)),
                    text=review_data.get('review_text', ''),
                    source='csv_upload',
                    is_spam=False
                )
                
                db.add(review)
                validated += 1
                
            except Exception as e:
                rejected += 1
                errors.append(f"Row error: {str(e)}")
                logger.error(f"Failed to process review: {str(e)}")
        
        # Commit all reviews
        await db.commit()
        
        # Update job status
        ingestion_jobs[job_id].update({
            'status': 'completed',
            'records_validated': validated,
            'records_rejected': rejected,
            'errors': errors,
            'completed_at': datetime.utcnow()
        })
        
        logger.info(f"Job {job_id} completed: {validated} validated, {rejected} rejected")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        ingestion_jobs[job_id].update({
            'status': 'failed',
            'errors': [str(e)],
            'completed_at': datetime.utcnow()
        })



@router.get("/scheduled/jobs")
async def list_scheduled_jobs():
    """List all scheduled ingestion jobs"""
    try:
        service = get_scheduled_service()
        jobs = service.get_jobs()
        
        return {
            "total": len(jobs),
            "jobs": jobs,
            "scheduler_running": service.is_running
        }
    except Exception as e:
        logger.error(f"Failed to list scheduled jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post("/scheduled/trigger/{job_id}")
async def trigger_scheduled_job(job_id: str):
    """Manually trigger a scheduled job"""
    try:
        service = get_scheduled_service()
        
        # Get the job
        job = service.scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Trigger the job immediately
        job.modify(next_run_time=datetime.utcnow())
        
        return {
            "message": f"Job {job_id} triggered successfully",
            "job_id": job_id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")
