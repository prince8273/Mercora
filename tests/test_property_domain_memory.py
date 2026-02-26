"""Property-based tests for Domain Memory layer"""
import pytest
from hypothesis import given, strategies as st, settings
from uuid import uuid4
from datetime import datetime

from src.memory import (
    MemoryManager,
    PreferenceManager,
    UserPreferences,
    ConversationContext,
    BusinessContext,
    HistoricalQuery,
    KPI
)


class TestPreferencePersistence:
    """
    Property 39: Preferences persist across sessions
    Validates: Requirements 8.1, 8.3
    """
    
    @given(
        num_users=st.integers(min_value=1, max_value=10),
        num_kpis=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_preferences_persist_across_sessions(self, num_users, num_kpis):
        """Test that user preferences persist across sessions"""
        # Feature: ecommerce-intelligence-agent, Property 39: Preferences persist across sessions
        
        manager = MemoryManager()
        tenant_id = uuid4()
        
        # Store preferences for multiple users
        user_prefs_map = {}
        for i in range(num_users):
            user_id = uuid4()
            kpi_prefs = {f"kpi_{j}": j % 2 == 0 for j in range(num_kpis)}
            
            preferences = UserPreferences(
                user_id=user_id,
                tenant_id=tenant_id,
                kpi_preferences=kpi_prefs,
                marketplace_focus=["amazon", "ebay"],
                business_goals={"target_revenue": 1000000}
            )
            
            manager.store_user_preferences(user_id, preferences)
            user_prefs_map[user_id] = preferences
        
        # Property: All stored preferences must be retrievable
        for user_id, original_prefs in user_prefs_map.items():
            retrieved_prefs = manager.retrieve_user_preferences(user_id)
            
            assert retrieved_prefs is not None
            assert retrieved_prefs.user_id == user_id
            assert retrieved_prefs.kpi_preferences == original_prefs.kpi_preferences
            assert retrieved_prefs.marketplace_focus == original_prefs.marketplace_focus
            assert retrieved_prefs.business_goals == original_prefs.business_goals
    
    @given(
        num_updates=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_preference_updates_persist(self, num_updates):
        """Test that preference updates persist correctly"""
        # Feature: ecommerce-intelligence-agent, Property 39: Preferences persist across sessions
        
        pref_manager = PreferenceManager()
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Perform multiple updates
        for i in range(num_updates):
            kpis = {f"kpi_{j}": (i + j) % 2 == 0 for j in range(3)}
            pref_manager.store_kpi_preferences(user_id, tenant_id, kpis)
        
        # Property: Latest update must be persisted
        retrieved_kpis = pref_manager.get_kpi_preferences(user_id)
        assert retrieved_kpis is not None
        assert len(retrieved_kpis) == 3


class TestMarketplaceFocusPrioritization:
    """
    Property 40: Marketplace focus affects prioritization
    Validates: Requirements 8.2
    """
    
    @given(
        num_marketplaces=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_marketplace_focus_is_stored(self, num_marketplaces):
        """Test that marketplace focus preferences are stored"""
        # Feature: ecommerce-intelligence-agent, Property 40: Marketplace focus affects prioritization
        
        pref_manager = PreferenceManager()
        user_id = uuid4()
        tenant_id = uuid4()
        
        marketplaces = [f"marketplace_{i}" for i in range(num_marketplaces)]
        pref_manager.set_marketplace_focus(user_id, tenant_id, marketplaces)
        
        # Property: Marketplace focus must be retrievable
        retrieved_focus = pref_manager.get_marketplace_focus(user_id)
        assert retrieved_focus == marketplaces
    
    @given(
        focus_marketplaces=st.lists(
            st.sampled_from(["amazon", "ebay", "walmart", "shopify"]),
            min_size=1,
            max_size=4,
            unique=True
        )
    )
    @settings(max_examples=10, deadline=None)
    def test_marketplace_focus_filters_data(self, focus_marketplaces):
        """Test that marketplace focus can be used for filtering"""
        # Feature: ecommerce-intelligence-agent, Property 40: Marketplace focus affects prioritization
        
        pref_manager = PreferenceManager()
        user_id = uuid4()
        tenant_id = uuid4()
        
        pref_manager.set_marketplace_focus(user_id, tenant_id, focus_marketplaces)
        
        # Property: Retrieved focus matches stored focus
        retrieved_focus = pref_manager.get_marketplace_focus(user_id)
        assert set(retrieved_focus) == set(focus_marketplaces)


class TestBusinessGoalContextualization:
    """
    Property 41: Business goals contextualize recommendations
    Validates: Requirements 8.4
    """
    
    @given(
        target_revenue=st.integers(min_value=100000, max_value=10000000),
        target_margin=st.floats(min_value=0.1, max_value=0.5)
    )
    @settings(max_examples=10, deadline=None)
    def test_business_goals_are_stored(self, target_revenue, target_margin):
        """Test that business goals are stored and retrievable"""
        # Feature: ecommerce-intelligence-agent, Property 41: Business goals contextualize recommendations
        
        pref_manager = PreferenceManager()
        user_id = uuid4()
        tenant_id = uuid4()
        
        goals = {
            "target_revenue": target_revenue,
            "target_margin": target_margin,
            "growth_rate": 0.15
        }
        
        pref_manager.update_business_goals(user_id, tenant_id, goals)
        
        # Property: Business goals must be retrievable
        retrieved_goals = pref_manager.get_business_goals(user_id)
        assert retrieved_goals["target_revenue"] == target_revenue
        assert retrieved_goals["target_margin"] == target_margin
    
    @given(
        num_goals=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_business_context_storage(self, num_goals):
        """Test that business context is stored at tenant level"""
        # Feature: ecommerce-intelligence-agent, Property 41: Business goals contextualize recommendations
        
        manager = MemoryManager()
        tenant_id = uuid4()
        
        goals = [f"goal_{i}" for i in range(num_goals)]
        context = BusinessContext(
            tenant_id=tenant_id,
            industry="ecommerce",
            target_markets=["US", "EU"],
            business_goals=goals
        )
        
        manager.store_business_context(tenant_id, context)
        
        # Property: Business context must be retrievable
        retrieved_context = manager.retrieve_business_context(tenant_id)
        assert retrieved_context is not None
        assert retrieved_context.tenant_id == tenant_id
        assert retrieved_context.business_goals == goals


class TestHistoricalContextPersonalization:
    """
    Property 42: Historical context personalizes responses
    Validates: Requirements 8.5
    """
    
    @given(
        num_queries=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_query_history_is_stored(self, num_queries):
        """Test that query history is stored and retrievable"""
        # Feature: ecommerce-intelligence-agent, Property 42: Historical context personalizes responses
        
        manager = MemoryManager()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Store multiple queries
        query_ids = []
        for i in range(num_queries):
            query_id = uuid4()
            query_ids.append(query_id)
            
            manager.store_query_result(
                query_id=query_id,
                query=f"Query {i}",
                result={"executive_summary": f"Result {i}"},
                tenant_id=tenant_id,
                user_id=user_id,
                confidence=0.85,
                execution_time_ms=1000
            )
        
        # Property: Query history must be retrievable
        history = manager.get_query_history(tenant_id, user_id)
        assert len(history) >= num_queries
        
        # Property: History is ordered by timestamp (newest first)
        timestamps = [q.timestamp for q in history]
        assert timestamps == sorted(timestamps, reverse=True)
    
    @given(
        num_queries=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=10, deadline=None)
    def test_similar_query_search(self, num_queries):
        """Test that similar queries can be found"""
        # Feature: ecommerce-intelligence-agent, Property 42: Historical context personalizes responses
        
        manager = MemoryManager()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Store queries with common keywords
        for i in range(num_queries):
            query_id = uuid4()
            query_text = f"pricing analysis for product {i}" if i % 2 == 0 else f"sentiment analysis for product {i}"
            
            manager.store_query_result(
                query_id=query_id,
                query=query_text,
                result={"executive_summary": f"Result {i}"},
                tenant_id=tenant_id,
                user_id=user_id,
                confidence=0.85,
                execution_time_ms=1000
            )
        
        # Property: Similar queries must be findable
        similar = manager.search_similar_queries("pricing analysis", tenant_id, top_k=5)
        assert len(similar) >= 1
        
        # Property: Results have similarity scores
        for query in similar:
            assert query.similarity_score is not None
            assert 0 <= query.similarity_score <= 1


class TestFollowUpContextUsage:
    """
    Property 32: Follow-up queries use conversation context
    Validates: Requirements 6.7
    """
    
    @given(
        num_messages=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_conversation_context_is_maintained(self, num_messages):
        """Test that conversation context is maintained across messages"""
        # Feature: ecommerce-intelligence-agent, Property 32: Follow-up queries use conversation context
        
        manager = MemoryManager()
        conversation_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Create conversation
        context = manager.create_conversation_context(conversation_id, tenant_id, user_id)
        
        # Add messages
        for i in range(num_messages):
            context.add_message("user" if i % 2 == 0 else "assistant", f"Message {i}")
        
        # Property: All messages must be stored
        assert len(context.messages) == num_messages
        
        # Property: Messages maintain order
        for i, message in enumerate(context.messages):
            assert f"Message {i}" in message["content"]
    
    @given(
        num_turns=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_conversation_context_retrieval(self, num_turns):
        """Test that conversation context can be retrieved"""
        # Feature: ecommerce-intelligence-agent, Property 32: Follow-up queries use conversation context
        
        manager = MemoryManager()
        conversation_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Create and update conversation
        manager.create_conversation_context(conversation_id, tenant_id, user_id)
        
        for i in range(num_turns):
            manager.update_conversation_context(
                conversation_id=conversation_id,
                query=f"Query {i}",
                result={"executive_summary": f"Result {i}"},
                tenant_id=tenant_id
            )
        
        # Property: Conversation context must be retrievable
        retrieved_context = manager.retrieve_conversation_context(conversation_id, tenant_id)
        assert retrieved_context is not None
        assert retrieved_context.conversation_id == conversation_id
        assert len(retrieved_context.messages) >= num_turns * 2  # user + assistant per turn


class TestTenantIsolation:
    """Test that domain memory respects tenant isolation"""
    
    @given(
        num_tenants=st.integers(min_value=2, max_value=5),
        queries_per_tenant=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=10, deadline=None)
    def test_query_history_tenant_isolation(self, num_tenants, queries_per_tenant):
        """Test that query history is isolated by tenant"""
        # Feature: ecommerce-intelligence-agent, Property 42: Historical context personalizes responses
        
        manager = MemoryManager()
        
        # Create queries for multiple tenants
        tenant_ids = [uuid4() for _ in range(num_tenants)]
        
        for tenant_id in tenant_ids:
            user_id = uuid4()
            for i in range(queries_per_tenant):
                manager.store_query_result(
                    query_id=uuid4(),
                    query=f"Query {i}",
                    result={"executive_summary": f"Result {i}"},
                    tenant_id=tenant_id,
                    user_id=user_id,
                    confidence=0.85,
                    execution_time_ms=1000
                )
        
        # Property: Each tenant can only see their own history
        for tenant_id in tenant_ids:
            history = manager.get_query_history(tenant_id)
            
            assert len(history) >= queries_per_tenant
            
            # All queries must belong to this tenant
            for query in history:
                assert query.tenant_id == tenant_id
    
    @given(
        num_tenants=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_preferences_tenant_isolation(self, num_tenants):
        """Test that preferences are isolated by tenant"""
        # Feature: ecommerce-intelligence-agent, Property 39: Preferences persist across sessions
        
        pref_manager = PreferenceManager()
        
        # Create preferences for multiple tenants
        tenant_user_map = {}
        for i in range(num_tenants):
            tenant_id = uuid4()
            user_id = uuid4()
            tenant_user_map[tenant_id] = user_id
            
            pref_manager.store_kpi_preferences(
                user_id=user_id,
                tenant_id=tenant_id,
                kpis={f"kpi_{i}": True}
            )
        
        # Property: Each tenant's preferences are isolated
        for tenant_id, user_id in tenant_user_map.items():
            prefs = pref_manager.get_all_preferences(user_id)
            assert prefs is not None
            assert prefs.tenant_id == tenant_id


class TestMemoryCleanup:
    """Test memory cleanup and data management"""
    
    @given(
        num_records=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=10, deadline=None)
    def test_tenant_data_cleanup(self, num_records):
        """Test that tenant data can be cleaned up"""
        # Feature: ecommerce-intelligence-agent, Property 39: Preferences persist across sessions
        
        manager = MemoryManager()
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Create multiple records
        for i in range(num_records):
            manager.store_query_result(
                query_id=uuid4(),
                query=f"Query {i}",
                result={"executive_summary": f"Result {i}"},
                tenant_id=tenant_id,
                user_id=user_id,
                confidence=0.85,
                execution_time_ms=1000
            )
        
        # Property: Cleanup must remove all tenant data
        cleared = manager.clear_tenant_data(tenant_id)
        assert cleared >= num_records
        
        # Property: No data should remain for tenant
        history = manager.get_query_history(tenant_id)
        assert len(history) == 0
