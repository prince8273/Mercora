"""
Integration Test 35.3: Deep Mode Integration

Tests Deep Mode with multi-agent coordination:
- 10-minute SLA compliance
- Comprehensive analysis
- Multi-agent coordination

Validates: Requirements 6.3, 10.2
"""
import pytest
import asyncio
import time
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestration.query_router import QueryRouter
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine
from src.orchestration.execution_service import ExecutionService
from src.orchestration.result_synthesizer import ResultSynthesizer
from src.schemas.orchestration import ExecutionMode, AgentType
from src.models.product import Product
from src.models.review import Review


@pytest.mark.asyncio
async def test_deep_mode_sla_compliance(db_session: AsyncSession):
    """
    Test Deep Mode completes within 10-minute SLA.
    
    Validates: Requirement 10.2 (10-minute SLA for Deep Mode)
    """
    tenant_id = uuid4()
    query_text = "Comprehensive analysis of product SKU-DEEP-001 including pricing, sentiment, and forecast"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-DEEP-001",
        normalized_sku="skudeep001",
        name="Deep Mode Test Product",
        category="Electronics",
        price=299.99,
        marketplace="Amazon",
        inventory_level=150,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    
    # Add reviews for sentiment analysis
    for i in range(10):
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            rating=3 + (i % 3),
            text=f"Detailed review {i}. Product quality is good.",
            sentiment_confidence=0.6 + (i * 0.03),
            sentiment="positive",
            source="test",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
    
    await db_session.commit()
    
    # Execute Deep Mode and measure time
    start_time = time.time()
    
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    # Force Deep Mode
    routing_decision.execution_mode = ExecutionMode.DEEP
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    # Use multiple agents for comprehensive analysis
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
        query_data={
            "query": query_text,
            "product_sku": "SKU-DEEP-001",
            "db": db_session,
            "tenant_id": tenant_id
        }
    )
    
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
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Validate SLA: 10 minutes = 600 seconds
    assert execution_time < 600.0, f"Deep Mode exceeded 10-minute SLA: {execution_time:.2f}s"
    assert report.report_id is not None


@pytest.mark.asyncio
async def test_deep_mode_multi_agent_coordination(db_session: AsyncSession):
    """
    Test Deep Mode coordinates multiple agents correctly.
    
    Validates: Multi-agent coordination and result synthesis
    """
    tenant_id = uuid4()
    query_text = "Full analysis of SKU-COORD-001"
    
    # Setup comprehensive test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-COORD-001",
        normalized_sku="skucoord001",
        name="Coordination Test Product",
        category="Home",
        price=179.99,
        marketplace="Amazon",
        inventory_level=120,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    
    # Add diverse reviews
    sentiments = ["positive", "negative", "neutral"]
    for i in range(15):
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            rating=2 + (i % 4),
            text=f"Review {i}. {sentiments[i % 3]} feedback.",
            sentiment_confidence=0.3 + (i * 0.04),
            sentiment=sentiments[i % 3],
            source="test",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
    
    await db_session.commit()
    
    # Execute with multiple agents
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
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
        query_data={"query": query_text, "product_sku": "SKU-COORD-001", "db": db_session, "tenant_id": tenant_id}
    )
    
    # Verify multiple agents executed
    agent_types = [r.agent_type for r in agent_results]
    assert len(agent_types) >= 2, "Deep Mode should execute multiple agents"
    
    # Verify results from different agents
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
    assert len(report.insights) >= 2, "Deep Mode should have multiple findings"
    assert len(report.action_items) >= 1, "Deep Mode should have action items"
    assert report.overall_confidence >= 0.0 and report.overall_confidence <= 100.0


@pytest.mark.asyncio
async def test_deep_mode_comprehensive_analysis(db_session: AsyncSession):
    """
    Test Deep Mode provides more comprehensive analysis than Quick Mode.
    
    Validates: Comprehensive analysis requirement
    """
    tenant_id = uuid4()
    query_text = "Analyze product SKU-COMP-001"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-COMP-001",
        normalized_sku="skucomp001",
        name="Comprehensive Analysis Product",
        category="Electronics",
        price=249.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    
    # Add reviews
    for i in range(20):
        review = Review(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product.id,
            rating=2 + (i % 4),
            text=f"Comprehensive review {i}.",
            sentiment_confidence=0.4 + (i * 0.02),
            sentiment="neutral",
            source="test",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        db_session.add(review)
    
    await db_session.commit()
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    # Execute Quick Mode
    execution_plan_quick = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    agent_results_quick = await execution_service.execute_plan(
        plan=execution_plan_quick,
        query_data={"query": query_text, "product_sku": "SKU-COMP-001", "db": db_session, "tenant_id": tenant_id}
    )
    
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    agent_results_dict_quick = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results_quick
    }
    
    report_quick = synthesizer.synthesize_results(
        query_id=str(uuid4()),
        query=query_text,
        agent_results=agent_results_dict_quick,
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    # Execute Deep Mode
    execution_plan_deep = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.DEEP
    )
    
    agent_results_deep = await execution_service.execute_plan(
        plan=execution_plan_deep,
        query_data={"query": query_text, "product_sku": "SKU-COMP-001", "db": db_session, "tenant_id": tenant_id}
    )
    
    agent_results_dict_deep = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results_deep
    }
    
    report_deep = synthesizer.synthesize_results(
        query_id=str(uuid4()),
        query=query_text,
        agent_results=agent_results_dict_deep,
        execution_metadata={"mode": ExecutionMode.DEEP.value}
    )
    
    # Deep Mode should have more comprehensive results
    assert len(report_deep.insights) >= len(report_quick.insights), \
        "Deep Mode should have more findings than Quick Mode"
    
    assert len(report_deep.action_items) >= len(report_quick.action_items), \
        "Deep Mode should have more action items than Quick Mode"


@pytest.mark.asyncio
async def test_deep_mode_parallel_agent_execution(db_session: AsyncSession):
    """
    Test Deep Mode executes independent agents in parallel.
    
    Validates: Parallel execution optimization
    """
    tenant_id = uuid4()
    query_text = "Parallel analysis of SKU-PARALLEL-001"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-PARALLEL-001",
        normalized_sku="skuparallel001",
        name="Parallel Execution Product",
        category="Test",
        price=199.99,
        marketplace="Amazon",
        inventory_level=80,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    execution_plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.DEEP
    )
    
    # Check that agents are in parallel groups
    assert len(execution_plan.parallel_groups) > 0, "Execution plan should have parallel groups"
    
    # Execute and measure time
    start_time = time.time()
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    agent_results = await execution_service.execute_plan(
        plan=execution_plan,
        query_data={"query": query_text, "product_sku": "SKU-PARALLEL-001", "db": db_session, "tenant_id": tenant_id}
    )
    
    parallel_time = time.time() - start_time
    
    # Calculate expected sequential time
    sequential_time = sum(r.execution_time for r in agent_results)
    
    # Parallel execution should be faster than sequential
    # Allow some overhead for coordination
    assert parallel_time < sequential_time * 0.8, \
        f"Parallel execution ({parallel_time:.2f}s) should be faster than sequential ({sequential_time:.2f}s)"
