"""
Prompt Optimization Module

This module provides:
1. Optimized prompt templates for common query patterns
2. Prompt caching for frequently used prompts
3. Context compression for long conversations
4. Token usage minimization strategies
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Optimized prompt template"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        user_prompt_template: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def format(self, **kwargs) -> str:
        """Format user prompt with parameters"""
        return self.user_prompt_template.format(**kwargs)


class PromptCache:
    """
    Cache for prompt responses to minimize token usage.
    
    Caches LLM responses for identical prompts to avoid redundant API calls.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize prompt cache
        
        Args:
            ttl_seconds: Time-to-live for cached entries (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, prompt: str) -> Optional[str]:
        """
        Get cached response for prompt
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_key(prompt)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if expired
            if datetime.utcnow() - entry["timestamp"] < timedelta(seconds=self.ttl_seconds):
                logger.info(f"Cache hit for prompt (key: {cache_key[:8]}...)")
                return entry["response"]
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
                logger.info(f"Cache expired for prompt (key: {cache_key[:8]}...)")
        
        return None
    
    def set(self, prompt: str, response: str):
        """
        Cache response for prompt
        
        Args:
            prompt: The prompt
            response: The LLM response to cache
        """
        cache_key = self._generate_key(prompt)
        
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Cached response for prompt (key: {cache_key[:8]}...)")
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        logger.info("Prompt cache cleared")
    
    def _generate_key(self, prompt: str) -> str:
        """Generate cache key from prompt"""
        return hashlib.sha256(prompt.encode()).hexdigest()


class ContextCompressor:
    """
    Compress conversation context to minimize token usage.
    
    Strategies:
    1. Keep only recent messages
    2. Summarize older messages
    3. Remove redundant information
    """
    
    def __init__(self, max_messages: int = 5, max_tokens_per_message: int = 200):
        """
        Initialize context compressor
        
        Args:
            max_messages: Maximum number of messages to keep
            max_tokens_per_message: Maximum tokens per message
        """
        self.max_messages = max_messages
        self.max_tokens_per_message = max_tokens_per_message
    
    def compress(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Compress conversation history
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Compressed conversation history
        """
        if not conversation_history:
            return []
        
        # Keep only recent messages
        recent_messages = conversation_history[-self.max_messages:]
        
        # Truncate long messages
        compressed = []
        for msg in recent_messages:
            content = msg.get("content", "")
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            estimated_tokens = len(content) // 4
            
            if estimated_tokens > self.max_tokens_per_message:
                # Truncate and add ellipsis
                max_chars = self.max_tokens_per_message * 4
                content = content[:max_chars] + "..."
            
            compressed.append({
                "role": msg.get("role", "user"),
                "content": content
            })
        
        logger.info(f"Compressed conversation from {len(conversation_history)} to {len(compressed)} messages")
        return compressed
    
    def summarize_context(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Create a summary of conversation context
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Summary string
        """
        if not conversation_history:
            return ""
        
        # Extract key information
        topics = set()
        products_mentioned = set()
        
        for msg in conversation_history:
            content = msg.get("content", "").lower()
            
            # Extract topics
            if "price" in content or "pricing" in content:
                topics.add("pricing")
            if "review" in content or "sentiment" in content:
                topics.add("sentiment")
            if "forecast" in content or "demand" in content:
                topics.add("forecast")
            
            # Extract product mentions (simplified)
            # In production, use NER or regex patterns
            if "product" in content:
                products_mentioned.add("products")
        
        summary_parts = []
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(topics)}")
        if products_mentioned:
            summary_parts.append(f"Context: {', '.join(products_mentioned)}")
        
        summary = ". ".join(summary_parts) if summary_parts else "No prior context"
        
        logger.info(f"Generated context summary: {summary}")
        return summary


class PromptOptimizer:
    """
    Main prompt optimization class combining templates, caching, and compression.
    """
    
    def __init__(self):
        """Initialize prompt optimizer"""
        self.templates = self._load_templates()
        self.cache = PromptCache()
        self.compressor = ContextCompressor()
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """Load optimized prompt templates"""
        templates = {}
        
        # Query Understanding Template
        templates["query_understanding"] = PromptTemplate(
            name="query_understanding",
            system_prompt="""You are a query analyzer for an e-commerce intelligence system.
Analyze queries and respond in JSON format with intent and parameters.

Available intents: pricing_analysis, sentiment_analysis, demand_forecast, 
competitive_intelligence, inventory_optimization, product_performance, multi_agent, unknown.

Be concise and accurate.""",
            user_prompt_template="Query: {query}\n\nRespond in JSON: {{\"intent\": \"...\", \"parameters\": {{...}}, \"confidence\": 0.0-1.0}}",
            max_tokens=500,
            temperature=0.3
        )
        
        # Agent Selection Template
        templates["agent_selection"] = PromptTemplate(
            name="agent_selection",
            system_prompt="""Select which agents (pricing, sentiment, forecast) are needed for this query.
Respond with JSON array of agent names.

Be minimal - only select agents that are truly needed.""",
            user_prompt_template="Query: {query}\nIntent: {intent}\n\nRespond: {{\"agents\": [...]}}",
            max_tokens=200,
            temperature=0.2
        )
        
        # Result Synthesis Template
        templates["result_synthesis"] = PromptTemplate(
            name="result_synthesis",
            system_prompt="""Synthesize results from multiple agents into a coherent executive summary.
Focus on key insights, actionable recommendations, and confidence levels.

Be concise and business-focused.""",
            user_prompt_template="Agent Results:\n{results}\n\nGenerate executive summary with key findings and recommendations.",
            max_tokens=1000,
            temperature=0.5
        )
        
        # Follow-up Query Template
        templates["follow_up"] = PromptTemplate(
            name="follow_up",
            system_prompt="""Analyze follow-up query in context of previous conversation.
Identify if this is a refinement, new question, or clarification.

Use conversation context to understand intent.""",
            user_prompt_template="Previous context: {context}\n\nNew query: {query}\n\nAnalyze intent and parameters.",
            max_tokens=400,
            temperature=0.3
        )
        
        logger.info(f"Loaded {len(templates)} prompt templates")
        return templates
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name
        
        Args:
            template_name: Name of the template
            
        Returns:
            PromptTemplate or None if not found
        """
        return self.templates.get(template_name)
    
    def optimize_prompt(
        self,
        template_name: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> tuple[str, str]:
        """
        Optimize prompt using template and context compression
        
        Args:
            template_name: Name of the template to use
            conversation_history: Optional conversation history
            **kwargs: Template parameters
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Compress conversation context if provided
        if conversation_history:
            compressed_context = self.compressor.compress(conversation_history)
            context_summary = self.compressor.summarize_context(compressed_context)
            kwargs["context"] = context_summary
        
        # Format user prompt
        user_prompt = template.format(**kwargs)
        
        return template.system_prompt, user_prompt
    
    def get_cached_response(self, prompt: str) -> Optional[str]:
        """
        Get cached response for prompt
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Cached response or None
        """
        return self.cache.get(prompt)
    
    def cache_response(self, prompt: str, response: str):
        """
        Cache response for prompt
        
        Args:
            prompt: The prompt
            response: The response to cache
        """
        self.cache.set(prompt, response)
    
    def clear_cache(self):
        """Clear prompt cache"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "cached_entries": len(self.cache.cache),
            "ttl_seconds": self.cache.ttl_seconds
        }


# Global prompt optimizer instance
_prompt_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer() -> PromptOptimizer:
    """Get global prompt optimizer instance"""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer
