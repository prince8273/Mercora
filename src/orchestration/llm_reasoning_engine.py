"""
LLM Reasoning Engine - Query Understanding and Agent Selection

This component uses LLM (OpenAI GPT-4 or Gemini) to:
1. Understand complex natural language queries
2. Identify which intelligence agents are needed
3. Generate execution plans for multi-agent coordination
4. Track token usage for cost governance
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum

from src.config import settings
from src.schemas.orchestration import (
    ExecutionPlan as SchemaExecutionPlan,
    AgentTask,
    ExecutionMode as SchemaExecutionMode,
    AgentType as SchemaAgentType,
)

logger = logging.getLogger(__name__)


# Use schema versions for consistency
AgentType = SchemaAgentType
ExecutionMode = SchemaExecutionMode


class QueryIntent(str, Enum):
    """Identified query intents"""
    PRICING_ANALYSIS = "pricing_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    DEMAND_FORECAST = "demand_forecast"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    PRODUCT_PERFORMANCE = "product_performance"
    MULTI_AGENT = "multi_agent"
    UNKNOWN = "unknown"


class TokenUsage:
    """Token usage tracking for cost governance"""
    
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.estimated_cost_usd = 0.0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        """Add token usage"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
        
        # Estimate cost (GPT-4 pricing as of 2024)
        # Input: $0.03 per 1K tokens, Output: $0.06 per 1K tokens
        self.estimated_cost_usd += (
            (prompt_tokens / 1000) * 0.03 +
            (completion_tokens / 1000) * 0.06
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4)
        }


class LLMReasoningEngine:
    """
    LLM-powered reasoning engine for query understanding and agent orchestration.
    
    Features:
    - Natural language query understanding
    - Intent classification
    - Agent selection based on query requirements
    - Execution plan generation
    - Token usage tracking
    - Prompt optimization and caching
    """
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize LLM Reasoning Engine
        
        Args:
            tenant_id: Tenant UUID for multi-tenancy isolation
        """
        self.tenant_id = tenant_id
        self.token_usage = TokenUsage()
        self.prompt_cache: Dict[str, Any] = {}
        
        # Initialize LLM client based on provider
        if settings.llm_provider == "openai":
            self._init_openai()
        elif settings.llm_provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY in .env file.")
            
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            logger.info(f"Initialized OpenAI client with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key is not configured. Please set GEMINI_API_KEY in .env file.")
            
            genai.configure(api_key=settings.gemini_api_key)
            self.client = genai.GenerativeModel(settings.gemini_model)
            self.model = settings.gemini_model
            logger.info(f"Initialized Gemini client with model: {self.model}")
        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def understand_query(
        self,
        query: str,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[QueryIntent, Dict[str, Any]]:
        """
        Understand user query and extract intent and parameters.
        
        Args:
            query: Natural language query from user
            conversation_context: Optional conversation history for context
            
        Returns:
            Tuple of (intent, extracted_parameters)
        """
        # Check prompt cache for similar queries
        cache_key = self._generate_cache_key(query)
        if cache_key in self.prompt_cache:
            logger.info("Using cached query understanding")
            cached = self.prompt_cache[cache_key]
            return cached["intent"], cached["parameters"]
        
        # Build prompt for query understanding
        system_prompt = self._get_query_understanding_prompt()
        user_prompt = self._build_user_prompt(query, conversation_context)
        
        # Call LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)
            
            # Parse response
            intent, parameters = self._parse_query_understanding_response(response)
            
            # Cache result
            self.prompt_cache[cache_key] = {
                "intent": intent,
                "parameters": parameters
            }
            
            return intent, parameters
        
        except Exception as e:
            logger.error(f"Error understanding query: {e}")
            # Fallback to keyword-based understanding
            return self._fallback_query_understanding(query)
    
    def select_agents(
        self,
        intent: QueryIntent,
        parameters: Dict[str, Any]
    ) -> List[AgentType]:
        """
        Select which intelligence agents are needed based on query intent.
        
        Args:
            intent: Identified query intent
            parameters: Extracted parameters from query
            
        Returns:
            List of agent types to execute
        """
        # Intent to agent mapping
        intent_agent_map = {
            QueryIntent.PRICING_ANALYSIS: [AgentType.PRICING],
            QueryIntent.SENTIMENT_ANALYSIS: [AgentType.SENTIMENT],
            QueryIntent.DEMAND_FORECAST: [AgentType.DEMAND_FORECAST],
            QueryIntent.COMPETITIVE_INTELLIGENCE: [AgentType.PRICING],
            QueryIntent.INVENTORY_OPTIMIZATION: [AgentType.DEMAND_FORECAST],
            QueryIntent.PRODUCT_PERFORMANCE: [AgentType.SENTIMENT],  # Changed: only sentiment for product performance
            QueryIntent.MULTI_AGENT: [
                AgentType.PRICING,
                AgentType.SENTIMENT,
                AgentType.DEMAND_FORECAST
            ],
        }
        
        agents = intent_agent_map.get(intent, [AgentType.SENTIMENT])  # Default to sentiment only
        
        # Check if parameters specify specific agents
        if "agents" in parameters:
            requested_agents = parameters["agents"]
            agents = [
                AgentType(agent) for agent in requested_agents
                if agent in [a.value for a in AgentType]
            ]
        
        logger.info(f"Selected agents for intent {intent}: {agents}")
        return agents
    
    def generate_execution_plan(
            self,
            query_id: str,
            query: str,
            intent: QueryIntent,
            parameters: Dict[str, Any],
            execution_mode: ExecutionMode = ExecutionMode.QUICK
        ) -> SchemaExecutionPlan:
            """
            Generate execution plan for query processing.

            Args:
                query_id: Unique query identifier
                query: Original user query
                intent: Identified query intent
                parameters: Extracted parameters
                execution_mode: Quick or Deep mode

            Returns:
                ExecutionPlan (schema version) with agents and parameters
            """
            # Select agents
            agents = self.select_agents(intent, parameters)

            # Extract product IDs
            product_ids = self._extract_product_ids(parameters)

            # Determine if parallel execution is possible
            parallel_execution = len(agents) > 1 and not self._has_dependencies(agents)

            # Estimate duration
            estimated_duration_seconds = self._estimate_duration(
                agents,
                execution_mode,
                parallel_execution
            )

            # Create AgentTask objects for each agent
            tasks = [
                AgentTask(
                    agent_type=agent,
                    parameters=parameters,
                    dependencies=[],
                    timeout_seconds=120 if execution_mode == ExecutionMode.QUICK else 300
                )
                for agent in agents
            ]

            # Create parallel_groups
            if parallel_execution and len(agents) > 1:
                parallel_groups = [agents]  # All agents execute in parallel
            else:
                parallel_groups = [[agent] for agent in agents]  # Sequential execution

            # Build schema ExecutionPlan
            plan = SchemaExecutionPlan(
                tasks=tasks,
                execution_mode=execution_mode,
                parallel_groups=parallel_groups,
                estimated_duration=timedelta(seconds=estimated_duration_seconds)
            )

            logger.info(f"Generated execution plan: mode={execution_mode.value}, agents={[a.value for a in agents]}, parallel={parallel_execution}")
            return plan


    
    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get current token usage statistics.
        
        Returns:
            Token usage dictionary with counts and estimated cost
        """
        return self.token_usage.to_dict()
    
    def reset_token_usage(self):
        """Reset token usage tracking"""
        self.token_usage = TokenUsage()
    
    def generate_summary(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate summary using LLM (public API).
        
        Args:
            content: Content to summarize
            system_prompt: Optional custom system prompt
            max_tokens: Optional max tokens override
            
        Returns:
            Generated summary text
        """
        if not system_prompt:
            system_prompt = "You are a business intelligence analyst. Generate a concise, actionable summary."
        
        try:
            response = self._call_llm(system_prompt, content)
            return response
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
    
    # Private helper methods
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        import hashlib
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def _get_query_understanding_prompt(self) -> str:
        """Get system prompt for query understanding"""
        return """You are an intelligent query analyzer for an e-commerce intelligence system.

Your task is to understand user queries and extract:
1. Intent: What the user wants to know
2. Parameters: Specific details like product IDs, time ranges, etc.

Available intents:
- pricing_analysis: Questions about pricing, competitors, price gaps
- sentiment_analysis: Questions about customer reviews, satisfaction, feedback
- demand_forecast: Questions about future demand, inventory, sales predictions
- competitive_intelligence: Questions about competitor strategies
- inventory_optimization: Questions about stock levels, reorder points
- product_performance: Comprehensive product analysis
- multi_agent: Complex queries requiring multiple analyses
- unknown: Cannot determine intent

Respond in JSON format:
{
  "intent": "intent_name",
  "parameters": {
    "product_ids": ["uuid1", "uuid2"],
    "time_range": "30_days",
    "include_competitors": true,
    ...
  },
  "confidence": 0.95
}"""
    
    def _build_user_prompt(
        self,
        query: str,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build user prompt with query and context"""
        prompt = f"User query: {query}\n\n"
        
        if conversation_context:
            prompt += "Conversation context:\n"
            for msg in conversation_context[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role}: {content}\n"
            prompt += "\n"
        
        prompt += "Analyze this query and respond in JSON format."
        return prompt
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM API and track token usage"""
        if settings.llm_provider == "openai":
            return self._call_openai(system_prompt, user_prompt)
        elif settings.llm_provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature
            )
            
            # Track token usage
            usage = response.usage
            self.token_usage.add_usage(
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            # Combine prompts for Gemini
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.client.generate_content(combined_prompt)
            
            # Gemini doesn't provide token counts in the same way
            # Estimate based on text length
            estimated_tokens = len(combined_prompt.split()) + len(response.text.split())
            self.token_usage.add_usage(
                estimated_tokens // 2,
                estimated_tokens // 2
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _parse_query_understanding_response(
        self,
        response: str
    ) -> Tuple[QueryIntent, Dict[str, Any]]:
        """Parse LLM response for query understanding"""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response.strip())
            
            # Extract intent
            intent_str = data.get("intent", "unknown")
            try:
                intent = QueryIntent(intent_str)
            except ValueError:
                intent = QueryIntent.UNKNOWN
            
            # Extract parameters
            parameters = data.get("parameters", {})
            
            return intent, parameters
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._fallback_query_understanding(response)
        except Exception as e:
            logger.error(f"Error parsing query understanding response: {e}")
            return QueryIntent.UNKNOWN, {}
    
    def _fallback_query_understanding(
        self,
        query: str
    ) -> Tuple[QueryIntent, Dict[str, Any]]:
        """Fallback keyword-based query understanding"""
        query_lower = query.lower()
        
        # Keyword-based intent detection
        if any(word in query_lower for word in ["price", "pricing", "cost", "competitor"]):
            return QueryIntent.PRICING_ANALYSIS, {}
        elif any(word in query_lower for word in ["review", "sentiment", "feedback", "customer"]):
            return QueryIntent.SENTIMENT_ANALYSIS, {}
        elif any(word in query_lower for word in ["forecast", "demand", "inventory", "stock"]):
            return QueryIntent.DEMAND_FORECAST, {}
        elif any(word in query_lower for word in ["performance", "analysis", "comprehensive"]):
            return QueryIntent.PRODUCT_PERFORMANCE, {}
        else:
            return QueryIntent.UNKNOWN, {}
    
    def _extract_product_ids(self, parameters: Dict[str, Any]) -> List[UUID]:
        """Extract product IDs from parameters"""
        product_ids = []
        
        if "product_ids" in parameters:
            for pid in parameters["product_ids"]:
                try:
                    product_ids.append(UUID(pid))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid product ID: {pid}")
        
        return product_ids
    
    def _has_dependencies(self, agents: List[AgentType]) -> bool:
        """Check if agents have dependencies (for now, assume no dependencies)"""
        # In a more complex system, some agents might depend on others
        # For now, all agents can run in parallel
        return False
    
    def _estimate_duration(
        self,
        agents: List[AgentType],
        execution_mode: ExecutionMode,
        parallel_execution: bool
    ) -> int:
        """Estimate execution duration in seconds"""
        # Base durations per agent (seconds)
        agent_durations = {
            AgentType.PRICING: 15,
            AgentType.SENTIMENT: 20,
            AgentType.DEMAND_FORECAST: 30
        }
        
        if execution_mode == ExecutionMode.QUICK:
            # Quick mode is faster (uses cache)
            total_duration = sum(agent_durations.get(agent, 10) for agent in agents)
            if parallel_execution:
                total_duration = max(agent_durations.get(agent, 10) for agent in agents)
            return min(total_duration, 120)  # Cap at 2 minutes
        else:
            # Deep mode takes longer
            total_duration = sum(agent_durations.get(agent, 10) * 2 for agent in agents)
            if parallel_execution:
                total_duration = max(agent_durations.get(agent, 10) * 2 for agent in agents)
            return min(total_duration, 600)  # Cap at 10 minutes
