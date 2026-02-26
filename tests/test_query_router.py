"""Tests for Query Router"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from src.orchestration.query_router import QueryRouter
from src.schemas.orchestration import (
    ExecutionMode,
    AgentType,
    ConversationContext,
    CachedResult
)


@pytest.fixture
def router():
    """Create a query router instance"""
    tenant_id = uuid4()
    return QueryRouter(tenant_id=tenant_id)


class TestPatternMatching:
    """Tests for query pattern matching"""
    
    def test_pricing_query_pattern(self, router):
        """Test pricing-related query pattern matching"""
        query = "What are the competitor prices for product X?"
        
        patterns = router.match_patterns(query.lower())
        
        assert len(patterns) > 0
        assert patterns[0].pattern_name == 'pricing_analysis'
        assert AgentType.PRICING in patterns[0].suggested_agents
        assert 'price' in patterns[0].matched_keywords
    
    def test_sentiment_query_pattern(self, router):
        """Test sentiment-related query pattern matching"""
        query = "Show me customer reviews and sentiment for product Y"
        
        patterns = router.match_patterns(query.lower())
        
        assert len(patterns) > 0
        # Should match sentiment pattern
        sentiment_patterns = [p for p in patterns if p.pattern_name == 'sentiment_analysis']
        assert len(sentiment_patterns) > 0
        assert AgentType.SENTIMENT in sentiment_patterns[0].suggested_agents
    
    def test_forecast_query_pattern(self, router):
        """Test forecast-related query pattern matching"""
        query = "Forecast demand for next 30 days"
        
        patterns = router.match_patterns(query.lower())
        
        assert len(patterns) > 0
        forecast_patterns = [p for p in patterns if p.pattern_name == 'demand_forecast']
        assert len(forecast_patterns) > 0
        assert AgentType.DEMAND_FORECAST in forecast_patterns[0].suggested_agents
    
    def test_multi_agent_query_pattern(self, router):
        """Test query requiring multiple agents"""
        query = "Analyze product performance including pricing, reviews, and sales forecast"
        
        patterns = router.match_patterns(query.lower())
        
        assert len(patterns) > 0
        # Should match product_performance pattern
        perf_patterns = [p for p in patterns if p.pattern_name == 'product_performance']
        assert len(perf_patterns) > 0
        # Should suggest multiple agents
        assert len(perf_patterns[0].suggested_agents) >= 2
    
    def test_no_pattern_match(self, router):
        """Test query with no pattern matches"""
        query = "Hello, how are you?"
        
        patterns = router.match_patterns(query.lower())
        
        # Should return empty list for non-business queries
        assert len(patterns) == 0


class TestExecutionModeDetection:
    """Tests for execution mode determination"""
    
    def test_quick_mode_simple_query(self, router):
        """Test quick mode for simple queries"""
        query = "What is the price of product X?"
        patterns = router.match_patterns(query.lower())
        
        mode = router.determine_execution_mode(query.lower(), patterns)
        
        assert mode == ExecutionMode.QUICK
    
    def test_deep_mode_keyword(self, router):
        """Test deep mode triggered by keywords"""
        query = "Provide a comprehensive analysis of product performance"
        patterns = router.match_patterns(query.lower())
        
        mode = router.determine_execution_mode(query.lower(), patterns)
        
        assert mode == ExecutionMode.DEEP
    
    def test_deep_mode_multiple_agents(self, router):
        """Test deep mode for queries requiring many agents"""
        query = "Analyze pricing, sentiment, and forecast for all products"
        patterns = router.match_patterns(query.lower())
        
        mode = router.determine_execution_mode(query.lower(), patterns)
        
        # Should use deep mode for complex multi-agent queries
        assert mode == ExecutionMode.DEEP


class TestQueryRouting:
    """Tests for complete query routing"""
    
    def test_route_pricing_query(self, router):
        """Test routing a pricing query"""
        query = "Show me competitor prices"
        
        decision = router.route_query(query)
        
        assert decision.execution_mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]
        assert AgentType.PRICING in decision.required_agents
        assert decision.estimated_duration is not None
    
    def test_route_sentiment_query(self, router):
        """Test routing a sentiment query"""
        query = "What do customers say about our products?"
        
        decision = router.route_query(query)
        
        assert AgentType.SENTIMENT in decision.required_agents
    
    def test_route_forecast_query(self, router):
        """Test routing a forecast query"""
        query = "Predict sales for next month"
        
        decision = router.route_query(query)
        
        assert AgentType.DEMAND_FORECAST in decision.required_agents
    
    def test_route_complex_query(self, router):
        """Test routing a complex multi-agent query"""
        query = "Comprehensive analysis of product X including pricing, reviews, and demand"
        
        decision = router.route_query(query)
        
        # Should require multiple agents
        assert len(decision.required_agents) >= 2
        # Complex queries should use deep mode
        assert decision.execution_mode == ExecutionMode.DEEP
    
    def test_route_with_context(self, router):
        """Test routing with conversation context"""
        context = ConversationContext(
            conversation_id=uuid4(),
            previous_queries=["What are the prices?"],
            user_preferences={"mode": "quick"}
        )
        
        query = "And what about reviews?"
        decision = router.route_query(query, context)
        
        assert decision is not None
        assert len(decision.required_agents) > 0


class TestCacheOperations:
    """Tests for cache operations"""
    
    def test_cache_key_generation(self, router):
        """Test cache key generation"""
        query = "What are the prices?"
        agents = [AgentType.PRICING]
        
        key1 = router._generate_cache_key(query, agents)
        key2 = router._generate_cache_key(query, agents)
        
        # Same query and agents should produce same key
        assert key1 == key2
        
        # Different query should produce different key
        key3 = router._generate_cache_key("Different query", agents)
        assert key1 != key3
    
    def test_cache_check_no_client(self, router):
        """Test cache check without cache client"""
        result = router.check_cache("some_hash")
        
        # Should return None when no cache client
        assert result is None


class TestDurationEstimation:
    """Tests for duration estimation"""
    
    def test_quick_mode_duration(self, router):
        """Test duration estimation for quick mode"""
        duration = router._estimate_duration(ExecutionMode.QUICK, 1)
        
        assert duration.total_seconds() > 0
        assert duration.total_seconds() < 120  # Should be under 2 minutes
    
    def test_deep_mode_duration(self, router):
        """Test duration estimation for deep mode"""
        duration = router._estimate_duration(ExecutionMode.DEEP, 1)
        
        assert duration.total_seconds() >= 120  # Should be at least 2 minutes
        assert duration.total_seconds() < 600  # Should be under 10 minutes
    
    def test_duration_scales_with_agents(self, router):
        """Test that duration scales with number of agents"""
        duration_1 = router._estimate_duration(ExecutionMode.QUICK, 1)
        duration_3 = router._estimate_duration(ExecutionMode.QUICK, 3)
        
        # More agents should take longer
        assert duration_3.total_seconds() > duration_1.total_seconds()


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_query(self, router):
        """Test handling of empty query"""
        query = ""
        
        decision = router.route_query(query)
        
        # Should still return a decision
        assert decision is not None
        assert len(decision.required_agents) > 0
    
    def test_very_long_query(self, router):
        """Test handling of very long query"""
        query = "price " * 100  # Very long query
        
        decision = router.route_query(query)
        
        assert decision is not None
        assert AgentType.PRICING in decision.required_agents
