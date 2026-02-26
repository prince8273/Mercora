"""API endpoints for Amazon product data ingestion"""
import logging
import io
import csv
import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal

from src.database import get_db
from src.models.product import Product
from src.models.review import Review
from uuid import uuid4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/amazon", tags=["amazon-data"])


class AmazonDataResponse(BaseModel):
    """Response for Amazon data ingestion"""
    job_id: str
    status: str
    message: str
    products_processed: int = 0
    reviews_processed: int = 0


def parse_prices(prices_str: str) -> tuple:
    """Parse prices JSON string and extract latest price"""
    try:
        if not prices_str:
            return None, None
        
        prices = json.loads(prices_str)
        if not prices:
            return None, None
        
        # Get most recent price
        latest = max(prices, key=lambda x: x.get('dateAdded', ''))
        return latest.get('amountMax'), latest.get('currency', 'USD')
    except:
        return None, None


async def process_amazon_data(
    job_id: str,
    rows: List[Dict[str, Any]],
    tenant_id: str,
    db: AsyncSession
):
    """Process Amazon product data with nested reviews"""
    try:
        products_created = 0
        products_updated = 0
        reviews_created = 0
        errors = []
        
        for idx, row in enumerate(rows):
            try:
                # Parse prices
                price, currency = parse_prices(row.get('prices', ''))
                
                # Extract product data
                sku = row.get('asins', f'ASIN-{idx}')
                name = row.get('name', 'Unknown Product')
                categories = row.get('categories', '')
                category = categories.split(',')[0] if categories else 'General'
                
                # Check if product already exists
                from sqlalchemy import select
                result = await db.execute(
                    select(Product).where(
                        Product.tenant_id == tenant_id,
                        Product.sku == sku,
                        Product.marketplace == 'Amazon'
                    )
                )
                existing_product = result.scalar_one_or_none()
                
                if existing_product:
                    # Update existing product
                    existing_product.name = name
                    existing_product.category = category
                    existing_product.price = Decimal(str(price)) if price else Decimal('99.99')
                    existing_product.currency = currency if currency else 'USD'
                    existing_product.extra_metadata = {
                        'brand': row.get('brand'),
                        'manufacturer': row.get('manufacturer'),
                        'weight': row.get('weight'),
                        'dimension': row.get('dimension'),
                        'ean': row.get('ean'),
                        'upc': row.get('upc'),
                    }
                    product = existing_product
                    products_updated += 1
                else:
                    # Create new product
                    product = Product(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        sku=sku,
                        normalized_sku=sku.lower(),
                        name=name,
                        category=category,
                        price=Decimal(str(price)) if price else Decimal('99.99'),
                        currency=currency if currency else 'USD',
                        marketplace='Amazon',
                        inventory_level=100,  # Default
                        extra_metadata={
                            'brand': row.get('brand'),
                            'manufacturer': row.get('manufacturer'),
                            'weight': row.get('weight'),
                            'dimension': row.get('dimension'),
                            'ean': row.get('ean'),
                            'upc': row.get('upc'),
                        }
                    )
                    db.add(product)
                    await db.flush()
                    products_created += 1
                
                # Extract and create review if present
                review_text = row.get('reviews.text')
                review_rating = row.get('reviews.rating')
                
                if review_text and review_rating:
                    try:
                        review_date_str = row.get('reviews.date')
                        if review_date_str:
                            # Parse ISO format date
                            review_date = datetime.fromisoformat(review_date_str.replace('Z', '+00:00'))
                        else:
                            review_date = datetime.utcnow()
                        
                        # Determine sentiment from rating
                        rating_val = int(float(review_rating))
                        if rating_val >= 4:
                            sentiment = 'positive'
                        elif rating_val >= 3:
                            sentiment = 'neutral'
                        else:
                            sentiment = 'negative'
                        
                        review = Review(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            product_id=product.id,
                            rating=rating_val,
                            text=str(review_text)[:1000],  # Limit length
                            sentiment=sentiment,
                            sentiment_confidence=0.85,
                            is_spam=False,
                            created_at=review_date,
                            source='Amazon'
                        )
                        
                        db.add(review)
                        reviews_created += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to create review for {sku}: {e}")
                
                # Flush after each product to catch errors early
                await db.flush()
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                logger.error(f"Failed to process row {idx}: {e}")
                # Rollback this transaction and continue
                await db.rollback()
                # Start a new transaction
                continue
        
        # Commit all changes
        await db.commit()
        
        logger.info(f"Amazon data job {job_id} completed: {products_created} created, {products_updated} updated, {reviews_created} reviews")
        
        return {
            'status': 'completed',
            'products_created': products_created,
            'products_updated': products_updated,
            'reviews_created': reviews_created,
            'errors': errors
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Amazon data job {job_id} failed: {e}")
        raise


@router.post("/upload", response_model=AmazonDataResponse)
async def upload_amazon_data(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload Amazon product data CSV with nested reviews.
    
    Expected columns:
    - id, asins, brand, categories, name, prices (JSON)
    - reviews.date, reviews.rating, reviews.text, reviews.title
    - reviews.username, reviews.numHelpful, etc.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    job_id = str(uuid4())
    
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        rows = list(csv_reader)
        logger.info(f"Received Amazon CSV with {len(rows)} rows")
        
        # Get tenant ID (use first tenant for now)
        from src.models.tenant import Tenant
        from sqlalchemy import select
        
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant found. Please run init_database.py first")
        
        tenant_id = str(tenant.id)
        
        # Process data
        result = await process_amazon_data(job_id, rows, tenant_id, db)
        
        return AmazonDataResponse(
            job_id=job_id,
            status=result['status'],
            message=f"Processed {result['products_created']} new products, {result.get('products_updated', 0)} updated, {result['reviews_created']} reviews",
            products_processed=result['products_created'] + result.get('products_updated', 0),
            reviews_processed=result['reviews_created']
        )
        
    except Exception as e:
        logger.error(f"Failed to process Amazon CSV upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.post("/upload/transformed")
async def upload_transformed_data(
    products_file: UploadFile = File(None),
    reviews_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload pre-transformed products and reviews files.
    Use this after running transform_amazon_data.py
    """
    results = {
        'products': None,
        'reviews': None
    }
    
    # Upload products if provided
    if products_file:
        from src.api.ingestion import upload_products_csv
        try:
            result = await upload_products_csv(products_file, None, db)
            results['products'] = result
        except Exception as e:
            logger.error(f"Failed to upload products: {e}")
            results['products'] = {'error': str(e)}
    
    # Upload reviews if provided
    if reviews_file:
        from src.api.ingestion import upload_reviews_csv
        try:
            result = await upload_reviews_csv(reviews_file, None, db)
            results['reviews'] = result
        except Exception as e:
            logger.error(f"Failed to upload reviews: {e}")
            results['reviews'] = {'error': str(e)}
    
    return results


@router.get("/stats")
async def get_amazon_data_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about Amazon data in the system"""
    from sqlalchemy import select, func
    
    try:
        # Count products from Amazon
        result = await db.execute(
            select(func.count(Product.id)).where(Product.marketplace == 'Amazon')
        )
        amazon_products = result.scalar() or 0
        
        # Count reviews
        result = await db.execute(
            select(func.count(Review.id)).where(Review.source == 'Amazon')
        )
        amazon_reviews = result.scalar() or 0
        
        # Get average rating
        result = await db.execute(
            select(func.avg(Review.rating)).where(Review.source == 'Amazon')
        )
        avg_rating = result.scalar() or 0
        
        return {
            'amazon_products': amazon_products,
            'amazon_reviews': amazon_reviews,
            'average_rating': round(float(avg_rating), 2) if avg_rating else 0,
            'reviews_per_product': round(amazon_reviews / amazon_products, 2) if amazon_products > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get Amazon stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
