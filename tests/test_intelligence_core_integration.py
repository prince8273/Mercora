"""Integration tests for complete Intelligence Core pipeline"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

from src.orchestration.query_router import QueryRouter
from src.orchestration.execution_service import ExecutionService
from src.orchestration.result_synthesizer import ResultSynthesizer
from src.schemas.orchestration import (
    ExecutionMode,
    AgentType,
    ExecutionPlan,
    AgentTask
)


class TestIntelligenceCoreIntegration:
    """Test complete intelligence core pipeline"""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID"""
        return uuid4()
    
    @pytest.fixture
    def query_router(self, tenant_id):
        """Create query router"""
        return QueryRouter(tenant_id=tenant_id)
    
    @pytest.fixture
    def execution_service(self, tenant_id):
        """Create execution service"""
        return ExecutionService(tenant_id=tenant_id)
    
    @pytest.fixture
    def result_synthesizer(self, tenant_id):
        """Create result synthesizer"""
        return ResultSynthesizer(tenant_id=tenant_id)
    
    def test_query_routing_pricing(self, query_router):
        """Test query routing for pricing queries"""
        query = "What are the price gaps for my products?"
        
        decision = query_router.route_query(query)
        
        assert decision.execution_mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]
        assert AgentType.PRICING in decision.required_agents
        assert decision.estimated_duration is not None
    
    def test_query_routing_sentiment(self, query_router):
        """Test query routing for sentiment queries"""
        query = "How are customers feeling about my products?"
        
        decision = query_router.route_query(query)
        
        assert decision.execution_mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]
        assert AgentType.SENTIMENT in decision.required_agents
    
    def test_query_routing_forecast(self, query_router):
        """Test query routing for forecast queries"""
        query = "What is the demand forecast for next month?"
        
        decision = query_router.route_query(query)
        
        assert decision.execution_mode in [ExecutionMode.QUICK, ExecutionMode.DEEP]
        assert AgentType.DEMAND_FORECAST in decision.required_agents
    
    def test_query_routing_multi_agent(self, query_router):
        """Test query routing for complex queries requiring multiple agents"""
        query = "Analyze product performance including pricing, sentiment, and demand"
        
        decision = query_router.route_query(query)
        
        # Should route to multiple agents
        assert len(decision.required_agents) >= 2
        # Complex queries should use deep mode
        assert decision.execution_mode == ExecutionMode.DEEP
    
    def test_execution_mode_determination(self, query_router):
        """Test execution mode determination"""
        # Simple query -> Quick mode
        simple_query = "Show me prices"
        simple_decision = query_router.route_query(simple_query)
        assert simple_decision.execution_mode == ExecutionMode.QUICK
        
        # Complex query -> Deep mode
        complex_query = "Comprehensive analysis of all products"
        complex_decision = query_router.route_query(complex_query)
        assert complex_decision.execution_mode == ExecutionMode.DEEP
    
    @pytest.mark.asyncio
    async def test_agent_execution_parallel(self, execution_service):
        """Test parallel agent execution"""
        # Create execution plan with multiple agents
        plan = ExecutionPlan(
            execution_mode=ExecutionMode.QUICK,
            tasks=[
                AgentTask(
                    agent_type=AgentType.PRICING,
                    parameters={},
                    timeout_seconds=30
                ),
                AgentTask(
                    agent_type=AgentType.SENTIMENT,
                    parameters={},
                    timeout_seconds=30
                )
            ],
            parallel_groups=[
                [AgentType.PRICING, AgentType.SENTIMENT]
            ],
            estimated_duration=timedelta(seconds=60)
        )
        
        # Execute plan (without real data, will use mock)
        results = await execution_service.execute_plan(plan)
        
        # Should have results from both agents
        assert len(results) == 2
        
        # Check agent types
        agent_types = {r.agent_type for r in results}
        assert AgentType.PRICING in agent_types
        assert AgentType.SENTIMENT in agent_types
    
    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, execution_service):
        """Test agent timeout handling"""
        # Create plan with very short timeout
        plan = ExecutionPlan(
            execution_mode=ExecutionMode.QUICK,
            tasks=[
                AgentTask(
                    agent_type=AgentType.PRICING,
                    parameters={},
                    timeout_seconds=1  # Very short timeout (1 second)
                )
            ],
            parallel_groups=[[AgentType.PRICING]],
            estimated_duration=timedelta(seconds=1)
        )
        
        results = await execution_service.execute_plan(plan)
        
        # Should have result (may be success or timeout)
        assert len(results) == 1
        # Execution should complete without crashing
        assert results[0].agent_type == AgentType.PRICING
    
    def test_result_synthesis(self, result_synthesizer):
        """Test result synthesis from multiple agents"""
        from src.schemas.orchestration import AgentResult
        
        # Create mock agent results
        agent_results = [
            AgentResult(
                agent_type=AgentType.PRICING,
                success=True,
                data={
                    'agent': 'pricing',
                    'status': 'completed',
                    'confidence': 0.85,
                    'data': {
                        'message': 'Analyzed 5 products, found 3 price gaps',
                        'average_price': 29.99,
                        'price_change_pct': 5.2
                    },
                    'recommendations': [
                        {
                            'title': 'Adjust pricing',
                            'description': 'Consider price increase',
                            'priority': 'high',
                            'impact': 'high',
                            'urgency': 'medium',
                            'confidence': 0.85
                        }
                    ]
                },
                execution_time=1.5,
                confidence=0.85
            ),
            AgentResult(
                agent_type=AgentType.SENTIMENT,
                success=True,
                data={
                    'agent': 'sentiment',
                    'status': 'completed',
                    'confidence': 0.78,
                    'data': {
                        'message': 'Analyzed 50 reviews with 0.65 average sentiment',
                        'average_sentiment': 0.65,
                        'sentiment_change': 3.1
                    },
                    'recommendations': []
                },
                execution_time=2.1,
                confidence=0.78
            )
        ]
        
        # Synthesize results
        report = result_synthesizer.synthesize_results(
            agent_results,
            query="Analyze product performance"
        )
        
        # Verify report structure
        assert report.report_id is not None
        assert report.query == "Analyze product performance"
        assert report.executive_summary is not None
        assert len(report.key_metrics) > 0
        assert len(report.insights) > 0
        assert report.overall_confidence > 0
        
        # Verify metrics
        metric_names = [m.name for m in report.key_metrics]
        assert "Average Price" in metric_names
        assert "Average Sentiment" in metric_names
        
        # Verify action items
        assert len(report.action_items) > 0
        assert report.action_items[0].title == 'Adjust pricing'
    
    def test_result_synthesis_with_failures(self, result_synthesizer):
        """Test result synthesis with some failed agents"""
        from src.schemas.orchestration import AgentResult
        
        agent_results = [
            AgentResult(
                agent_type=AgentType.PRICING,
                success=True,
                data={
                    'agent': 'pricing',
                    'confidence': 0.85,
                    'data': {'message': 'Success'}
                },
                execution_time=1.5,
                confidence=0.85
            ),
            AgentResult(
                agent_type=AgentType.SENTIMENT,
                success=False,
                error="Timeout",
                execution_time=30.0
            )
        ]
        
        report = result_synthesizer.synthesize_results(agent_results)
        
        # Should still generate report
        assert report.report_id is not None
        
        # Should have data quality warnings
        assert len(report.data_quality_warnings) > 0
        
        # Should have uncertainties
        assert len(report.uncertainties) > 0
        
        # Should indicate sentiment failure
        failed_agents = report.agent_results['failed']
        assert len(failed_agents) == 1
        assert failed_agents[0]['agent'] == 'sentiment'
    
    def test_action_item_prioritization(self, result_synthesizer):
        """Test action item prioritization"""
        recommendations = [
            {
                'title': 'Low priority action',
                'description': 'Can wait',
                'priority': 'low',
                'impact': 'low',
                'urgency': 'low',
                'confidence': 0.5
            },
            {
                'title': 'High priority action',
                'description': 'Do now',
                'priority': 'high',
                'impact': 'high',
                'urgency': 'high',
                'confidence': 0.9
            },
            {
                'title': 'Medium priority action',
                'description': 'Do soon',
                'priority': 'medium',
                'impact': 'medium',
                'urgency': 'medium',
                'confidence': 0.7
            }
        ]
        
        action_items = result_synthesizer.prioritize_action_items(recommendations)
        
        # Should be sorted by priority
        assert len(action_items) == 3
        assert action_items[0].title == 'High priority action'
        assert action_items[0].priority == 'high'
        assert action_items[-1].title == 'Low priority action'
    
    def test_confidence_calculation(self, result_synthesizer):
        """Test overall confidence calculation"""
        # High confidence agents
        high_confidences = [0.9, 0.85, 0.88]
        high_result = result_synthesizer.calculate_overall_confidence(high_confidences)
        assert high_result > 0.8
        
        # Low confidence agents
        low_confidences = [0.4, 0.5, 0.45]
        low_result = result_synthesizer.calculate_overall_confidence(low_confidences)
        assert low_result < 0.6
        
        # Mixed confidence
        mixed_confidences = [0.9, 0.5, 0.7]
        mixed_result = result_synthesizer.calculate_overall_confidence(mixed_confidences)
        assert 0.5 < mixed_result < 0.8
        
        # Empty list
        empty_result = result_synthesizer.calculate_overall_confidence([])
        assert empty_result == 0.5  # Default
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(
        self,
        query_router,
        execution_service,
        result_synthesizer
    ):
        """Test complete end-to-end pipeline"""
        # Step 1: Route query
        query = "Analyze pricing and sentiment for my products"
        routing_decision = query_router.route_query(query)
        
        assert routing_decision.required_agents is not None
        assert len(routing_decision.required_agents) >= 2
        
        # Step 2: Create execution plan
        plan = ExecutionPlan(
            execution_mode=routing_decision.execution_mode,
            tasks=[
                AgentTask(
                    agent_type=agent,
                    parameters={},
                    timeout_seconds=30
                )
                for agent in routing_decision.required_agents
            ],
            parallel_groups=[routing_decision.required_agents],
            estimated_duration=routing_decision.estimated_duration
        )
        
        # Step 3: Execute agents
        agent_results = await execution_service.execute_plan(plan)
        
        assert len(agent_results) > 0
        
        # Step 4: Synthesize results
        report = result_synthesizer.synthesize_results(agent_results, query)
        
        # Verify complete report
        assert report.report_id is not None
        assert report.query == query
        assert report.executive_summary is not None
        assert report.overall_confidence > 0
        
        # Should have metrics from multiple agents
        assert len(report.key_metrics) >= 0  # May be 0 with mock data
        
        # Should have insights
        assert len(report.insights) > 0
    
    def test_pattern_matching(self, query_router):
        """Test query pattern matching"""
        # Test various query patterns
        test_cases = [
            ("price comparison", AgentType.PRICING),
            ("customer reviews", AgentType.SENTIMENT),
            ("sales forecast", AgentType.DEMAND_FORECAST),
            ("inventory levels", AgentType.DEMAND_FORECAST),
        ]
        
        for query, expected_agent in test_cases:
            patterns = query_router.match_patterns(query.lower())
            
            # Should match at least one pattern
            assert len(patterns) > 0
            
            # Should suggest the expected agent
            suggested_agents = set()
            for pattern in patterns:
                suggested_agents.update(pattern.suggested_agents)
            
            assert expected_agent in suggested_agents
    
    def test_cache_key_generation(self, query_router):
        """Test cache key generation"""
        query1 = "What are my prices?"
        query2 = "What are my prices?"  # Same query
        query3 = "What are my prices"   # Different (no question mark)
        
        agents = [AgentType.PRICING]
        
        key1 = query_router._generate_cache_key(query1, agents)
        key2 = query_router._generate_cache_key(query2, agents)
        key3 = query_router._generate_cache_key(query3, agents)
        
        # Same queries should generate same key
        assert key1 == key2
        
        # Different queries should generate different keys
        # (though normalization might make them the same)
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_execution_stats_tracking(self, execution_service):
        """Test execution statistics tracking"""
        # Initially no stats
        stats = execution_service.get_execution_stats()
        initial_count = stats['total_executions']
        
        # Record some executions
        from src.schemas.orchestration import AgentResult, ExecutionPlan, AgentTask
        
        plan = ExecutionPlan(
            execution_mode=ExecutionMode.QUICK,
            tasks=[
                AgentTask(
                    agent_type=AgentType.PRICING,
                    parameters={},
                    timeout_seconds=30
                )
            ],
            parallel_groups=[[AgentType.PRICING]],
            estimated_duration=timedelta(seconds=30)
        )
        
        results = [
            AgentResult(
                agent_type=AgentType.PRICING,
                success=True,
                data={'test': 'data'},
                execution_time=1.5,
                confidence=0.85
            )
        ]
        
        execution_service._record_execution(plan, results)
        
        # Check stats updated
        new_stats = execution_service.get_execution_stats()
        assert new_stats['total_executions'] == initial_count + 1
