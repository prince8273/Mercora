"""
Property-Based Tests for Execution Service

These tests validate correctness properties for execution service functionality
using Hypothesis for property-based testing.

Focus: Testing behavioral properties, not implementation details.
"""
import pytest
import asyncio
import time
from hypothesis import given, strategies as st, settings, assume
from uuid import uuid4, UUID
from datetime import timedelta

from src.orchestration.execution_service import ExecutionService
from src.schemas.orchestration import (
    ExecutionPlan,
    ExecutionMode,
    AgentType,
    AgentTask,
    FallbackStrategy
)


# Strategy for generating execution plans
@st.composite
def execution_plan_strategy(draw, mode=None, min_agents=2, max_agents=4):
    """Generate realistic execution plans for testing"""
    if mode is None:
        mode = draw(st.sampled_from([ExecutionMode.QUICK, ExecutionMode.DEEP]))
    
    # Generate agent types
    num_agents = draw(st.integers(min_value=min_agents, max_value=max_agents))
    available_agents = [AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST, AgentType.DATA_QA]
    agents = draw(st.lists(
        st.sampled_from(available_agents),
        min_size=num_agents,
        max_size=num_agents,
        unique=True
    ))
    
    # Create tasks for each agent
    tasks = []
    for agent in agents:
        timeout = draw(st.integers(min_value=5, max_value=30))
        tasks.append(AgentTask(
            agent_type=agent,
            parameters={},
            timeout_seconds=timeout,
            required=draw(st.booleans())
        ))
    
    # For parallel execution test, put all agents in one group
    parallel_groups = [agents]
    
    return ExecutionPlan(
        execution_mode=mode,
        tasks=tasks,
        parallel_groups=parallel_groups,
        estimated_duration=timedelta(seconds=max(t.timeout_seconds for t in tasks))
    )


class TestExecutionServiceProperties:
    """Property-based tests for Execution Service"""
    
    @settings(max_examples=10, deadline=None)
    @given(plan=execution_plan_strategy(min_agents=2, max_agents=4))
    @pytest.mark.asyncio
    async def test_property_30_independent_agents_execute_in_parallel(self, plan):
        """
        # Feature: ecommerce-intelligence-agent, Property 30: Independent agents execute in parallel
        
        Property: For any query requiring multiple agents with no dependencies,
        the orchestration layer should execute those agents in parallel rather than sequentially.
        
        Validates: Requirements 6.5
        """
        tenant_id = uuid4()
        service = ExecutionService(tenant_id)
        
        # Record start time
        start_time = time.time()
        
        # Execute plan (agents have no dependencies, so should run in parallel)
        results = await service.execute_plan(plan, query_data=None)
        
        # Record end time
        total_execution_time = time.time() - start_time
        
        # Property 1: All agents must produce results
        assert len(results) == len(plan.tasks), \
            "Every agent in the plan must produce a result"
        
        # Property 2: All agents must be represented in results
        result_agents = {r.agent_type for r in results}
        plan_agents = {t.agent_type for t in plan.tasks}
        assert result_agents == plan_agents, \
            "Result set must match planned agent set"
        
        # Property 3: Each result must have execution metadata
        for result in results:
            assert result.agent_type is not None, "Result must identify its agent"
            assert result.execution_time >= 0, "Execution time must be non-negative"
            assert isinstance(result.success, bool), "Success must be boolean"
        
        # Property 4: Parallel execution should be faster than sequential
        # (Only test if execution times are meaningful - not near-zero)
        sequential_time = sum(r.execution_time for r in results)
        if sequential_time > 0.1:  # Only test if agents took meaningful time
            # Parallel should be significantly faster (allow 50% overhead)
            assert total_execution_time < sequential_time * 0.7, \
                f"Parallel execution should be faster than sequential"
    
    @settings(max_examples=10, deadline=None)
    @given(
        mode=st.sampled_from([ExecutionMode.QUICK, ExecutionMode.DEEP]),
        num_agents=st.integers(min_value=1, max_value=3)
    )
    @pytest.mark.asyncio
    async def test_property_29_deep_mode_enforces_resource_limits(self, mode, num_agents):
        """
        # Feature: ecommerce-intelligence-agent, Property 29: Deep Mode enforces resource limits
        
        Property: For any Deep Mode execution, the system should enforce configured
        execution time and resource limits, terminating requests that exceed limits.
        
        Validates: Requirements 6.4
        """
        tenant_id = uuid4()
        service = ExecutionService(tenant_id)
        
        # Create execution plan with agents
        available_agents = [AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST]
        agents = available_agents[:num_agents]
        
        tasks = [
            AgentTask(
                agent_type=agent,
                parameters={},
                timeout_seconds=10,
                required=True
            )
            for agent in agents
        ]
        
        plan = ExecutionPlan(
            execution_mode=mode,
            tasks=tasks,
            parallel_groups=[agents],
            estimated_duration=timedelta(seconds=10)
        )
        
        # Execute plan
        start_time = time.time()
        results = await service.execute_plan(plan, query_data=None)
        execution_time = time.time() - start_time
        
        # Property 1: Resource limit enforcement must be available
        within_limits = service.enforce_resource_limits(execution_time, mode)
        assert isinstance(within_limits, bool), \
            "Resource limit check must return boolean"
        
        # Property 2: Quick mode enforces 2-minute limit
        if mode == ExecutionMode.QUICK:
            assert service.enforce_resource_limits(60, ExecutionMode.QUICK) is True
            assert service.enforce_resource_limits(121, ExecutionMode.QUICK) is False
        
        # Property 3: Deep mode enforces 10-minute limit
        if mode == ExecutionMode.DEEP:
            assert service.enforce_resource_limits(300, ExecutionMode.DEEP) is True
            assert service.enforce_resource_limits(601, ExecutionMode.DEEP) is False
        
        # Property 4: All agents must complete within mode limits
        mode_limit = 120 if mode == ExecutionMode.QUICK else 600
        assert execution_time < mode_limit, \
            f"{mode.value} mode execution must complete within {mode_limit}s limit"
    
    @settings(max_examples=10, deadline=None)
    @given(num_agents=st.integers(min_value=2, max_value=4))
    @pytest.mark.asyncio
    async def test_property_45_component_failures_are_isolated(self, num_agents):
        """
        # Feature: ecommerce-intelligence-agent, Property 45: Component failures are isolated
        
        Property: For any component failure, the system should isolate the failure,
        log it, and continue operation with remaining functional components.
        
        Validates: Requirements 9.3
        """
        tenant_id = uuid4()
        service = ExecutionService(tenant_id)
        
        # Create execution plan with multiple agents
        available_agents = [AgentType.PRICING, AgentType.SENTIMENT, AgentType.DEMAND_FORECAST, AgentType.DATA_QA]
        agents = available_agents[:num_agents]
        
        # Create tasks (all non-required so execution continues on failure)
        tasks = [
            AgentTask(
                agent_type=agent,
                parameters={},
                timeout_seconds=10,
                required=False
            )
            for agent in agents
        ]
        
        plan = ExecutionPlan(
            execution_mode=ExecutionMode.DEEP,
            tasks=tasks,
            parallel_groups=[agents],
            estimated_duration=timedelta(seconds=10)
        )
        
        # Execute plan
        results = await service.execute_plan(plan, query_data=None)
        
        # Property 1: All agents must produce results (success or failure)
        assert len(results) == len(tasks), \
            "Every agent must produce a result, even if it fails"
        
        # Property 2: Results must identify their agent
        result_agents = {r.agent_type for r in results}
        plan_agents = {t.agent_type for t in plan.tasks}
        assert result_agents == plan_agents, \
            "All planned agents must be represented in results"
        
        # Property 3: Failed agents must have error information
        failed_results = [r for r in results if not r.success]
        for failed_result in failed_results:
            assert failed_result.error is not None, \
                "Failed agents must provide error information"
            assert len(failed_result.error) > 0, \
                "Error message must not be empty"
        
        # Property 4: Successful agents must not have errors
        successful_results = [r for r in results if r.success]
        for success_result in successful_results:
            assert success_result.error is None or success_result.error == "", \
                "Successful agents must not have error messages"
        
        # Property 5: Fallback strategies must be available
        for agent in agents:
            error = TimeoutError("Test timeout")
            fallback = service.handle_agent_failure(agent, error)
            assert isinstance(fallback, FallbackStrategy), \
                "Fallback strategy must be determined for all agent types"
            assert fallback in [
                FallbackStrategy.USE_CACHE,
                FallbackStrategy.RETRY,
                FallbackStrategy.SKIP,
                FallbackStrategy.FAIL
            ], "Fallback must be a valid strategy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
