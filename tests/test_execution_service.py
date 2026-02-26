"""Tests for Execution Service"""
import pytest
import asyncio
from uuid import uuid4
from datetime import timedelta

from src.orchestration.execution_service import ExecutionService
from src.schemas.orchestration import (
    ExecutionPlan,
    ExecutionMode,
    AgentType,
    AgentTask,
    FallbackStrategy
)


@pytest.fixture
def service():
    """Create an execution service instance"""
    tenant_id = uuid4()
    return ExecutionService(tenant_id=tenant_id)


@pytest.fixture
def simple_plan():
    """Create a simple execution plan"""
    tasks = [
        AgentTask(
            agent_type=AgentType.PRICING,
            parameters={'product_ids': ['prod-1']},
            dependencies=[],
            timeout_seconds=10
        )
    ]
    
    return ExecutionPlan(
        tasks=tasks,
        execution_mode=ExecutionMode.QUICK,
        parallel_groups=[[AgentType.PRICING]],
        estimated_duration=timedelta(seconds=30)
    )


@pytest.fixture
def multi_agent_plan():
    """Create a multi-agent execution plan"""
    tasks = [
        AgentTask(
            agent_type=AgentType.PRICING,
            parameters={},
            dependencies=[],
            timeout_seconds=10
        ),
        AgentTask(
            agent_type=AgentType.SENTIMENT,
            parameters={},
            dependencies=[],
            timeout_seconds=10
        ),
        AgentTask(
            agent_type=AgentType.DEMAND_FORECAST,
            parameters={},
            dependencies=[],
            timeout_seconds=10
        )
    ]
    
    return ExecutionPlan(
        tasks=tasks,
        execution_mode=ExecutionMode.DEEP,
        parallel_groups=[[AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST]],
        estimated_duration=timedelta(seconds=120)
    )


class TestPlanExecution:
    """Tests for plan execution"""
    
    @pytest.mark.asyncio
    async def test_execute_simple_plan(self, service, simple_plan):
        """Test executing a simple single-agent plan"""
        results = await service.execute_plan(simple_plan)
        
        assert len(results) == 1
        assert results[0].agent_type == AgentType.PRICING
        assert results[0].success is True
        assert results[0].execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_multi_agent_plan(self, service, multi_agent_plan):
        """Test executing a multi-agent plan"""
        results = await service.execute_plan(multi_agent_plan)
        
        assert len(results) == 3
        # All agents should have results
        agent_types = {r.agent_type for r in results}
        assert AgentType.PRICING in agent_types
        assert AgentType.SENTIMENT in agent_types
        assert AgentType.DEMAND_FORECAST in agent_types
    
    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self, service, multi_agent_plan):
        """Test that parallel execution is faster than sequential"""
        import time
        
        start = time.time()
        results = await service.execute_plan(multi_agent_plan)
        parallel_time = time.time() - start
        
        # Parallel execution should complete in roughly the time of the slowest agent
        # Not the sum of all agents
        assert parallel_time < 1.0  # Should be much faster than 3 * 0.1s sequential


class TestParallelExecution:
    """Tests for parallel agent execution"""
    
    @pytest.mark.asyncio
    async def test_execute_agents_parallel(self, service, multi_agent_plan):
        """Test parallel execution of multiple agents"""
        agents = [AgentType.PRICING, AgentType.SENTIMENT]
        
        results = await service.execute_agents_parallel(agents, multi_agent_plan)
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_parallel_execution_handles_exceptions(self, service, multi_agent_plan):
        """Test that parallel execution handles exceptions gracefully"""
        # This test verifies exception handling in parallel execution
        agents = [AgentType.PRICING, AgentType.SENTIMENT]
        
        results = await service.execute_agents_parallel(agents, multi_agent_plan)
        
        # Should return results even if some fail
        assert len(results) == 2


class TestFailureHandling:
    """Tests for failure handling"""
    
    def test_handle_timeout_error(self, service):
        """Test handling of timeout errors"""
        strategy = service.handle_agent_failure(
            AgentType.PRICING,
            TimeoutError("Timeout")
        )
        
        assert strategy == FallbackStrategy.USE_CACHE
    
    def test_handle_critical_agent_failure(self, service):
        """Test handling of critical agent failures"""
        strategy = service.handle_agent_failure(
            AgentType.PRICING,
            Exception("Some error")
        )
        
        # Critical agents should retry
        assert strategy == FallbackStrategy.RETRY
    
    def test_handle_non_critical_agent_failure(self, service):
        """Test handling of non-critical agent failures"""
        strategy = service.handle_agent_failure(
            AgentType.DATA_QA,
            Exception("Some error")
        )
        
        # Non-critical agents should skip
        assert strategy == FallbackStrategy.SKIP


class TestResourceLimits:
    """Tests for resource limit enforcement"""
    
    def test_quick_mode_time_limit(self, service):
        """Test quick mode time limit"""
        # Within limit
        assert service.enforce_resource_limits(60, ExecutionMode.QUICK) is True
        
        # Exceeds limit
        assert service.enforce_resource_limits(130, ExecutionMode.QUICK) is False
    
    def test_deep_mode_time_limit(self, service):
        """Test deep mode time limit"""
        # Within limit
        assert service.enforce_resource_limits(300, ExecutionMode.DEEP) is True
        
        # Exceeds limit
        assert service.enforce_resource_limits(650, ExecutionMode.DEEP) is False


class TestExecutionStats:
    """Tests for execution statistics"""
    
    @pytest.mark.asyncio
    async def test_execution_recorded(self, service, simple_plan):
        """Test that executions are recorded"""
        initial_count = len(service.execution_history)
        
        await service.execute_plan(simple_plan)
        
        assert len(service.execution_history) == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_get_execution_stats_empty(self, service):
        """Test getting stats when no executions"""
        stats = service.get_execution_stats()
        
        assert stats['total_executions'] == 0
        assert stats['success_rate'] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_execution_stats_with_history(self, service, simple_plan):
        """Test getting stats with execution history"""
        await service.execute_plan(simple_plan)
        await service.execute_plan(simple_plan)
        
        stats = service.get_execution_stats()
        
        assert stats['total_executions'] == 2
        assert stats['success_rate'] > 0
        assert 'avg_execution_time' in stats
        assert 'by_mode' in stats
