"""Tests for LLM provider abstraction layer"""
import pytest
from uuid import uuid4

from src.orchestration.llm_providers import (
    BaseLLMProvider,
    OpenAIProvider,
    GeminiProvider,
    LLMResponse
)
from src.orchestration.llm_reasoning_engine import LLMReasoningEngine


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
        self.call_count = 0
    
    async def complete(
        self,
        prompt: str,
        conversation_history=None,
        temperature=0.7,
        max_tokens=2000,
        json_mode=True
    ) -> LLMResponse:
        """Mock completion"""
        self.call_count += 1
        
        # Return mock JSON response
        content = '''{
            "intent": "test_intent",
            "key_entities": {"products": ["test_product"]},
            "required_capabilities": ["pricing_analysis"],
            "suggested_agents": ["pricing"],
            "reasoning": "Mock reasoning",
            "confidence": 0.9
        }'''
        
        return LLMResponse(
            content=content,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model=self.model,
            cost_usd=0.01
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Mock cost estimation"""
        return 0.01
    
    def get_model_name(self) -> str:
        """Get mock model name"""
        return self.model


def test_base_provider_interface():
    """Test that BaseLLMProvider defines the correct interface"""
    assert hasattr(BaseLLMProvider, 'complete')
    assert hasattr(BaseLLMProvider, 'estimate_cost')
    assert hasattr(BaseLLMProvider, 'get_model_name')


def test_mock_provider():
    """Test mock provider implementation"""
    import asyncio
    
    provider = MockLLMProvider()
    
    # Test completion
    loop = asyncio.new_event_loop()
    response = loop.run_until_complete(
        provider.complete("test prompt")
    )
    
    assert isinstance(response, LLMResponse)
    assert response.prompt_tokens == 100
    assert response.completion_tokens == 50
    assert response.total_tokens == 150
    assert response.model == "mock-model"
    assert response.cost_usd == 0.01
    assert provider.call_count == 1


def test_openai_provider_cost_estimation():
    """Test OpenAI provider cost estimation"""
    # Don't need real API key for cost estimation
    provider = OpenAIProvider(api_key="fake-key", model="gpt-4")
    
    # Test GPT-4 pricing
    cost = provider.estimate_cost(1000, 500)
    expected = (1000 / 1000 * 0.03) + (500 / 1000 * 0.06)
    assert cost == round(expected, 4)
    
    # Test GPT-3.5-turbo pricing
    provider_35 = OpenAIProvider(api_key="fake-key", model="gpt-3.5-turbo")
    cost_35 = provider_35.estimate_cost(1000, 500)
    expected_35 = (1000 / 1000 * 0.0015) + (500 / 1000 * 0.002)
    assert cost_35 == round(expected_35, 4)


def test_gemini_provider_cost_estimation():
    """Test Gemini provider cost estimation"""
    try:
        # Don't need real API key for cost estimation
        provider = GeminiProvider(api_key="fake-key", model="gemini-pro")
        
        # Test Gemini Pro pricing (per 1M tokens)
        cost = provider.estimate_cost(1_000_000, 500_000)
        expected = (1_000_000 / 1_000_000 * 0.50) + (500_000 / 1_000_000 * 1.50)
        assert cost == round(expected, 6)
        
    except ImportError:
        pytest.skip("google-generativeai not installed")


def test_llm_reasoning_engine_with_mock_provider():
    """Test LLMReasoningEngine with mock provider"""
    tenant_id = uuid4()
    mock_provider = MockLLMProvider()
    
    engine = LLMReasoningEngine(
        tenant_id=tenant_id,
        llm_provider=mock_provider
    )
    
    # Test query understanding
    understanding = engine.understand_query("What are my pricing gaps?")
    
    assert understanding.intent == "test_intent"
    assert "products" in understanding.key_entities
    assert "pricing_analysis" in understanding.required_capabilities
    assert mock_provider.call_count == 1
    
    # Check token usage tracking
    assert len(engine.token_usage_history) == 1
    usage = engine.token_usage_history[0]
    assert usage.total_tokens == 150
    assert usage.cost_usd == 0.01


def test_llm_reasoning_engine_fallback():
    """Test LLMReasoningEngine fallback when no provider"""
    tenant_id = uuid4()
    
    # Create engine without provider
    engine = LLMReasoningEngine(
        tenant_id=tenant_id,
        llm_provider=None
    )
    
    # Should use fallback rule-based understanding
    understanding = engine.understand_query("What are my pricing gaps?")
    
    assert understanding.intent == "general_analysis"
    assert understanding.reasoning == "Fallback rule-based understanding"
    assert len(understanding.suggested_agents) > 0


def test_provider_selection_openai():
    """Test provider selection for OpenAI"""
    from src.config import settings
    
    # Save original values
    original_provider = settings.llm_provider
    original_key = settings.openai_api_key
    
    try:
        # Set OpenAI configuration
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key"
        
        tenant_id = uuid4()
        engine = LLMReasoningEngine(tenant_id=tenant_id)
        
        assert engine.llm_provider is not None
        assert isinstance(engine.llm_provider, OpenAIProvider)
        
    finally:
        # Restore original values
        settings.llm_provider = original_provider
        settings.openai_api_key = original_key


def test_provider_selection_gemini():
    """Test provider selection for Gemini"""
    from src.config import settings
    
    # Save original values
    original_provider = settings.llm_provider
    original_key = getattr(settings, 'gemini_api_key', '')
    
    try:
        # Set Gemini configuration
        settings.llm_provider = "gemini"
        settings.gemini_api_key = "test-key"
        
        tenant_id = uuid4()
        
        try:
            engine = LLMReasoningEngine(tenant_id=tenant_id)
            
            assert engine.llm_provider is not None
            assert isinstance(engine.llm_provider, GeminiProvider)
            
        except ImportError:
            pytest.skip("google-generativeai not installed")
        
    finally:
        # Restore original values
        settings.llm_provider = original_provider
        if hasattr(settings, 'gemini_api_key'):
            settings.gemini_api_key = original_key


def test_token_usage_tracking():
    """Test token usage tracking across multiple calls"""
    tenant_id = uuid4()
    mock_provider = MockLLMProvider()
    
    engine = LLMReasoningEngine(
        tenant_id=tenant_id,
        llm_provider=mock_provider
    )
    
    # Make multiple queries
    engine.understand_query("Query 1")
    engine.understand_query("Query 2")
    engine.understand_query("Query 3")
    
    # Check token usage
    stats = engine.get_total_token_usage()
    
    assert stats['request_count'] == 3
    assert stats['total_tokens'] == 450  # 150 * 3
    assert stats['total_cost_usd'] == 0.03  # 0.01 * 3
    assert stats['avg_tokens_per_request'] == 150


def test_conversation_context():
    """Test conversation context management"""
    tenant_id = uuid4()
    mock_provider = MockLLMProvider()
    
    engine = LLMReasoningEngine(
        tenant_id=tenant_id,
        llm_provider=mock_provider
    )
    
    conversation_id = str(uuid4())  # Use UUID string
    
    # Make queries with conversation context
    engine.understand_query("Query 1", conversation_id=conversation_id)
    engine.understand_query("Query 2", conversation_id=conversation_id)
    
    # Check conversation context
    context = engine.get_conversation_context(conversation_id)
    
    assert context is not None
    assert len(context.previous_queries) == 2
    assert "Query 1" in context.previous_queries
    assert "Query 2" in context.previous_queries
    
    # Clear context
    cleared = engine.clear_conversation_context(conversation_id)
    assert cleared is True
    
    # Verify cleared
    context_after = engine.get_conversation_context(conversation_id)
    assert context_after is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
