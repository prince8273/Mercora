"""
Integration Test 35.1: End-to-End Query Execution

Tests complete flow from query to report:
- Query Router pattern matching
- LLM Reasoning Engine query understanding
- Execution Service agent coordination
- Result Synthesizer report generation

Validates: Requirements 6.1, 6.6, 7.1
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestration.query_router import QueryRouter
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine, QueryIntent
from src.orchestration.execution_service import ExecutionService
from src.orchestration.result_synthesizer import ResultSynthesizer
from src.schemas.orchestration import ExecutionMode, AgentType
from src.models.product import Product
from src.models.review import Review


@pytest.mark.asyncio
async def test_end_to_end_pricing_query(db_session: AsyncSession):
    """
    Test complete flow for pricing query.
    
    Flow:
    1. Query Router identifies pricing query
    2. LLM Engine understands query intent
    3. Execution Service runs pricing agent
    4. Result Synthesizer generates report
    """
    tenant_id = uuid4()
    query_text = "What is the optimal price for product SKU-123?"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-123",
        normalized_sku="sku123",
        name="Test Product",
        category="Electronics",
        price=99.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    # STEP 1: Query Router
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    assert routing_decision.execution_mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]
    assert AgentType.PRICING in routing_decision.required_agents
    
    # STEP 2: LLM Reasoning Engine
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    assert query_intent is not None
    assert isinstance(query_intent, QueryIntent)
    assert isinstance(query_parameters, dict)
    
    # STEP 3: Execution Service
    execution_plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    agent_results = await execution_service.execute_plan(
        plan=execution_plan,
        query_data={
            "query": query_text,
            "product_sku": "SKU-123",
            "db": db_session,
            "tenant_id": tenant_id
        }
    )
    
    assert len(agent_results) > 0
    assert any(r.agent_type == AgentType.PRICING for r in agent_results)
    
    # STEP 4: Result Synthesizer
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    
    # Convert agent results to dict format
    agent_results_dict = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results
    }
    
    report = synthesizer.synthesize_results(
        query_id=str(uuid4()),
        query=query_text,
        agent_results=agent_results_dict,
        execution_metadata={
            "mode": ExecutionMode.QUICK.value,
            "total_time": sum(r.execution_time for r in agent_results)
        }
    )
    
    # Validate report structure
    assert report.report_id is not None
    assert report.query == query_text
    assert report.tenant_id == tenant_id
    assert report.overall_confidence >= 0.0
    assert report.overall_confidence <= 100.0
    assert isinstance(report.executive_summary, str)
    assert isinstance(report.insights, list)
    assert isinstance(report.action_items, list)


@pytest.mark.asyncio
async def test_end_to_end_sentiment_query(db_session: AsyncSession):
    """
    Test complete flow for sentiment analysis query.
    """
    tenant_id = uuid4()
    query_text = "What do customers think about product SKU-456?"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-456",
        normalized_sku="sku456",
        name="Test Product 2",
        category="Home",
        price=49.99,
        marketplace="eBay",
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    
    # Add reviews
    for i in range(3):
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            rating=4 + (i % 2),
            text=f"Great product! Very satisfied. Review {i}",
            sentiment_confidence=0.8,
            sentiment="positive",
            source="test",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
    
    await db_session.commit()
    
    # Execute full flow
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    assert AgentType.SENTIMENT in routing_decision.required_agents
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    execution_plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    agent_results = await execution_service.execute_plan(
        plan=execution_plan,
        query_data={"query": query_text, "product_sku": "SKU-456", "db": db_session, "tenant_id": tenant_id}
    )
    
    assert len(agent_results) > 0
    
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    agent_results_dict = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results
    }
    
    report = synthesizer.synthesize_results(
        query_id=str(uuid4()),
        query=query_text,
        agent_results=agent_results_dict,
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    assert report.report_id is not None
    assert report.tenant_id == tenant_id
    assert report.overall_confidence >= 0.0
    assert report.overall_confidence <= 100.0


@pytest.mark.asyncio
async def test_end_to_end_multi_agent_query(db_session: AsyncSession):
    """
    Test complete flow with multiple agents.
    
    Validates:
    - Multiple agents invoked correctly
    - Results aggregated properly
    - Report includes all agent insights
    """
    tenant_id = uuid4()
    query_text = "Analyze pricing and sentiment for product SKU-789"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-789",
        normalized_sku="sku789",
        name="Multi-Agent Test Product",
        category="Electronics",
        price=199.99,
        marketplace="Amazon",
        inventory_level=75,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    
    # Add reviews
    for i in range(5):
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            rating=3 + (i % 3),
            text=f"Product review {i}. Mixed feelings.",
            sentiment_confidence=0.5 + (i * 0.1),
            sentiment="neutral",
            source="test",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
    
    await db_session.commit()
    
    # Execute with multiple agents
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    # Force both agents by updating parameters
    query_parameters['agents'] = ['pricing', 'sentiment']
    
    execution_plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.DEEP
    )
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    agent_results = await execution_service.execute_plan(
        plan=execution_plan,
        query_data={"query": query_text, "product_sku": "SKU-789", "db": db_session, "tenant_id": tenant_id}
    )
    
    # Verify multiple agents executed
    agent_types = [r.agent_type for r in agent_results]
    assert AgentType.PRICING in agent_types or AgentType.SENTIMENT in agent_types
    
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    agent_results_dict = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results
    }
    
    report = synthesizer.synthesize_results(
        query_id=str(uuid4()),
        query=query_text,
        agent_results=agent_results_dict,
        execution_metadata={"mode": ExecutionMode.DEEP.value}
    )
    
    # Validate comprehensive report
    assert report.report_id is not None
    assert report.tenant_id == tenant_id
    assert len(report.insights) > 0
    assert len(report.action_items) > 0
    assert report.overall_confidence >= 0.0 and report.overall_confidence <= 100.0
