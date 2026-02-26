"""
Property-based tests for data models and round-trip validation

Feature: ecommerce-intelligence-agent
Tasks: 3.5, 3.6
Requirements: 2.6, 20.2
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, date
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tenant import Tenant
from src.models.product import Product
from src.models.analytical_report import AnalyticalReport
from src.models.forecast_result import ForecastResult
from src.models.aggregated_metrics import AggregatedMetrics


# Strategies for generating test data
uuid_strategy = st.builds(uuid4)

tenant_strategy = st.fixed_dictionaries({
    'name': st.text(min_size=3, max_size=50),
    'slug': st.text(min_size=3, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    'contact_email': st.emails(),
    'plan': st.sampled_from(['free', 'basic', 'pro', 'enterprise'])
})

product_strategy = st.fixed_dictionaries({
    'sku': st.text(min_size=5, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    'name': st.text(min_size=3, max_size=100),
    'category': st.sampled_from(['Electronics', 'Clothing', 'Home', 'Sports', 'Books']),
    'price': st.decimals(min_value=0.01, max_value=10000, places=2),
    'marketplace': st.sampled_from(['Amazon', 'eBay', 'Walmart', 'Target'])
})

analytical_report_strategy = st.fixed_dictionaries({
    'executive_summary': st.text(min_size=10, max_size=500),
    'overall_confidence': st.floats(min_value=0.0, max_value=1.0),
    'execution_mode': st.sampled_from(['QUICK', 'DEEP'])
})

forecast_result_strategy = st.fixed_dictionaries({
    'forecast_horizon_days': st.integers(min_value=7, max_value=90),
    'model_version': st.text(min_size=3, max_size=20),
    'confidence_score': st.floats(min_value=0.0, max_value=1.0),
    'seasonality_detected': st.booleans()
})

aggregated_metrics_strategy = st.fixed_dictionaries({
    'metric_type': st.sampled_from(['sales', 'pricing', 'sentiment', 'inventory']),
    'metric_name': st.sampled_from(['total_revenue', 'avg_price', 'avg_rating', 'stock_level']),
    'aggregation_period': st.sampled_from(['daily', 'weekly', 'monthly']),
    'metric_value': st.floats(min_value=0.0, max_value=1000000.0)
})


class TestDataRoundTripProperties:
    """
    Property-based tests for data round-trip validation
    
    These tests verify that:
    1. Data can be written to and read from the database without loss (Property 9)
    2. All stored data is tagged with tenant_id (Property 83)
    """
    
    @pytest.mark.asyncio
    @given(
        tenant_data=tenant_strategy,
        product_data=product_strategy
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_property_9_validated_data_round_trip(
        self,
        tenant_data,
        product_data,
        async_db_session
    ):
        """
        Property 9: Validated data round-trip
        
        GIVEN valid data for a tenant and product
        WHEN the data is written to the database and then read back
        THEN all fields should match exactly (no data loss)
        
        Validates: Requirements 2.6
        """
        # Feature: ecommerce-intelligence-agent, Property 9: Validated data round-trip
        
        # Make slug unique by adding UUID suffix to avoid collisions
        unique_slug = f"{tenant_data['slug']}-{str(uuid4())[:8]}"
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data['name'],
            slug=unique_slug,
            contact_email=tenant_data['contact_email'],
            plan=tenant_data['plan'],
            is_active=True
        )
        async_db_session.add(tenant)
        await async_db_session.flush()
        
        # Store original tenant values
        original_tenant_id = tenant.id
        original_tenant_name = tenant.name
        original_tenant_slug = tenant.slug
        original_tenant_email = tenant.contact_email
        original_tenant_plan = tenant.plan
        
        # Create product
        product = Product(
            tenant_id=tenant.id,
            sku=product_data['sku'],
            normalized_sku=product_data['sku'].lower(),
            name=product_data['name'],
            category=product_data['category'],
            price=float(product_data['price']),
            currency='USD',
            marketplace=product_data['marketplace'],
            inventory_level=100
        )
        async_db_session.add(product)
        await async_db_session.flush()
        
        # Store original product values
        original_product_id = product.id
        original_product_sku = product.sku
        original_product_name = product.name
        original_product_price = product.price
        original_product_marketplace = product.marketplace
        
        # Read tenant back from database
        result_tenant = await async_db_session.execute(
            select(Tenant).where(Tenant.id == original_tenant_id)
        )
        retrieved_tenant = result_tenant.scalar_one_or_none()
        
        # PROPERTY: Tenant data round-trip is lossless
        assert retrieved_tenant is not None, "Tenant should be retrievable"
        assert retrieved_tenant.id == original_tenant_id, "Tenant ID should match"
        assert retrieved_tenant.name == original_tenant_name, "Tenant name should match"
        assert retrieved_tenant.slug == original_tenant_slug, "Tenant slug should match"
        assert retrieved_tenant.contact_email == original_tenant_email, "Tenant email should match"
        assert retrieved_tenant.plan == original_tenant_plan, "Tenant plan should match"
        
        # Read product back from database
        result_product = await async_db_session.execute(
            select(Product).where(Product.id == original_product_id)
        )
        retrieved_product = result_product.scalar_one_or_none()
        
        # PROPERTY: Product data round-trip is lossless
        assert retrieved_product is not None, "Product should be retrievable"
        assert retrieved_product.id == original_product_id, "Product ID should match"
        assert retrieved_product.sku == original_product_sku, "Product SKU should match"
        assert retrieved_product.name == original_product_name, "Product name should match"
        assert float(retrieved_product.price) == original_product_price, "Product price should match"
        assert retrieved_product.marketplace == original_product_marketplace, "Product marketplace should match"
        assert retrieved_product.tenant_id == original_tenant_id, "Product tenant_id should match"
    
    @pytest.mark.asyncio
    @given(
        tenant_data=tenant_strategy,
        product_data=product_strategy,
        report_data=analytical_report_strategy,
        forecast_data=forecast_result_strategy,
        metrics_data=aggregated_metrics_strategy
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_property_83_all_data_tagged_with_tenant_id(
        self,
        tenant_data,
        product_data,
        report_data,
        forecast_data,
        metrics_data,
        async_db_session
    ):
        """
        Property 83: All stored data is tagged with tenant ID
        
        GIVEN various data models (Product, AnalyticalReport, ForecastResult, AggregatedMetrics)
        WHEN they are created and stored in the database
        THEN all records MUST have a tenant_id field populated
        AND the tenant_id MUST reference a valid tenant
        
        Validates: Requirements 20.2
        """
        # Feature: ecommerce-intelligence-agent, Property 83: All stored data is tagged with tenant ID
        
        # Make slug unique by adding UUID suffix to avoid collisions
        unique_slug = f"{tenant_data['slug']}-{str(uuid4())[:8]}"
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data['name'],
            slug=unique_slug,
            contact_email=tenant_data['contact_email'],
            plan=tenant_data['plan'],
            is_active=True
        )
        async_db_session.add(tenant)
        await async_db_session.flush()
        
        tenant_id = tenant.id
        
        # Create product
        product = Product(
            tenant_id=tenant_id,
            sku=product_data['sku'],
            normalized_sku=product_data['sku'].lower(),
            name=product_data['name'],
            category=product_data['category'],
            price=float(product_data['price']),
            currency='USD',
            marketplace=product_data['marketplace'],
            inventory_level=100
        )
        async_db_session.add(product)
        await async_db_session.flush()
        
        # PROPERTY: Product has tenant_id
        assert product.tenant_id is not None, "Product must have tenant_id"
        assert product.tenant_id == tenant_id, "Product tenant_id must match tenant"
        
        # Create analytical report
        report = AnalyticalReport(
            tenant_id=tenant_id,
            query_id=uuid4(),
            executive_summary=report_data['executive_summary'],
            key_metrics={'revenue': 1000.0},
            agent_results=[{'agent': 'pricing', 'result': 'success'}],
            action_items=[{'action': 'review pricing', 'priority': 'high'}],
            overall_confidence=report_data['overall_confidence'],
            execution_mode=report_data['execution_mode']
        )
        async_db_session.add(report)
        await async_db_session.flush()
        
        # PROPERTY: AnalyticalReport has tenant_id
        assert report.tenant_id is not None, "AnalyticalReport must have tenant_id"
        assert report.tenant_id == tenant_id, "AnalyticalReport tenant_id must match tenant"
        
        # Create forecast result
        forecast = ForecastResult(
            tenant_id=tenant_id,
            product_id=product.id,
            forecast_horizon_days=forecast_data['forecast_horizon_days'],
            model_version=forecast_data['model_version'],
            predicted_demand=[10.0, 12.0, 15.0],
            confidence_intervals=[[8.0, 12.0], [10.0, 14.0], [13.0, 17.0]],
            confidence_score=forecast_data['confidence_score'],
            seasonality_detected=forecast_data['seasonality_detected']
        )
        async_db_session.add(forecast)
        await async_db_session.flush()
        
        # PROPERTY: ForecastResult has tenant_id
        assert forecast.tenant_id is not None, "ForecastResult must have tenant_id"
        assert forecast.tenant_id == tenant_id, "ForecastResult tenant_id must match tenant"
        
        # Create aggregated metrics
        metrics = AggregatedMetrics(
            tenant_id=tenant_id,
            product_id=product.id,
            metric_type=metrics_data['metric_type'],
            metric_name=metrics_data['metric_name'],
            aggregation_period=metrics_data['aggregation_period'],
            period_start=date.today(),
            period_end=date.today(),
            metric_value=metrics_data['metric_value']
        )
        async_db_session.add(metrics)
        await async_db_session.flush()
        
        # PROPERTY: AggregatedMetrics has tenant_id
        assert metrics.tenant_id is not None, "AggregatedMetrics must have tenant_id"
        assert metrics.tenant_id == tenant_id, "AggregatedMetrics tenant_id must match tenant"
        
        # PROPERTY: All records can be queried by tenant_id
        result_products = await async_db_session.execute(
            select(Product).where(Product.tenant_id == tenant_id)
        )
        tenant_products = result_products.scalars().all()
        assert len(tenant_products) >= 1, "Should find at least one product for tenant"
        
        result_reports = await async_db_session.execute(
            select(AnalyticalReport).where(AnalyticalReport.tenant_id == tenant_id)
        )
        tenant_reports = result_reports.scalars().all()
        assert len(tenant_reports) >= 1, "Should find at least one report for tenant"
        
        result_forecasts = await async_db_session.execute(
            select(ForecastResult).where(ForecastResult.tenant_id == tenant_id)
        )
        tenant_forecasts = result_forecasts.scalars().all()
        assert len(tenant_forecasts) >= 1, "Should find at least one forecast for tenant"
        
        result_metrics = await async_db_session.execute(
            select(AggregatedMetrics).where(AggregatedMetrics.tenant_id == tenant_id)
        )
        tenant_metrics = result_metrics.scalars().all()
        assert len(tenant_metrics) >= 1, "Should find at least one metrics record for tenant"
        
        # PROPERTY: No records exist without tenant_id
        result_orphan_products = await async_db_session.execute(
            select(Product).where(Product.tenant_id.is_(None))
        )
        orphan_products = result_orphan_products.scalars().all()
        assert len(orphan_products) == 0, "No products should exist without tenant_id"
