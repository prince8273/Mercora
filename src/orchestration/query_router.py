"""
Query Router - Deterministic Query Routing

This component provides deterministic pattern-based routing for common queries.
It determines execution mode (Quick vs Deep) and checks cache before routing.

Features:
- Pattern matching for common query types
- Execution mode determination (Quick: 2-min SLA, Deep: 10-min SLA)
- Cache checking before routing to LLM
- Fallback to LLM reasoning for complex queries
"""
import logging
import re
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID
from datetime import timedelta
from enum import Enum

from src.orchestration.llm_reasoning_engine import (
    LLMReasoningEngine,
    QueryIntent,
)
from src.schemas.orchestration import (
    ExecutionMode,
    AgentType,
    QueryPattern,
    RoutingDecision,
    ConversationContext,
    CachedResult
)
from src.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class InternalQueryPattern:
    """Internal query pattern for deterministic routing"""
    
    def __init__(
        self,
        name: str,
        patterns: List[str],
        agents: List[AgentType],
        execution_mode: ExecutionMode,
        priority: int = 0
    ):
        self.name = name
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.agents = agents
        self.execution_mode = execution_mode
        self.priority = priority
    
    def matches(self, query: str) -> Tuple[bool, List[str]]:
        """Check if query matches any pattern and return matched keywords"""
        matched_keywords = []
        for pattern in self.patterns:
            match = pattern.search(query)
            if match:
                # Extract key words from the matched phrase
                matched_text = match.group(0)
                # Extract meaningful keywords (words with 4+ chars)
                words = [w for w in matched_text.split() if len(w) >= 4]
                matched_keywords.extend(words)
        
        # Remove duplicates while preserving order
        seen = set()
        matched_keywords = [x for x in matched_keywords if not (x in seen or seen.add(x))]
        
        return len(matched_keywords) > 0, matched_keywords


class QueryRouter:
    """
    Deterministic query router with pattern matching and cache checking.
    
    Routes queries based on:
    1. Pattern matching for common queries (deterministic)
    2. Cache availability (Quick Mode optimization)
    3. LLM reasoning for complex queries (fallback)
    
    Execution Modes:
    - Quick Mode: 2-minute SLA, uses cache, single agent
    - Deep Mode: 10-minute SLA, full analysis, multi-agent
    """
    
    def __init__(self, tenant_id: UUID, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Query Router
        
        Args:
            tenant_id: Tenant UUID for multi-tenancy isolation
            cache_manager: Optional cache manager for result caching
        """
        self.tenant_id = tenant_id
        self.cache_manager = cache_manager
        self.llm_engine = LLMReasoningEngine(tenant_id)
        self.patterns = self._load_patterns()
        
        logger.info(f"QueryRouter initialized for tenant {tenant_id}")
    
    def _load_patterns(self) -> List[InternalQueryPattern]:
        """Load predefined query patterns"""
        patterns = [
            # Pricing queries - Quick Mode
            InternalQueryPattern(
                name="pricing_analysis",
                patterns=[
                    r"what.*price",
                    r"show.*price",
                    r"get.*price",
                    r"price.*for",
                    r"how much.*cost",
                    r"pricing.*information",
                    r"competitor.*price",
                    r"price.*gap",
                    r"price.*comparison",
                    r"competitive.*pricing",
                    r"market.*price"
                ],
                agents=[AgentType.PRICING],
                execution_mode=ExecutionMode.QUICK,
                priority=10
            ),
            
            # Sentiment queries - Quick Mode
            InternalQueryPattern(
                name="sentiment_analysis",
                patterns=[
                    r"customer.*review",
                    r"what.*customer.*think",
                    r"sentiment.*analysis",
                    r"review.*summary",
                    r"feedback.*from",
                    r"complaint.*pattern",
                    r"feature.*request",
                    r"aspect.*sentiment",
                    r"topic.*cluster",
                    r"detailed.*sentiment"
                ],
                agents=[AgentType.SENTIMENT],
                execution_mode=ExecutionMode.QUICK,
                priority=10
            ),
            
            # Forecast queries - Quick Mode
            InternalQueryPattern(
                name="demand_forecast",
                patterns=[
                    r"predict.*demand",
                    r"forecast.*sales",
                    r"forecast.*demand",
                    r"future.*demand",
                    r"expected.*sales",
                    r"demand.*forecast",
                    r"seasonal.*pattern",
                    r"demand.*supply.*gap",
                    r"inventory.*risk",
                    r"long.*term.*forecast",
                    r"detailed.*forecast",
                    r"next.*\d+.*day",
                    r"next.*month",
                    r"next.*quarter"
                ],
                agents=[AgentType.DEMAND_FORECAST],
                execution_mode=ExecutionMode.QUICK,
                priority=10
            ),
            
            # Multi-agent queries - Always Deep Mode
            InternalQueryPattern(
                name="product_performance",
                patterns=[
                    r"product.*performance",
                    r"comprehensive.*analysis",
                    r"full.*analysis",
                    r"complete.*report",
                    r"overall.*performance",
                    r"analyze.*everything",
                    r"pricing.*reviews.*demand",
                    r"pricing.*sentiment.*forecast"
                ],
                agents=[AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST],
                execution_mode=ExecutionMode.DEEP,
                priority=30
            ),
        ]
        
        # Sort by priority (higher priority first)
        patterns.sort(key=lambda p: p.priority, reverse=True)
        
        logger.info(f"Loaded {len(patterns)} query patterns")
        return patterns
    
    def match_patterns(self, query: str) -> List[QueryPattern]:
        """
        Match query against predefined patterns.
        
        Args:
            query: User's natural language query (should be lowercased)
            
        Returns:
            List of matched QueryPattern objects with confidence scores
        """
        matched = []
        
        for pattern in self.patterns:
            is_match, keywords = pattern.matches(query)
            if is_match:
                # Calculate confidence based on number of keyword matches
                confidence = min(1.0, len(keywords) * 0.3)
                
                matched.append(QueryPattern(
                    pattern_name=pattern.name,
                    confidence=confidence,
                    matched_keywords=keywords,
                    suggested_agents=pattern.agents
                ))
        
        return matched
    
    def determine_execution_mode(
        self,
        query: str,
        patterns: List[QueryPattern]
    ) -> ExecutionMode:
        """
        Determine execution mode based on query and matched patterns.
        
        Args:
            query: User's natural language query (should be lowercased)
            patterns: List of matched patterns
            
        Returns:
            ExecutionMode (QUICK or DEEP)
        """
        # Check for deep mode keywords
        deep_keywords = [
            'comprehensive', 'detailed', 'full', 'complete', 'analyze everything',
            'all products', 'in-depth'
        ]
        
        if any(keyword in query for keyword in deep_keywords):
            return ExecutionMode.DEEP
        
        # Check if multiple agents are required
        if patterns:
            all_agents = set()
            for pattern in patterns:
                all_agents.update(pattern.suggested_agents)
            
            if len(all_agents) >= 2:
                return ExecutionMode.DEEP
        
        # Default to quick mode
        return ExecutionMode.QUICK
    
    def route_query(
        self,
        query: str,
        context: Optional[ConversationContext] = None
    ) -> RoutingDecision:
        """
        Route query to appropriate execution path.
        
        Args:
            query: User's natural language query
            context: Optional conversation context
            
        Returns:
            RoutingDecision with routing decisions
        """
        logger.info(f"Routing query: '{query}'")
        
        # Normalize query
        query_lower = query.lower()
        
        # Step 1: Pattern matching
        patterns = self.match_patterns(query_lower)
        
        # Step 2: Determine execution mode
        execution_mode = self.determine_execution_mode(query_lower, patterns)
        
        # Step 3: Collect required agents
        required_agents = []
        if patterns:
            for pattern in patterns:
                required_agents.extend(pattern.suggested_agents)
            # Remove duplicates while preserving order
            seen = set()
            required_agents = [x for x in required_agents if not (x in seen or seen.add(x))]
        else:
            # Fallback: use all agents for unknown queries
            required_agents = [AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST]
            execution_mode = ExecutionMode.DEEP
        
        # Step 4: Generate cache key
        cache_key = self._generate_cache_key(query, required_agents)
        
        # Step 5: Cache will be checked at execution time (not here, since this is sync)
        use_cache = self.cache_manager is not None
        
        # Step 6: Estimate duration
        estimated_duration = self._estimate_duration(execution_mode, len(required_agents))
        
        decision = RoutingDecision(
            execution_mode=execution_mode,
            required_agents=required_agents,
            use_cache=use_cache,
            cache_key=cache_key,
            estimated_duration=estimated_duration
        )
        
        logger.info(f"Routing decision: mode={execution_mode.value}, agents={[a.value for a in required_agents]}, cache={use_cache}")
        
        return decision
    
    def _generate_cache_key(self, query: str, agents: List[AgentType]) -> str:
        """
        Generate cache key from query and agents.
        
        Args:
            query: User's natural language query
            agents: List of required agents
            
        Returns:
            Cache key string
        """
        # Normalize query
        normalized = query.lower().strip()
        
        # Sort agents for consistent key generation
        agent_str = ",".join(sorted([a.value for a in agents]))
        
        # Generate hash
        key_input = f"{self.tenant_id}:{normalized}:{agent_str}"
        cache_key = hashlib.sha256(key_input.encode()).hexdigest()
        
        return cache_key
    
    def check_cache(self, cache_key: str) -> Optional[CachedResult]:
        """
        Check cache for query results.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            CachedResult if found, None otherwise
        """
        if not self.cache_manager:
            return None
        
        try:
            cached_result = self.cache_manager.get(cache_key)
            return cached_result
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None
    
    def _estimate_duration(
        self,
        execution_mode: ExecutionMode,
        num_agents: int
    ) -> timedelta:
        """
        Estimate execution duration based on mode and number of agents.
        
        Args:
            execution_mode: Execution mode (QUICK or DEEP)
            num_agents: Number of agents to execute
            
        Returns:
            Estimated duration as timedelta
        """
        if execution_mode == ExecutionMode.QUICK:
            # Quick mode: 30-60 seconds per agent
            base_seconds = 30
            per_agent_seconds = 15
        else:
            # Deep mode: 2-5 minutes per agent
            base_seconds = 120
            per_agent_seconds = 60
        
        total_seconds = base_seconds + (per_agent_seconds * (num_agents - 1))
        
        return timedelta(seconds=total_seconds)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "tenant_id": str(self.tenant_id),
            "patterns_loaded": len(self.patterns),
            "cache_enabled": self.cache_manager is not None
        }
