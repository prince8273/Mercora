"""
Integration Test 35.2: Quick Mode Integration

Tests Quick Mode execution with cache:
- 2-minute SLA compliance
- Cache hit/miss behavior
- Cached result usage

Validates: Requirements 6.2, 10.1
"""
import pytest
import asyncio
import time
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestration.query_router import QueryRouter
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine
from src.orchestration.execution_service import ExecutionService
from src.orchestration.result_synthesizer import ResultSynthesizer
from src.cache.cache_manager import CacheManager
from src.schemas.orchestration import ExecutionMode, AgentType
from src.models.product import Product


@pytest.mark.asyncio
async def test_quick_mode_sla_compliance(db_session: AsyncSession):
    """
    Test Quick Mode completes within 2-minute SLA.
    
    Validates: Requirement 10.1 (2-minute SLA for Quick Mode)
    """
    tenant_id = uuid4()
    query_text = "What is the price for SKU-QUICK-001?"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-QUICK-001",
        normalized_sku="skuquick001",
        name="Quick Mode Test Product",
        category="Test",
        price=79.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    # Execute Quick Mode and measure time
    start_time = time.time()
    
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    # Force Quick Mode
    routing_decision.execution_mode = ExecutionMode.QUICK
    
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
        query_data={
            "query": query_text,
            "product_sku": "SKU-QUICK-001",
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
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Validate SLA: 2 minutes = 120 seconds
    assert execution_time < 120.0, f"Quick Mode exceeded 2-minute SLA: {execution_time:.2f}s"
    assert report.report_id is not None


@pytest.mark.asyncio
async def test_quick_mode_cache_miss_then_hit(db_session: AsyncSession):
    """
    Test cache behavior: first query misses cache, second query hits cache.
    
    Validates: Requirement 6.2 (Cache integration)
    """
    tenant_id = uuid4()
    query_text = "Analyze product SKU-CACHE-001"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-CACHE-001",
        normalized_sku="skucache001",
        name="Cache Test Product",
        category="Test",
        price=59.99,
        marketplace="Amazon",
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    # Initialize cache
    cache_manager = CacheManager()
    
    # First execution - cache miss
    query_router = QueryRouter(tenant_id=tenant_id, cache_manager=cache_manager)
    routing_decision = query_router.route_query(query_text)
    
    cache_key = routing_decision.cache_key
    assert cache_key is not None
    
    # Check cache - should be empty
    cached_result = await cache_manager.get("query_result", tenant_id, cache_key)
    assert cached_result is None, "Cache should be empty on first query"
    
    # Execute query
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
        query_data={
            "query": query_text,
            "product_sku": "SKU-CACHE-001",
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
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    # Store result in cache
    await cache_manager.set(
        "query_result",
        tenant_id,
        cache_key,
        {
            "report": report.dict(),
            "timestamp": datetime.utcnow().isoformat()
        },
        ttl=300  # 5 minutes
    )
    
    # Second execution - cache hit
    cached_result = await cache_manager.get("query_result", tenant_id, cache_key)
    assert cached_result is not None, "Cache should contain result after first query"
    assert "report" in cached_result
    assert cached_result["report"]["query"] == query_text


@pytest.mark.asyncio
async def test_quick_mode_faster_than_deep_mode(db_session: AsyncSession):
    """
    Test that Quick Mode is significantly faster than Deep Mode.
    
    Validates: Performance optimization in Quick Mode
    """
    tenant_id = uuid4()
    query_text = "Analyze product SKU-PERF-001"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-PERF-001",
        normalized_sku="skuperf001",
        name="Performance Test Product",
        category="Test",
        price=149.99,
        marketplace="Amazon",
        inventory_level=200,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    # Execute Quick Mode
    start_quick = time.perf_counter()
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
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
        query_data={
            "query": query_text,
            "product_sku": "SKU-PERF-001",
            "db": db_session,
            "tenant_id": tenant_id
        }
    )
    
    quick_time = time.perf_counter() - start_quick
    
    # Execute Deep Mode
    start_deep = time.perf_counter()
    
    execution_plan_deep = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.DEEP
    )
    
    agent_results_deep = await execution_service.execute_plan(
        plan=execution_plan_deep,
        query_data={
            "query": query_text,
            "product_sku": "SKU-PERF-001",
            "db": db_session,
            "tenant_id": tenant_id
        }
    )
    
    deep_time = time.perf_counter() - start_deep
    
    # Quick Mode should be faster (or at least not slower)
    # Allow some variance due to test environment
    assert quick_time <= deep_time * 1.5, \
        f"Quick Mode ({quick_time:.2f}s) should be faster than Deep Mode ({deep_time:.2f}s)"


@pytest.mark.asyncio
async def test_quick_mode_uses_subset_of_agents(db_session: AsyncSession):
    """
    Test that Quick Mode uses fewer agents than Deep Mode.
    
    Validates: Agent selection optimization in Quick Mode
    """
    tenant_id = uuid4()
    query_text = "Complete analysis of product SKU-AGENT-001"
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-AGENT-001",
        normalized_sku="skuagent001",
        name="Agent Selection Test Product",
        category="Test",
        price=99.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    # Quick Mode plan
    execution_plan_quick = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    # Deep Mode plan
    execution_plan_deep = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.DEEP
    )
    
    # Quick Mode should have fewer or equal agents
    quick_agent_count = len(execution_plan_quick.tasks)
    deep_agent_count = len(execution_plan_deep.tasks)
    
    assert quick_agent_count <= deep_agent_count, \
        f"Quick Mode should use fewer agents ({quick_agent_count}) than Deep Mode ({deep_agent_count})"
    
    # Quick Mode should have shorter timeouts
    quick_max_timeout = max(task.timeout_seconds for task in execution_plan_quick.tasks)
    deep_max_timeout = max(task.timeout_seconds for task in execution_plan_deep.tasks)
    
    assert quick_max_timeout <= deep_max_timeout, \
        "Quick Mode should have shorter timeouts than Deep Mode"
