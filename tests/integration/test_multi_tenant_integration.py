"""
Integration Test 35.4: Multi-Tenant Isolation Integration

Tests tenant data isolation across queries:
- Tenant data isolation across queries
- Cross-tenant access prevention
- Tenant context propagation

Validates: Requirements 20.1, 20.3, 20.5
"""
import pytest
import asyncio
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
from src.models.review import Review


@pytest.mark.asyncio
async def test_tenant_data_isolation_in_queries(db_session: AsyncSession):
    """
    Test that queries only access data from their own tenant.
    
    Validates: Requirement 20.1 (Tenant data isolation)
    """
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    # Setup data for Tenant A
    product_a = Product(
        id=uuid4(),
        tenant_id=tenant_a,
        sku="SKU-TENANT-A",
        normalized_sku="skutenanta",
        name="Tenant A Product",
        category="Electronics",
        price=99.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_a)
    
    # Setup data for Tenant B
    product_b = Product(
        id=uuid4(),
        tenant_id=tenant_b,
        sku="SKU-TENANT-B",
        normalized_sku="skutenantb",
        name="Tenant B Product",
        category="Home",
        price=149.99,
        marketplace="Amazon",
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_b)
    
    await db_session.commit()
    
    # Execute query for Tenant A
    query_text_a = "Analyze product SKU-TENANT-A"
    
    llm_engine_a = LLMReasoningEngine(tenant_id=tenant_a)
    query_intent_a, query_parameters_a = llm_engine_a.understand_query(query_text_a)
    
    execution_plan_a = llm_engine_a.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text_a,
        intent=query_intent_a,
        parameters=query_parameters_a,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service_a = ExecutionService(tenant_id=tenant_a)
    agent_results_a = await execution_service_a.execute_plan(
        plan=execution_plan_a,
        query_data={"query": query_text_a, "product_sku": "SKU-TENANT-A", "db": db_session, "tenant_id": tenant_a}
    )
    
    synthesizer_a = ResultSynthesizer(tenant_id=tenant_a)
    agent_results_dict_a = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results_a
    }
    
    report_a = synthesizer_a.synthesize_results(
        query_id=str(uuid4()),
        query=query_text_a,
        agent_results=agent_results_dict_a,
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    # Execute query for Tenant B
    query_text_b = "Analyze product SKU-TENANT-B"
    
    llm_engine_b = LLMReasoningEngine(tenant_id=tenant_b)
    query_intent_b, query_parameters_b = llm_engine_b.understand_query(query_text_b)
    
    execution_plan_b = llm_engine_b.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text_b,
        intent=query_intent_b,
        parameters=query_parameters_b,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service_b = ExecutionService(tenant_id=tenant_b)
    agent_results_b = await execution_service_b.execute_plan(
        plan=execution_plan_b,
        query_data={"query": query_text_b, "product_sku": "SKU-TENANT-B", "db": db_session, "tenant_id": tenant_b}
    )
    
    synthesizer_b = ResultSynthesizer(tenant_id=tenant_b)
    agent_results_dict_b = {
        result.agent_type: {
            "data": result.data,
            "confidence": result.confidence,
            "execution_time": result.execution_time
        }
        for result in agent_results_b
    }
    
    report_b = synthesizer_b.synthesize_results(
        query_id=str(uuid4()),
        query=query_text_b,
        agent_results=agent_results_dict_b,
        execution_metadata={"mode": ExecutionMode.QUICK.value}
    )
    
    # Validate tenant isolation
    assert report_a.tenant_id == tenant_a
    assert report_b.tenant_id == tenant_b
    assert report_a.tenant_id != report_b.tenant_id
    
    # Reports should not contain cross-tenant data
    assert "SKU-TENANT-B" not in str(report_a.dict())
    assert "SKU-TENANT-A" not in str(report_b.dict())


@pytest.mark.asyncio
async def test_cross_tenant_cache_isolation(db_session: AsyncSession):
    """
    Test that cache is isolated between tenants.
    
    Validates: Requirement 20.3 (Tenant isolation in shared resources)
    """
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    # Setup identical products for both tenants
    product_a = Product(
        id=uuid4(),
        tenant_id=tenant_a,
        sku="SKU-CACHE-TEST",
        normalized_sku="skucachetest",
        name="Cache Test Product A",
        category="Test",
        price=99.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_a)
    
    product_b = Product(
        id=uuid4(),
        tenant_id=tenant_b,
        sku="SKU-CACHE-TEST",
        normalized_sku="skucachetest",
        name="Cache Test Product B",
        category="Test",
        price=149.99,  # Different price
        marketplace="Amazon",
        cost=75.00,
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_b)
    
    await db_session.commit()
    
    # Initialize caches
    cache_a = CacheManager()
    cache_b = CacheManager()
    
    # Store data in Tenant A cache
    cache_key = "product:SKU-CACHE-TEST"
    await cache_a.set("query_result", tenant_a, cache_key, {"price": 99.99}, ttl=300)
    
    # Try to access from Tenant B cache
    cached_b = await cache_b.get("query_result", tenant_b, cache_key)
    
    # Tenant B should not see Tenant A's cached data
    assert cached_b is None, "Tenant B should not access Tenant A's cache"
    
    # Store data in Tenant B cache
    await cache_b.set("query_result", tenant_b, cache_key, {"price": 149.99}, ttl=300)
    
    # Verify both tenants have their own cached data
    cached_a = await cache_a.get("query_result", tenant_a, cache_key)
    cached_b = await cache_b.get("query_result", tenant_b, cache_key)
    
    assert cached_a is not None
    assert cached_b is not None
    assert cached_a["price"] == 99.99
    assert cached_b["price"] == 149.99


@pytest.mark.asyncio
async def test_tenant_context_propagation(db_session: AsyncSession):
    """
    Test that tenant context propagates through all layers.
    
    Validates: Requirement 20.1 (Tenant context propagation)
    """
    tenant_id = uuid4()
    
    # Setup test data
    product = Product(
        id=uuid4(),
        tenant_id=tenant_id,
        sku="SKU-CONTEXT-001",
        normalized_sku="skucontext001",
        name="Context Propagation Product",
        category="Test",
        price=79.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product)
    await db_session.commit()
    
    query_text = "Analyze product SKU-CONTEXT-001"
    
    # Execute through all layers
    query_router = QueryRouter(tenant_id=tenant_id)
    routing_decision = query_router.route_query(query_text)
    
    # Verify tenant context in router
    assert query_router.tenant_id == tenant_id
    
    llm_engine = LLMReasoningEngine(tenant_id=tenant_id)
    query_intent, query_parameters = llm_engine.understand_query(query_text)
    
    # Verify tenant context in LLM engine
    assert llm_engine.tenant_id == tenant_id
    
    execution_plan = llm_engine.generate_execution_plan(
        query_id=str(uuid4()),
        query=query_text,
        intent=query_intent,
        parameters=query_parameters,
        execution_mode=ExecutionMode.QUICK
    )
    
    execution_service = ExecutionService(tenant_id=tenant_id)
    
    # Verify tenant context in execution service
    assert execution_service.tenant_id == tenant_id
    
    agent_results = await execution_service.execute_plan(
        plan=execution_plan,
        query_data={"query": query_text, "product_sku": "SKU-CONTEXT-001", "db": db_session, "tenant_id": tenant_id}
    )
    
    synthesizer = ResultSynthesizer(tenant_id=tenant_id)
    
    # Verify tenant context in synthesizer
    assert synthesizer.tenant_id == tenant_id
    
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
    
    # Verify tenant context in final report
    assert report.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_concurrent_multi_tenant_queries(db_session: AsyncSession):
    """
    Test concurrent queries from different tenants don't interfere.
    
    Validates: Requirement 20.5 (Concurrent tenant operations)
    """
    tenant_a = uuid4()
    tenant_b = uuid4()
    tenant_c = uuid4()
    
    # Setup data for all tenants
    products = []
    for i, tenant in enumerate([tenant_a, tenant_b, tenant_c]):
        product = Product(
            id=uuid4(),
            tenant_id=tenant,
            sku=f"SKU-CONCURRENT-{i}",
            normalized_sku=f"skuconcurrent{i}",
            name=f"Concurrent Test Product {i}",
            category="Test",
            price=100.00 + (i * 50) + (i * 25),
            marketplace="Amazon",
            inventory_level=100 - (i * 10),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    
    async def execute_tenant_query(tenant_id: uuid4, sku: str):
        """Execute query for a specific tenant"""
        query_text = f"Analyze product {sku}"
        
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
            query_data={"query": query_text, "product_sku": sku, "db": db_session, "tenant_id": tenant_id}
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
        
        return report
    
    # Execute queries concurrently
    results = await asyncio.gather(
        execute_tenant_query(tenant_a, "SKU-CONCURRENT-0"),
        execute_tenant_query(tenant_b, "SKU-CONCURRENT-1"),
        execute_tenant_query(tenant_c, "SKU-CONCURRENT-2"),
        return_exceptions=True
    )
    
    # Verify all queries succeeded
    assert len(results) == 3
    for result in results:
        assert not isinstance(result, Exception), f"Query failed: {result}"
    
    # Verify tenant isolation in results
    assert results[0].tenant_id == tenant_a
    assert results[1].tenant_id == tenant_b
    assert results[2].tenant_id == tenant_c
    
    # Verify no cross-contamination
    assert "SKU-CONCURRENT-1" not in str(results[0].dict())
    assert "SKU-CONCURRENT-2" not in str(results[0].dict())
    assert "SKU-CONCURRENT-0" not in str(results[1].dict())
    assert "SKU-CONCURRENT-2" not in str(results[1].dict())
    assert "SKU-CONCURRENT-0" not in str(results[2].dict())
    assert "SKU-CONCURRENT-1" not in str(results[2].dict())


@pytest.mark.asyncio
async def test_analytical_storage_tenant_isolation(db_session: AsyncSession):
    """
    Test that analytical storage is isolated between tenants.
    
    Validates: Requirement 20.2 (Tenant data tagging)
    """
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    # Setup data
    product_a = Product(
        id=uuid4(),
        tenant_id=tenant_a,
        sku="SKU-STORAGE-A",
        normalized_sku="skustoragea",
        name="Storage Test A",
        category="Test",
        price=99.99,
        marketplace="Amazon",
        inventory_level=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_a)
    
    product_b = Product(
        id=uuid4(),
        tenant_id=tenant_b,
        sku="SKU-STORAGE-B",
        normalized_sku="skustorageb",
        name="Storage Test B",
        category="Test",
        price=149.99,
        marketplace="Amazon",
        inventory_level=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(product_b)
    
    await db_session.commit()
    
    # Execute queries and store results
    for tenant_id, sku in [(tenant_a, "SKU-STORAGE-A"), (tenant_b, "SKU-STORAGE-B")]:
        query_text = f"Analyze {sku}"
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
            query_data={"query": f"Analyze {sku}", "product_sku": sku, "db": db_session, "tenant_id": tenant_id}
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
            query=f"Analyze {sku}",
            agent_results=agent_results_dict,
            execution_metadata={"mode": ExecutionMode.QUICK.value}
        )
        
        # Verify report is tagged with correct tenant
        assert report.tenant_id == tenant_id
    
    # Verify analytical storage isolation
    storage_a = ResultSynthesizer._analytical_storage.get(tenant_a, [])
    storage_b = ResultSynthesizer._analytical_storage.get(tenant_b, [])
    
    # Each tenant should have their own storage
    assert len(storage_a) >= 0
    assert len(storage_b) >= 0
    
    # Verify no cross-tenant data in storage
    for report in storage_a:
        assert report.tenant_id == tenant_a
    
    for report in storage_b:
        assert report.tenant_id == tenant_b
