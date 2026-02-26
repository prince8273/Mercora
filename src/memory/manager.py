"""
Memory Manager - Centralized service for all memory operations

This module provides the main interface for storing and retrieving
user preferences, conversation context, and historical queries.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from src.memory.models import (
    UserPreferences,
    ConversationContext,
    BusinessContext,
    HistoricalQuery
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Centralized service for all memory operations.
    
    Manages user preferences, conversation history, business context,
    and historical query storage for personalization and context retention.
    """
    
    def __init__(self):
        """Initialize memory manager"""
        # In-memory storage (would be replaced with database in production)
        self._query_results: Dict[UUID, Dict[str, Any]] = {}
        self._conversations: Dict[UUID, ConversationContext] = {}
        self._user_preferences: Dict[UUID, UserPreferences] = {}
        self._business_contexts: Dict[UUID, BusinessContext] = {}
        self._historical_queries: List[HistoricalQuery] = []
        
        logger.info("MemoryManager initialized")
    
    def store_query_result(
        self,
        query_id: UUID,
        query: str,
        result: Dict[str, Any],
        tenant_id: UUID,
        user_id: UUID,
        confidence: float,
        execution_time_ms: int
    ) -> None:
        """
        Store a query result for historical reference.
        
        Args:
            query_id: Unique query identifier
            query: Query text
            result: Query result dictionary
            tenant_id: Tenant UUID
            user_id: User UUID
            confidence: Overall confidence score
            execution_time_ms: Execution time in milliseconds
        """
        # Store full result
        self._query_results[query_id] = {
            "query": query,
            "result": result,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        }
        
        # Store historical query for search
        historical_query = HistoricalQuery(
            query_id=query_id,
            tenant_id=tenant_id,
            user_id=user_id,
            query_text=query,
            result_summary=result.get("executive_summary", ""),
            confidence=confidence,
            execution_time_ms=execution_time_ms
        )
        self._historical_queries.append(historical_query)
        
        logger.info(f"Stored query result for query_id={query_id}")
    
    def retrieve_conversation_context(
        self,
        conversation_id: UUID,
        tenant_id: UUID
    ) -> Optional[ConversationContext]:
        """
        Retrieve conversation context for follow-up queries.
        
        Args:
            conversation_id: Conversation UUID
            tenant_id: Tenant UUID for isolation
            
        Returns:
            ConversationContext if found, None otherwise
        """
        context = self._conversations.get(conversation_id)
        
        if context and context.tenant_id == tenant_id:
            logger.info(f"Retrieved conversation context for conversation_id={conversation_id}")
            return context
        
        logger.warning(f"Conversation context not found for conversation_id={conversation_id}")
        return None
    
    def create_conversation_context(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            conversation_id: Conversation UUID
            tenant_id: Tenant UUID
            user_id: User UUID
            
        Returns:
            New ConversationContext
        """
        context = ConversationContext(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        self._conversations[conversation_id] = context
        
        logger.info(f"Created conversation context for conversation_id={conversation_id}")
        return context
    
    def update_conversation_context(
        self,
        conversation_id: UUID,
        query: str,
        result: Dict[str, Any],
        tenant_id: UUID
    ) -> None:
        """
        Update conversation context with new query and result.
        
        Args:
            conversation_id: Conversation UUID
            query: Query text
            result: Query result
            tenant_id: Tenant UUID for isolation
        """
        context = self._conversations.get(conversation_id)
        
        if context and context.tenant_id == tenant_id:
            context.add_message("user", query)
            context.add_message("assistant", result.get("executive_summary", ""))
            context.last_query = query
            context.last_result = result
            
            logger.info(f"Updated conversation context for conversation_id={conversation_id}")
        else:
            logger.warning(f"Cannot update conversation context for conversation_id={conversation_id}")
    
    def store_user_preferences(
        self,
        user_id: UUID,
        preferences: UserPreferences
    ) -> None:
        """
        Store user preferences for personalization.
        
        Args:
            user_id: User UUID
            preferences: UserPreferences object
        """
        preferences.updated_at = datetime.utcnow()
        self._user_preferences[user_id] = preferences
        
        logger.info(f"Stored user preferences for user_id={user_id}")
    
    def retrieve_user_preferences(
        self,
        user_id: UUID
    ) -> Optional[UserPreferences]:
        """
        Retrieve user preferences.
        
        Args:
            user_id: User UUID
            
        Returns:
            UserPreferences if found, None otherwise
        """
        preferences = self._user_preferences.get(user_id)
        
        if preferences:
            logger.info(f"Retrieved user preferences for user_id={user_id}")
        else:
            logger.info(f"No preferences found for user_id={user_id}")
        
        return preferences
    
    def search_similar_queries(
        self,
        query: str,
        tenant_id: UUID,
        top_k: int = 5
    ) -> List[HistoricalQuery]:
        """
        Search for similar historical queries.
        
        Note: This is a simple keyword-based search. In production,
        this would use vector embeddings and semantic search.
        
        Args:
            query: Query text to search for
            tenant_id: Tenant UUID for isolation
            top_k: Number of results to return
            
        Returns:
            List of similar HistoricalQuery objects
        """
        query_lower = query.lower()
        
        # Filter by tenant and calculate simple similarity
        tenant_queries = [
            q for q in self._historical_queries
            if q.tenant_id == tenant_id
        ]
        
        # Simple keyword matching (would be replaced with vector search)
        scored_queries = []
        for historical_query in tenant_queries:
            # Count matching words
            query_words = set(query_lower.split())
            historical_words = set(historical_query.query_text.lower().split())
            matching_words = query_words.intersection(historical_words)
            
            if matching_words:
                similarity = len(matching_words) / max(len(query_words), len(historical_words))
                historical_query.similarity_score = similarity
                scored_queries.append(historical_query)
        
        # Sort by similarity and return top_k
        scored_queries.sort(key=lambda q: q.similarity_score or 0, reverse=True)
        results = scored_queries[:top_k]
        
        logger.info(f"Found {len(results)} similar queries for tenant_id={tenant_id}")
        return results
    
    def store_business_context(
        self,
        tenant_id: UUID,
        context: BusinessContext
    ) -> None:
        """
        Store business context for tenant.
        
        Args:
            tenant_id: Tenant UUID
            context: BusinessContext object
        """
        context.updated_at = datetime.utcnow()
        self._business_contexts[tenant_id] = context
        
        logger.info(f"Stored business context for tenant_id={tenant_id}")
    
    def retrieve_business_context(
        self,
        tenant_id: UUID
    ) -> Optional[BusinessContext]:
        """
        Retrieve business context for tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            BusinessContext if found, None otherwise
        """
        context = self._business_contexts.get(tenant_id)
        
        if context:
            logger.info(f"Retrieved business context for tenant_id={tenant_id}")
        else:
            logger.info(f"No business context found for tenant_id={tenant_id}")
        
        return context
    
    def get_query_history(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[HistoricalQuery]:
        """
        Get query history for tenant or user.
        
        Args:
            tenant_id: Tenant UUID
            user_id: Optional user UUID filter
            limit: Maximum number of results
            
        Returns:
            List of HistoricalQuery objects (newest first)
        """
        queries = [
            q for q in self._historical_queries
            if q.tenant_id == tenant_id
            and (user_id is None or q.user_id == user_id)
        ]
        
        # Sort by timestamp (newest first)
        queries.sort(key=lambda q: q.timestamp, reverse=True)
        
        return queries[:limit]
    
    def clear_tenant_data(self, tenant_id: UUID) -> int:
        """
        Clear all memory data for a tenant.
        
        Used for tenant cleanup or testing.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of records cleared
        """
        cleared = 0
        
        # Clear query results
        query_ids_to_remove = [
            qid for qid, data in self._query_results.items()
            if data["tenant_id"] == tenant_id
        ]
        for qid in query_ids_to_remove:
            del self._query_results[qid]
            cleared += 1
        
        # Clear conversations
        conv_ids_to_remove = [
            cid for cid, conv in self._conversations.items()
            if conv.tenant_id == tenant_id
        ]
        for cid in conv_ids_to_remove:
            del self._conversations[cid]
            cleared += 1
        
        # Clear historical queries
        original_count = len(self._historical_queries)
        self._historical_queries = [
            q for q in self._historical_queries
            if q.tenant_id != tenant_id
        ]
        cleared += original_count - len(self._historical_queries)
        
        # Clear business context
        if tenant_id in self._business_contexts:
            del self._business_contexts[tenant_id]
            cleared += 1
        
        logger.info(f"Cleared {cleared} memory records for tenant {tenant_id}")
        return cleared
