"""
Tests for LLM Reasoning Engine

These tests verify the LLM Reasoning Engine functionality including:
- Query understanding
- Agent selection
- Execution plan generation
- Token usage tracking
- Prompt optimization
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, MagicMock

from src.orchestration.llm_reasoning_engine import (
    LLMReasoningEngine,
    AgentType,
    ExecutionMode,
    QueryIntent,
    ExecutionPlan,
    TokenUsage
)
from src.orchestration.prompt_optimizer import (
    PromptOptimizer,
    PromptCache,
    ContextCompressor
)


class TestTokenUsage:
    """Tests for TokenUsage tracking"""
    
    def test_token_usage_initialization(self):
        """Test TokenUsage initializes with zero values"""
        usage = TokenUsage()
        
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.estimated_cost_usd == 0.0
    
    def test_token_usage_add_usage(self):
        """Test adding token usage"""
        usage = TokenUsage()
        
        usage.add_usage(100, 50)
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.estimated_cost_usd > 0
    
    def test_token_usage_to_dict(self):
        """Test converting TokenUsage to dictionary"""
        usage = TokenUsage()
        usage.add_usage(100, 50)
        
        result = usage.to_dict()
        
        assert "prompt_tokens" in result
        assert "completion_tokens" in result
        assert "total_tokens" in result
        assert "estimated_cost_usd" in result
        assert result["total_tokens"] == 150


class TestExecutionPlan:
    """Tests for ExecutionPlan"""
    
    def test_execution_plan_creation(self):
        """Test creating an execution plan"""
        query_id = "test-query-123"
        product_ids = [uuid4(), uuid4()]
        
        plan = ExecutionPlan(
            query_id=query_id,
            intent=QueryIntent.PRICING_ANALYSIS,
            agents=[AgentType.PRICING],
            execution_mode=ExecutionMode.QUICK,
            product_ids=product_ids,
            parameters={"include_recommendations": True},
            parallel_execution=False,
            estimated_duration_seconds=30
        )
        
        assert plan.query_id == query_id
        assert plan.intent == QueryIntent.PRICING_ANALYSIS
        assert len(plan.agents) == 1
        assert plan.agents[0] == AgentType.PRICING
        assert plan.execution_mode == ExecutionMode.QUICK
        assert len(plan.product_ids) == 2
    
    def test_execution_plan_to_dict(self):
        """Test converting ExecutionPlan to dictionary"""
        plan = ExecutionPlan(
            query_id="test-123",
            intent=QueryIntent.SENTIMENT_ANALYSIS,
            agents=[AgentType.SENTIMENT],
            execution_mode=ExecutionMode.DEEP,
            product_ids=[uuid4()],
            parameters={},
            parallel_execution=True,
            estimated_duration_seconds=60
        )
        
        result = plan.to_dict()
        
        assert "query_id" in result
        assert "intent" in result
        assert "agents" in result
        assert "execution_mode" in result
        assert "product_ids" in result
        assert result["intent"] == "sentiment_analysis"


class TestLLMReasoningEngine:
    """Tests for LLM Reasoning Engine"""
    
    @patch('src.orchestration.llm_reasoning_engine.settings')
    def test_engine_initialization_openai(self, mock_settings):
        """Test initializing engine with OpenAI"""
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            engine = LLMReasoningEngine(tenant_id)
            
            assert engine.tenant_id == tenant_id
            assert isinstance(engine.token_usage, TokenUsage)
            assert isinstance(engine.prompt_cache, dict)
    
    def test_select_agents_pricing_intent(self):
        """Test agent selection for pricing intent"""
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            with patch('src.orchestration.llm_reasoning_engine.settings') as mock_settings:
                mock_settings.llm_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_model = "gpt-4"
                
                engine = LLMReasoningEngine(tenant_id)
                
                agents = engine.select_agents(
                    QueryIntent.PRICING_ANALYSIS,
                    {}
                )
                
                assert AgentType.PRICING in agents
                assert len(agents) == 1
    
    def test_select_agents_product_performance(self):
        """Test agent selection for product performance (multi-agent)"""
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            with patch('src.orchestration.llm_reasoning_engine.settings') as mock_settings:
                mock_settings.llm_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_model = "gpt-4"
                
                engine = LLMReasoningEngine(tenant_id)
                
                agents = engine.select_agents(
                    QueryIntent.PRODUCT_PERFORMANCE,
                    {}
                )
                
                # Product performance requires all agents
                assert AgentType.PRICING in agents
                assert AgentType.SENTIMENT in agents
                assert AgentType.FORECAST in agents
                assert len(agents) == 3
    
    def test_generate_execution_plan(self):
        """Test generating execution plan"""
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            with patch('src.orchestration.llm_reasoning_engine.settings') as mock_settings:
                mock_settings.llm_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_model = "gpt-4"
                
                engine = LLMReasoningEngine(tenant_id)
                
                plan = engine.generate_execution_plan(
                    query_id="test-123",
                    query="What are the prices for my products?",
                    intent=QueryIntent.PRICING_ANALYSIS,
                    parameters={"product_ids": [str(uuid4())]},
                    execution_mode=ExecutionMode.QUICK
                )
                
                assert isinstance(plan, ExecutionPlan)
                assert plan.query_id == "test-123"
                assert plan.intent == QueryIntent.PRICING_ANALYSIS
                assert plan.execution_mode == ExecutionMode.QUICK
                assert len(plan.agents) > 0
    
    def test_fallback_query_understanding(self):
        """Test fallback keyword-based query understanding"""
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            with patch('src.orchestration.llm_reasoning_engine.settings') as mock_settings:
                mock_settings.llm_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_model = "gpt-4"
                
                engine = LLMReasoningEngine(tenant_id)
                
                # Test pricing keywords
                intent, params = engine._fallback_query_understanding(
                    "What are the competitor prices?"
                )
                assert intent == QueryIntent.PRICING_ANALYSIS
                
                # Test sentiment keywords
                intent, params = engine._fallback_query_understanding(
                    "Show me customer reviews"
                )
                assert intent == QueryIntent.SENTIMENT_ANALYSIS
                
                # Test forecast keywords
                intent, params = engine._fallback_query_understanding(
                    "Predict future demand"
                )
                assert intent == QueryIntent.DEMAND_FORECAST
    
    def test_extract_product_ids(self):
        """Test extracting product IDs from parameters"""
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            with patch('src.orchestration.llm_reasoning_engine.settings') as mock_settings:
                mock_settings.llm_provider = "openai"
                mock_settings.openai_api_key = "test-key"
                mock_settings.openai_model = "gpt-4"
                
                engine = LLMReasoningEngine(tenant_id)
                
                uuid1 = uuid4()
                uuid2 = uuid4()
                
                parameters = {
                    "product_ids": [str(uuid1), str(uuid2)]
                }
                
                product_ids = engine._extract_product_ids(parameters)
                
                assert len(product_ids) == 2
                assert all(isinstance(pid, UUID) for pid in product_ids)


class TestPromptOptimizer:
    """Tests for Prompt Optimizer"""
    
    def test_prompt_optimizer_initialization(self):
        """Test PromptOptimizer initializes with templates"""
        optimizer = PromptOptimizer()
        
        assert len(optimizer.templates) > 0
        assert isinstance(optimizer.cache, PromptCache)
        assert isinstance(optimizer.compressor, ContextCompressor)
    
    def test_get_template(self):
        """Test getting prompt template"""
        optimizer = PromptOptimizer()
        
        template = optimizer.get_template("query_understanding")
        
        assert template is not None
        assert template.name == "query_understanding"
        assert len(template.system_prompt) > 0
    
    def test_optimize_prompt(self):
        """Test optimizing prompt with template"""
        optimizer = PromptOptimizer()
        
        system_prompt, user_prompt = optimizer.optimize_prompt(
            "query_understanding",
            query="What are my product prices?"
        )
        
        assert len(system_prompt) > 0
        assert "What are my product prices?" in user_prompt
    
    def test_prompt_cache(self):
        """Test prompt caching"""
        cache = PromptCache(ttl_seconds=3600)
        
        prompt = "Test prompt"
        response = "Test response"
        
        # Cache should be empty initially
        assert cache.get(prompt) is None
        
        # Set cache
        cache.set(prompt, response)
        
        # Should retrieve cached response
        cached = cache.get(prompt)
        assert cached == response
    
    def test_context_compressor(self):
        """Test context compression"""
        compressor = ContextCompressor(max_messages=3)
        
        conversation = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
        ]
        
        compressed = compressor.compress(conversation)
        
        # Should keep only last 3 messages
        assert len(compressed) == 3
        assert compressed[0]["content"] == "Message 2"
    
    def test_context_summarization(self):
        """Test context summarization"""
        compressor = ContextCompressor()
        
        conversation = [
            {"role": "user", "content": "What are the prices for my products?"},
            {"role": "assistant", "content": "Here are the pricing details..."},
            {"role": "user", "content": "Show me customer reviews"},
        ]
        
        summary = compressor.summarize_context(conversation)
        
        assert len(summary) > 0
        assert "pricing" in summary.lower() or "sentiment" in summary.lower()


class TestIntegration:
    """Integration tests for LLM Reasoning Engine"""
    
    @patch('src.orchestration.llm_reasoning_engine.settings')
    def test_end_to_end_query_processing(self, mock_settings):
        """Test end-to-end query processing flow"""
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        
        tenant_id = uuid4()
        
        with patch('openai.OpenAI'):
            engine = LLMReasoningEngine(tenant_id)
            
            # Generate execution plan
            plan = engine.generate_execution_plan(
                query_id="test-123",
                query="Analyze product performance",
                intent=QueryIntent.PRODUCT_PERFORMANCE,
                parameters={"product_ids": [str(uuid4())]},
                execution_mode=ExecutionMode.DEEP
            )
            
            # Verify plan
            assert plan.query_id == "test-123"
            assert len(plan.agents) > 0
            assert plan.execution_mode == ExecutionMode.DEEP
            
            # Get token usage
            usage = engine.get_token_usage()
            assert "total_tokens" in usage
