"""Property-based tests for API schema conformance"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4
from pydantic import ValidationError

from src.schemas.pricing import (
    PricingAnalysisRequest,
    PricingAnalysisResponse,
    MarginConstraints
)
from src.schemas.sentiment import (
    SentimentAnalysisRequest,
    SentimentAnalysisResult
)
from src.schemas.forecast import (
    ForecastRequest,
    DemandForecastResponse
)
from src.schemas.query import QueryRequest
from src.schemas.report import StructuredReport
from src.schemas.preferences import (
    UserPreferencesRequest,
    UserPreferencesResponse
)


class TestAgentInputOutputSchemaConformance:
    """
    Property 44: Agent inputs and outputs conform to schemas
    Validates: Requirements 9.2
    """
    
    @given(
        product_ids=st.lists(st.uuids(), min_size=1, max_size=5),
        min_margin=st.floats(min_value=0.0, max_value=50.0),
        max_discount=st.floats(min_value=0.0, max_value=50.0)
    )
    @settings(max_examples=10, deadline=None)
    def test_pricing_agent_input_schema_conformance(
        self,
        product_ids,
        min_margin,
        max_discount
    ):
        """Test that pricing agent inputs conform to schema"""
        # Property: Valid inputs must be accepted
        try:
            request = PricingAnalysisRequest(
                product_ids=product_ids,
                margin_constraints=MarginConstraints(
                    min_margin_percentage=min_margin,
                    max_discount_percentage=max_discount
                )
            )
            
            # Property: Schema validation must succeed for valid data
            assert request.product_ids == product_ids
            assert request.margin_constraints.min_margin_percentage == min_margin
            assert request.margin_constraints.max_discount_percentage == max_discount
            
        except ValidationError as e:
            # If validation fails, it should be for a good reason
            pytest.fail(f"Valid input rejected by schema: {e}")
    
    @given(
        query_text=st.text(min_size=1, max_size=500),
        product_ids=st.lists(st.uuids(), min_size=0, max_size=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_query_request_schema_conformance(self, query_text, product_ids):
        """Test that query requests conform to schema"""
        # Property: Valid query requests must be accepted
        try:
            request = QueryRequest(
                query_text=query_text,
                product_ids=product_ids if product_ids else None
            )
            
            # Property: Schema validation must succeed
            assert request.query_text == query_text
            if product_ids:
                assert request.product_ids == product_ids
            
        except ValidationError as e:
            pytest.fail(f"Valid query request rejected by schema: {e}")
    
    @given(
        product_ids=st.lists(st.uuids(), min_size=1, max_size=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_sentiment_agent_input_schema_conformance(self, product_ids):
        """Test that sentiment agent inputs conform to schema"""
        # Property: Valid inputs must be accepted
        try:
            request = SentimentAnalysisRequest(
                product_ids=product_ids
            )
            
            # Property: Schema validation must succeed
            assert request.product_ids == product_ids
            
        except ValidationError as e:
            pytest.fail(f"Valid input rejected by schema: {e}")
    
    @given(
        product_id=st.uuids(),
        forecast_horizon_days=st.sampled_from([7, 30, 90])
    )
    @settings(max_examples=10, deadline=None)
    def test_forecast_agent_input_schema_conformance(self, product_id, forecast_horizon_days):
        """Test that forecast agent inputs conform to schema"""
        # Property: Valid inputs must be accepted
        try:
            request = ForecastRequest(
                product_id=product_id,
                forecast_horizon_days=forecast_horizon_days
            )
            
            # Property: Schema validation must succeed
            assert request.product_id == product_id
            assert request.forecast_horizon_days == forecast_horizon_days
            
        except ValidationError as e:
            pytest.fail(f"Valid input rejected by schema: {e}")
    
    @given(
        kpi_prefs=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.booleans(),
            min_size=0,
            max_size=5
        ),
        marketplaces=st.lists(
            st.sampled_from(["amazon", "ebay", "walmart", "shopify"]),
            min_size=0,
            max_size=4,
            unique=True
        )
    )
    @settings(max_examples=10, deadline=None)
    def test_preferences_input_schema_conformance(self, kpi_prefs, marketplaces):
        """Test that user preferences inputs conform to schema"""
        # Property: Valid inputs must be accepted
        try:
            request = UserPreferencesRequest(
                kpi_preferences=kpi_prefs if kpi_prefs else None,
                marketplace_focus=marketplaces if marketplaces else None
            )
            
            # Property: Schema validation must succeed
            if kpi_prefs:
                assert request.kpi_preferences == kpi_prefs
            if marketplaces:
                assert request.marketplace_focus == marketplaces
            
        except ValidationError as e:
            pytest.fail(f"Valid input rejected by schema: {e}")
    
    def test_structured_report_output_schema_conformance(self):
        """Test that structured report outputs conform to schema"""
        # Property: Valid outputs must be accepted
        try:
            report = StructuredReport(
                report_id=uuid4(),
                tenant_id=uuid4(),
                query="Test query",
                executive_summary="Test summary",
                key_metrics=[],  # List of MetricWithTrend
                insights=[],
                action_items=[],
                overall_confidence=85.0,  # 0-100 scale
                data_quality_warnings=[],
                risks=[],
                recommendations=[],
                uncertainties=[],
                agent_results={}
            )
            
            # Property: Schema validation must succeed
            assert report.executive_summary == "Test summary"
            assert report.overall_confidence == 85.0
            assert isinstance(report.key_metrics, list)
            
        except ValidationError as e:
            pytest.fail(f"Valid output rejected by schema: {e}")
    
    @given(
        invalid_confidence=st.floats(min_value=-10.0, max_value=-0.01) | st.floats(min_value=100.01, max_value=200.0)
    )
    @settings(max_examples=10, deadline=None)
    def test_invalid_confidence_rejected(self, invalid_confidence):
        """Test that invalid confidence scores are rejected"""
        # Property: Invalid confidence scores must be rejected
        with pytest.raises(ValidationError):
            StructuredReport(
                report_id=uuid4(),
                tenant_id=uuid4(),
                query="Test query",
                executive_summary="Test",
                key_metrics=[],
                insights=[],
                action_items=[],
                overall_confidence=invalid_confidence,  # Invalid: must be 0-100
                data_quality_warnings=[],
                risks=[],
                recommendations=[],
                uncertainties=[],
                agent_results={}
            )
    
    def test_empty_query_text_rejected(self):
        """Test that empty query text is rejected"""
        # Property: Empty query text must be rejected
        with pytest.raises(ValidationError):
            QueryRequest(
                query_text="",  # Invalid: empty string
                product_ids=None
            )
    
    def test_invalid_horizon_days_rejected(self):
        """Test that invalid forecast horizons are rejected"""
        # Property: Invalid horizon days must be rejected
        with pytest.raises(ValidationError):
            ForecastRequest(
                product_id=uuid4(),
                forecast_horizon_days=0  # Invalid: must be >= 7
            )
    
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids()
    )
    @settings(max_examples=10, deadline=None)
    def test_preferences_response_schema_conformance(self, user_id, tenant_id):
        """Test that preferences response conforms to schema"""
        # Property: Valid responses must be accepted
        try:
            response = UserPreferencesResponse(
                user_id=user_id,
                tenant_id=tenant_id,
                kpi_preferences={"revenue": True, "margin": False},
                marketplace_focus=["amazon", "ebay"],
                business_goals={"target_revenue": 1000000}
            )
            
            # Property: Schema validation must succeed
            assert response.user_id == user_id
            assert response.tenant_id == tenant_id
            assert isinstance(response.kpi_preferences, dict)
            assert isinstance(response.marketplace_focus, list)
            assert isinstance(response.business_goals, dict)
            
        except ValidationError as e:
            pytest.fail(f"Valid response rejected by schema: {e}")


class TestSchemaFieldValidation:
    """Test that schema field validation works correctly"""
    
    def test_margin_constraints_validation(self):
        """Test margin constraints field validation"""
        # Property: Negative margins must be rejected
        with pytest.raises(ValidationError):
            MarginConstraints(
                min_margin_percentage=-10.0,  # Invalid: negative
                max_discount_percentage=20.0
            )
        
        # Property: Negative discounts must be rejected
        with pytest.raises(ValidationError):
            MarginConstraints(
                min_margin_percentage=20.0,
                max_discount_percentage=-10.0  # Invalid: negative
            )
    
    def test_uuid_field_validation(self):
        """Test UUID field validation"""
        # Property: Invalid UUIDs must be rejected
        with pytest.raises(ValidationError):
            QueryRequest(
                query_text="test query",
                product_ids=["not-a-uuid"]  # Invalid: not a UUID
            )
    
    def test_list_field_validation(self):
        """Test list field validation"""
        # Property: Empty product ID lists should be handled
        request = QueryRequest(
            query_text="test query",
            product_ids=[]  # Valid: empty list
        )
        assert request.product_ids == []
        
        # Property: None should be accepted for optional lists
        request = QueryRequest(
            query_text="test query",
            product_ids=None  # Valid: None for optional field
        )
        assert request.product_ids is None


class TestSchemaRoundTrip:
    """Test that schemas can be serialized and deserialized"""
    
    @given(
        query_text=st.text(min_size=1, max_size=200),
        product_ids=st.lists(st.uuids(), min_size=1, max_size=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_query_request_round_trip(self, query_text, product_ids):
        """Test query request serialization round-trip"""
        # Create request
        request = QueryRequest(
            query_text=query_text,
            product_ids=product_ids
        )
        
        # Serialize to dict
        request_dict = request.model_dump()
        
        # Deserialize back
        request_restored = QueryRequest(**request_dict)
        
        # Property: Round-trip must preserve data
        assert request_restored.query_text == request.query_text
        assert request_restored.product_ids == request.product_ids
    
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids()
    )
    @settings(max_examples=10, deadline=None)
    def test_preferences_response_round_trip(self, user_id, tenant_id):
        """Test preferences response serialization round-trip"""
        # Create response
        response = UserPreferencesResponse(
            user_id=user_id,
            tenant_id=tenant_id,
            kpi_preferences={"revenue": True},
            marketplace_focus=["amazon"],
            business_goals={"target": 1000}
        )
        
        # Serialize to dict
        response_dict = response.model_dump()
        
        # Deserialize back
        response_restored = UserPreferencesResponse(**response_dict)
        
        # Property: Round-trip must preserve data
        assert response_restored.user_id == response.user_id
        assert response_restored.tenant_id == response.tenant_id
        assert response_restored.kpi_preferences == response.kpi_preferences
        assert response_restored.marketplace_focus == response.marketplace_focus
        assert response_restored.business_goals == response.business_goals
