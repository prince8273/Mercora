"""CSV Upload and Analysis API"""
import csv
import io
from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine
from src.orchestration.query_router import QueryRouter
from src.orchestration.execution_service import ExecutionService
from src.orchestration.result_synthesizer import ResultSynthesizer
from src.models.product import Product
from src.models.review import Review
from src.models.sales_record import SalesRecord
from src.models.user import User
from src.schemas.orchestration import ExecutionMode
from src.auth.dependencies import get_current_active_user, get_tenant_id
from src.cache.event_bus import get_event_publisher, EventType, DataEvent

router = APIRouter(prefix="/csv", tags=["CSV Upload"])


@router.post("/upload/products")
async def upload_products_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload products CSV and get AI-powered analysis (TENANT-ISOLATED).
    
    Expected CSV columns: sku, name, category, price, marketplace, inventory_level
    
    Returns:
        Analysis results from LLM reasoning engine
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV file
    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    # Parse and store products
    products = []
    for row in csv_reader:
        product = Product(
            id=uuid4(),
            tenant_id=tenant_id,
            sku=row.get('sku', ''),
            normalized_sku=row.get('sku', '').upper(),
            name=row.get('name', ''),
            category=row.get('category', 'General'),
            price=float(row.get('price', 0)),
            currency=row.get('currency', 'USD'),
            marketplace=row.get('marketplace', 'unknown'),
            inventory_level=int(row.get('inventory_level', 0)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        products.append(product)
        db.add(product)
    
    await db.commit()
    
    # Publish cache invalidation events for each product
    event_publisher = get_event_publisher()
    for product in products:
        event = DataEvent(
            event_type=EventType.PRODUCT_CREATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=str(product.id),
            metadata={'sku': product.sku, 'name': product.name}
        )
        await event_publisher.publish(event)
    
    # Analyze with LLM
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    
    # Create analysis query
    query = f"""Analyze the uploaded product data:
- Total products: {len(products)}
- Categories: {', '.join(set(p.category for p in products))}
- Price range: ${min(p.price for p in products):.2f} - ${max(p.price for p in products):.2f}
- Marketplaces: {', '.join(set(p.marketplace for p in products))}

Provide insights on:
1. Pricing strategy recommendations
2. Inventory optimization suggestions
3. Product portfolio analysis
"""
    
    # Get LLM understanding - FIXED: unpack tuple
    intent, parameters = llm_engine.understand_query(query)
    
    # Select agents - FIXED: pass both arguments
    agents = llm_engine.select_agents(intent, parameters)
    
    # Create execution plan - FIXED: use generate_execution_plan
    query_id = str(uuid4())
    plan = llm_engine.generate_execution_plan(
        query_id=query_id,
        query=query,
        intent=intent,
        parameters=parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    # Execute plan
    execution_service = ExecutionService(tenant_id=tenant_id)
    
    # Prepare query data for agents
    query_data = {
        'db': db,
        'tenant_id': tenant_id,
        'product_ids': [p.id for p in products]
    }
    
    agent_results_list = await execution_service.execute_plan(plan, query_data)
    
    # Convert list of AgentResult to dict format expected by synthesizer
    agent_results = {
        result.agent_type: result.data if result.success else {}
        for result in agent_results_list
    }
    
    # Synthesize results
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    execution_metadata = {
        'execution_mode': ExecutionMode.QUICK.value,
        'agents_used': [a.value for a in agents],
        'product_count': len(products)
    }
    final_report = synthesizer.synthesize_results(
        query_id=query_id,
        query=query,
        agent_results=agent_results,
        execution_metadata=execution_metadata
    )
    
    return {
        'status': 'success',
        'products_uploaded': len(products),
        'analysis': {
            'intent': intent.value,  # FIXED: use .value
            'confidence': parameters.get('confidence', 0.0),  # FIXED: extract from parameters
            'agents_used': [a.value for a in agents],
            'report': final_report.model_dump() if hasattr(final_report, 'model_dump') else final_report.dict()
        },
        'token_usage': llm_engine.get_token_usage()  # FIXED: correct method name
    }


@router.post("/upload/reviews")
async def upload_reviews_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload reviews CSV and get sentiment analysis (TENANT-ISOLATED).
    
    Expected CSV columns: product_id, rating, text, source
    
    Returns:
        Sentiment analysis from LLM reasoning engine
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV file
    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    # Parse and store reviews
    reviews = []
    for row in csv_reader:
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=UUID(row.get('product_id')),
            rating=int(row.get('rating', 3)),
            text=row.get('text', ''),
            source=row.get('source', 'csv_upload'),
            is_spam=False,
            created_at=datetime.utcnow()
        )
        reviews.append(review)
        db.add(review)
    
    await db.commit()
    
    # Publish cache invalidation events for each review
    event_publisher = get_event_publisher()
    for review in reviews:
        event = DataEvent(
            event_type=EventType.REVIEW_CREATED,
            tenant_id=tenant_id,
            entity_type='review',
            entity_id=str(review.id),
            metadata={'product_id': str(review.product_id), 'rating': review.rating}
        )
        await event_publisher.publish(event)
    
    # Analyze with LLM
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    
    # Create analysis query
    avg_rating = sum(r.rating for r in reviews) / len(reviews)
    query = f"""Analyze the uploaded review data:
- Total reviews: {len(reviews)}
- Average rating: {avg_rating:.2f}/5
- Rating distribution: {_get_rating_distribution(reviews)}

Provide insights on:
1. Overall customer sentiment
2. Key themes and topics
3. Areas for improvement
4. Feature requests
"""
    
    # Get LLM understanding - FIXED: unpack tuple
    intent, parameters = llm_engine.understand_query(query)
    
    # Select agents - FIXED: pass both arguments
    agents = llm_engine.select_agents(intent, parameters)
    
    # Create execution plan - FIXED: use generate_execution_plan
    query_id = str(uuid4())
    plan = llm_engine.generate_execution_plan(
        query_id=query_id,
        query=query,
        intent=intent,
        parameters=parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    # Execute plan
    execution_service = ExecutionService(tenant_id=tenant_id)
    
    # Get unique product IDs
    product_ids = list(set(r.product_id for r in reviews))
    
    query_data = {
        'db': db,
        'tenant_id': tenant_id,
        'product_ids': product_ids
    }
    
    agent_results_list = await execution_service.execute_plan(plan, query_data)
    
    # Convert list of AgentResult to dict format expected by synthesizer
    agent_results = {
        result.agent_type: result.data if result.success else {}
        for result in agent_results_list
    }
    
    # Synthesize results
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    execution_metadata = {
        'execution_mode': ExecutionMode.QUICK.value,
        'agents_used': [a.value for a in agents],
        'product_count': len(product_ids)
    }
    final_report = synthesizer.synthesize_results(
        query_id=query_id,
        query=query,
        agent_results=agent_results,
        execution_metadata=execution_metadata
    )
    
    return {
        'status': 'success',
        'reviews_uploaded': len(reviews),
        'analysis': {
            'intent': intent.value,  # FIXED: use .value
            'confidence': parameters.get('confidence', 0.0),  # FIXED: extract from parameters
            'agents_used': [a.value for a in agents],
            'average_rating': avg_rating,
            'report': final_report.model_dump() if hasattr(final_report, 'model_dump') else final_report.dict()
        },
        'token_usage': llm_engine.get_token_usage()  # FIXED: correct method name
    }


@router.post("/upload/sales")
async def upload_sales_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload sales CSV and get demand forecast analysis (TENANT-ISOLATED).
    
    Expected CSV columns: product_id, quantity, revenue, date, marketplace
    
    Returns:
        Demand forecast analysis from LLM reasoning engine
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV file
    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    # Parse and store sales records
    sales_records = []
    for row in csv_reader:
        record = SalesRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=UUID(row.get('product_id')),
            quantity=int(row.get('quantity', 0)),
            revenue=float(row.get('revenue', 0)),
            date=datetime.fromisoformat(row.get('date')).date(),
            marketplace=row.get('marketplace', 'unknown')
        )
        sales_records.append(record)
        db.add(record)
    
    await db.commit()
    
    # Publish cache invalidation events for each sales record
    event_publisher = get_event_publisher()
    for record in sales_records:
        event = DataEvent(
            event_type=EventType.SALES_RECORDED,
            tenant_id=tenant_id,
            entity_type='sales',
            entity_id=str(record.id),
            metadata={'product_id': str(record.product_id), 'quantity': record.quantity}
        )
        await event_publisher.publish(event)
    
    # Analyze with LLM
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    
    # Create analysis query
    total_revenue = sum(r.revenue for r in sales_records)
    total_quantity = sum(r.quantity for r in sales_records)
    query = f"""Analyze the uploaded sales data:
- Total sales records: {len(sales_records)}
- Total revenue: ${total_revenue:,.2f}
- Total units sold: {total_quantity:,}
- Average order value: ${total_revenue/len(sales_records):.2f}

Provide insights on:
1. Sales trends and patterns
2. Demand forecasting for next 30 days
3. Inventory recommendations
4. Revenue optimization opportunities
"""
    
    # Get LLM understanding - FIXED: unpack tuple
    intent, parameters = llm_engine.understand_query(query)
    
    # Select agents - FIXED: pass both arguments
    agents = llm_engine.select_agents(intent, parameters)
    
    # Create execution plan - FIXED: use generate_execution_plan
    query_id = str(uuid4())
    plan = llm_engine.generate_execution_plan(
        query_id=query_id,
        query=query,
        intent=intent,
        parameters=parameters,
        execution_mode=ExecutionMode.DEEP  # Use deep mode for forecasting
    )
    
    # Execute plan
    execution_service = ExecutionService(tenant_id=tenant_id)
    
    # Get unique product IDs
    product_ids = list(set(r.product_id for r in sales_records))
    
    query_data = {
        'db': db,
        'tenant_id': tenant_id,
        'product_ids': product_ids
    }
    
    agent_results_list = await execution_service.execute_plan(plan, query_data)
    
    # Convert list of AgentResult to dict format expected by synthesizer
    agent_results = {
        result.agent_type: result.data if result.success else {}
        for result in agent_results_list
    }
    
    # Synthesize results
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    execution_metadata = {
        'execution_mode': ExecutionMode.DEEP.value,
        'agents_used': [a.value for a in agents],
        'product_count': len(product_ids)
    }
    final_report = synthesizer.synthesize_results(
        query_id=query_id,
        query=query,
        agent_results=agent_results,
        execution_metadata=execution_metadata
    )
    
    return {
        'status': 'success',
        'sales_records_uploaded': len(sales_records),
        'analysis': {
            'intent': intent.value,  # FIXED: use .value
            'confidence': parameters.get('confidence', 0.0),  # FIXED: extract from parameters
            'agents_used': [a.value for a in agents],
            'total_revenue': total_revenue,
            'total_quantity': total_quantity,
            'report': final_report.model_dump() if hasattr(final_report, 'model_dump') else final_report.dict()
        },
        'token_usage': llm_engine.get_token_usage()  # FIXED: correct method name
    }


@router.post("/analyze")
async def analyze_csv_with_custom_query(
    file: UploadFile = File(...),
    query: str = "Analyze this data and provide insights",
    data_type: str = "products",  # products, reviews, or sales
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload any CSV and analyze with custom query through LLM (TENANT-ISOLATED).
    
    Args:
        file: CSV file
        query: Custom analysis query
        data_type: Type of data (products, reviews, sales)
        
    Returns:
        LLM-powered analysis results
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV file
    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    # Parse CSV into list of dicts
    rows = list(csv_reader)
    
    # Analyze with LLM
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    
    # Enhance query with CSV context
    enhanced_query = f"""{query}

CSV Data Summary:
- Rows: {len(rows)}
- Columns: {', '.join(rows[0].keys()) if rows else 'None'}
- Data type: {data_type}

Sample data (first 3 rows):
{_format_sample_data(rows[:3])}
"""
    
    # Get LLM understanding - FIXED: unpack tuple
    intent, parameters = llm_engine.understand_query(enhanced_query)
    
    # Select agents - FIXED: pass both arguments
    agents = llm_engine.select_agents(intent, parameters)
    
    # Create execution plan - FIXED: use generate_execution_plan
    plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=enhanced_query,
        intent=intent,
        parameters=parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    return {
        'status': 'success',
        'rows_analyzed': len(rows),
        'columns': list(rows[0].keys()) if rows else [],
        'analysis': {
            'intent': intent.value,  # FIXED: use .value
            'confidence': parameters.get('confidence', 0.0),  # FIXED: extract from parameters
            'suggested_agents': [a.value for a in agents],
            'reasoning': parameters.get('reasoning', ''),  # FIXED: extract from parameters
            'execution_plan': {
                'mode': plan.execution_mode.value,
                'tasks': [
                    {
                        'agent': task.agent_type.value,
                        'timeout': task.timeout_seconds
                    }
                    for task in plan.tasks
                ],
                'estimated_duration': str(plan.estimated_duration)
            }
        },
        'token_usage': llm_engine.get_token_usage()  # FIXED: correct method name
    }


def _get_rating_distribution(reviews: List[Review]) -> Dict[int, int]:
    """Get rating distribution"""
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        distribution[review.rating] = distribution.get(review.rating, 0) + 1
    return distribution


def _format_sample_data(rows: List[Dict[str, Any]]) -> str:
    """Format sample data for LLM"""
    if not rows:
        return "No data"
    
    formatted = []
    for i, row in enumerate(rows, 1):
        formatted.append(f"Row {i}: {row}")
    
    return '\n'.join(formatted)
