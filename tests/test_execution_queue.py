"""Tests for Execution Queue"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

from src.orchestration.execution_queue import ExecutionQueue
from src.schemas.orchestration import (
    QueryRequest,
    ExecutionMode,
    Priority
)


@pytest.fixture
def queue():
    """Create an execution queue instance"""
    return ExecutionQueue(max_concurrent_deep=3)


@pytest.fixture
def quick_request():
    """Create a quick mode request"""
    return QueryRequest(
        request_id=uuid4(),
        query="Test query",
        tenant_id=uuid4(),
        user_id=uuid4(),
        execution_mode=ExecutionMode.QUICK,
        priority=Priority.NORMAL
    )


@pytest.fixture
def deep_request():
    """Create a deep mode request"""
    return QueryRequest(
        request_id=uuid4(),
        query="Test deep query",
        tenant_id=uuid4(),
        user_id=uuid4(),
        execution_mode=ExecutionMode.DEEP,
        priority=Priority.NORMAL
    )


class TestEnqueueDequeue:
    """Tests for enqueue and dequeue operations"""
    
    @pytest.mark.asyncio
    async def test_enqueue_quick_request(self, queue, quick_request):
        """Test enqueueing a quick mode request"""
        position = await queue.enqueue_request(quick_request)
        
        # Quick mode bypasses queue
        assert position.position == 0
        assert position.estimated_wait_time.total_seconds() == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_deep_request(self, queue, deep_request):
        """Test enqueueing a deep mode request"""
        position = await queue.enqueue_request(deep_request)
        
        assert position.position > 0
        assert position.request_id == deep_request.request_id
    
    @pytest.mark.asyncio
    async def test_dequeue_request(self, queue, deep_request):
        """Test dequeueing a request"""
        await queue.enqueue_request(deep_request)
        
        dequeued = await queue.dequeue_request()
        
        assert dequeued is not None
        assert dequeued.request_id == deep_request.request_id
    
    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, queue):
        """Test dequeueing from empty queue"""
        dequeued = await queue.dequeue_request()
        
        assert dequeued is None
    
    @pytest.mark.asyncio
    async def test_dequeue_respects_capacity(self, queue):
        """Test that dequeue respects max concurrent limit"""
        # Fill up to capacity
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            await queue.enqueue_request(request)
            await queue.dequeue_request()
        
        # Add one more
        extra_request = QueryRequest(
            request_id=uuid4(),
            query="Extra query",
            tenant_id=uuid4(),
            user_id=uuid4(),
            execution_mode=ExecutionMode.DEEP,
            priority=Priority.NORMAL
        )
        await queue.enqueue_request(extra_request)
        
        # Should not dequeue (at capacity)
        dequeued = await queue.dequeue_request()
        assert dequeued is None


class TestPriorityHandling:
    """Tests for priority-based ordering"""
    
    @pytest.mark.asyncio
    async def test_high_priority_first(self, queue):
        """Test that high priority requests are dequeued first"""
        # Enqueue normal priority
        normal_request = QueryRequest(
            request_id=uuid4(),
            query="Normal",
            tenant_id=uuid4(),
            user_id=uuid4(),
            execution_mode=ExecutionMode.DEEP,
            priority=Priority.NORMAL
        )
        await queue.enqueue_request(normal_request)
        
        # Enqueue high priority
        high_request = QueryRequest(
            request_id=uuid4(),
            query="High",
            tenant_id=uuid4(),
            user_id=uuid4(),
            execution_mode=ExecutionMode.DEEP,
            priority=Priority.HIGH
        )
        await queue.enqueue_request(high_request)
        
        # High priority should be dequeued first
        dequeued = await queue.dequeue_request()
        assert dequeued.request_id == high_request.request_id
    
    @pytest.mark.asyncio
    async def test_fifo_within_priority(self, queue):
        """Test FIFO ordering within same priority"""
        requests = []
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            requests.append(request)
            await queue.enqueue_request(request)
        
        # Should dequeue in FIFO order
        for expected_request in requests:
            dequeued = await queue.dequeue_request()
            assert dequeued.request_id == expected_request.request_id
            await queue.mark_completed(dequeued)


class TestQueueDepth:
    """Tests for queue depth monitoring"""
    
    @pytest.mark.asyncio
    async def test_get_queue_depth(self, queue):
        """Test getting total queue depth"""
        assert queue.get_queue_depth() == 0
        
        # Add requests
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            await queue.enqueue_request(request)
        
        assert queue.get_queue_depth() == 3
    
    @pytest.mark.asyncio
    async def test_get_queue_depth_by_priority(self, queue):
        """Test getting queue depth by priority"""
        # Add high priority
        high_request = QueryRequest(
            request_id=uuid4(),
            query="High",
            tenant_id=uuid4(),
            user_id=uuid4(),
            execution_mode=ExecutionMode.DEEP,
            priority=Priority.HIGH
        )
        await queue.enqueue_request(high_request)
        
        # Add normal priority
        normal_request = QueryRequest(
            request_id=uuid4(),
            query="Normal",
            tenant_id=uuid4(),
            user_id=uuid4(),
            execution_mode=ExecutionMode.DEEP,
            priority=Priority.NORMAL
        )
        await queue.enqueue_request(normal_request)
        
        depth_by_priority = queue.get_queue_depth_by_priority()
        
        assert depth_by_priority['high'] == 1
        assert depth_by_priority['normal'] == 1
        assert depth_by_priority['low'] == 0


class TestWaitTimeEstimation:
    """Tests for wait time estimation"""
    
    @pytest.mark.asyncio
    async def test_estimate_wait_time(self, queue, deep_request):
        """Test wait time estimation"""
        position = await queue.enqueue_request(deep_request)
        
        wait_time = queue.estimate_wait_time(position)
        
        assert wait_time.total_seconds() > 0
    
    @pytest.mark.asyncio
    async def test_wait_time_increases_with_position(self, queue):
        """Test that wait time increases with queue position"""
        requests = []
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            position = await queue.enqueue_request(request)
            requests.append((request, position))
        
        # Later positions should have longer wait times
        wait_times = [queue.estimate_wait_time(pos) for _, pos in requests]
        for i in range(len(wait_times) - 1):
            assert wait_times[i+1].total_seconds() >= wait_times[i].total_seconds()


class TestCompletion:
    """Tests for marking requests as completed"""
    
    @pytest.mark.asyncio
    async def test_mark_completed(self, queue, deep_request):
        """Test marking a request as completed"""
        await queue.enqueue_request(deep_request)
        dequeued = await queue.dequeue_request()
        
        assert queue.current_deep_executions == 1
        
        await queue.mark_completed(dequeued)
        
        assert queue.current_deep_executions == 0
    
    @pytest.mark.asyncio
    async def test_mark_completed_frees_capacity(self, queue):
        """Test that marking completed frees up capacity"""
        # Fill to capacity
        requests = []
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            await queue.enqueue_request(request)
            dequeued = await queue.dequeue_request()
            requests.append(dequeued)
        
        # At capacity
        assert queue.current_deep_executions == 3
        
        # Complete one
        await queue.mark_completed(requests[0])
        
        # Should have capacity now
        assert queue.current_deep_executions == 2


class TestQueueStats:
    """Tests for queue statistics"""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, queue, deep_request):
        """Test getting queue statistics"""
        await queue.enqueue_request(deep_request)
        
        stats = queue.get_stats()
        
        assert 'total_queued' in stats
        assert 'by_priority' in stats
        assert 'processing' in stats
        assert 'completed' in stats
        assert 'current_deep_executions' in stats
        assert 'capacity_used' in stats
    
    @pytest.mark.asyncio
    async def test_clear_queue(self, queue):
        """Test clearing the queue"""
        # Add requests
        for i in range(3):
            request = QueryRequest(
                request_id=uuid4(),
                query=f"Query {i}",
                tenant_id=uuid4(),
                user_id=uuid4(),
                execution_mode=ExecutionMode.DEEP,
                priority=Priority.NORMAL
            )
            await queue.enqueue_request(request)
        
        assert queue.get_queue_depth() == 3
        
        cleared = await queue.clear_queue()
        
        assert cleared == 3
        assert queue.get_queue_depth() == 0
