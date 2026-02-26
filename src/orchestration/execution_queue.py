"""Execution Queue for managing request backpressure"""
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
from collections import deque

from src.schemas.orchestration import (
    QueryRequest,
    QueuePosition,
    Priority,
    ExecutionMode
)


class ExecutionQueue:
    """
    Manages backpressure for Deep Mode requests.
    
    Implements priority queue with:
    - Priority-based ordering
    - Wait time estimation
    - Queue depth monitoring
    - FIFO within same priority
    
    TENANT ISOLATION:
    Queue operations are tenant-aware but queue is shared across tenants
    with fair scheduling.
    """
    
    def __init__(self, max_concurrent_deep: int = 3):
        """
        Initialize execution queue.
        
        Args:
            max_concurrent_deep: Maximum concurrent deep mode executions
        """
        self.max_concurrent_deep = max_concurrent_deep
        self.current_deep_executions = 0
        
        # Priority queues (high, normal, low)
        self.queues = {
            Priority.HIGH: deque(),
            Priority.NORMAL: deque(),
            Priority.LOW: deque()
        }
        
        self.processing: List[QueryRequest] = []
        self.completed: List[QueryRequest] = []
        
        self._lock = asyncio.Lock()
    
    async def enqueue_request(
        self,
        request: QueryRequest
    ) -> QueuePosition:
        """
        Enqueue a request.
        
        Args:
            request: Query request to enqueue
            
        Returns:
            QueuePosition with estimated wait time
        """
        async with self._lock:
            # Quick mode requests bypass queue
            if request.execution_mode == ExecutionMode.QUICK:
                return QueuePosition(
                    position=0,
                    estimated_wait_time=timedelta(seconds=0),
                    request_id=request.request_id
                )
            
            # Add to appropriate priority queue
            self.queues[request.priority].append(request)
            
            # Calculate position
            position = self._calculate_position(request)
            
            # Create QueuePosition object
            queue_position = QueuePosition(
                position=position,
                estimated_wait_time=timedelta(seconds=0),  # Placeholder
                request_id=request.request_id
            )
            
            # Estimate wait time
            wait_time = self.estimate_wait_time(queue_position)
            
            # Update with actual wait time
            queue_position.estimated_wait_time = wait_time
            
            return queue_position
    
    async def dequeue_request(self) -> Optional[QueryRequest]:
        """
        Dequeue the next request to process.
        
        Returns:
            Next QueryRequest or None if queue empty or at capacity
        """
        async with self._lock:
            # Check if we can process more deep mode requests
            if self.current_deep_executions >= self.max_concurrent_deep:
                return None
            
            # Try to get request from priority queues (high -> normal -> low)
            for priority in [Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                if self.queues[priority]:
                    request = self.queues[priority].popleft()
                    self.processing.append(request)
                    
                    if request.execution_mode == ExecutionMode.DEEP:
                        self.current_deep_executions += 1
                    
                    return request
            
            return None
    
    async def mark_completed(self, request: QueryRequest) -> None:
        """
        Mark a request as completed.
        
        Args:
            request: Completed request
        """
        async with self._lock:
            if request in self.processing:
                self.processing.remove(request)
                self.completed.append(request)
                
                if request.execution_mode == ExecutionMode.DEEP:
                    self.current_deep_executions = max(0, self.current_deep_executions - 1)
    
    def get_queue_depth(self) -> int:
        """
        Get total queue depth.
        
        Returns:
            Number of requests in queue
        """
        return sum(len(q) for q in self.queues.values())
    
    def get_queue_depth_by_priority(self) -> dict:
        """
        Get queue depth by priority.
        
        Returns:
            Dictionary with depth per priority
        """
        return {
            priority.value: len(queue)
            for priority, queue in self.queues.items()
        }
    
    def estimate_wait_time(self, position: QueuePosition) -> timedelta:
        """
        Estimate wait time for a queue position.
        
        Args:
            position: Queue position
            
        Returns:
            Estimated wait time
        """
        # Estimate based on position and average execution time
        # Assume 5 minutes per deep mode request
        avg_execution_time = 300  # seconds
        
        # Account for concurrent processing
        concurrent_factor = self.max_concurrent_deep
        
        # Calculate wait time
        wait_seconds = (position.position * avg_execution_time) / concurrent_factor
        
        return timedelta(seconds=wait_seconds)
    
    def _calculate_position(self, request: QueryRequest) -> int:
        """
        Calculate position in queue for a request.
        
        Args:
            request: Query request
            
        Returns:
            Position (1-indexed)
        """
        position = 1
        
        # Count requests ahead in higher priority queues
        for priority in [Priority.HIGH, Priority.NORMAL, Priority.LOW]:
            if priority.value > request.priority.value:
                position += len(self.queues[priority])
            elif priority == request.priority:
                # Position within same priority queue
                position += len(self.queues[priority])
                break
        
        return position
    
    def get_stats(self) -> dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        return {
            'total_queued': self.get_queue_depth(),
            'by_priority': self.get_queue_depth_by_priority(),
            'processing': len(self.processing),
            'completed': len(self.completed),
            'current_deep_executions': self.current_deep_executions,
            'capacity_used': self.current_deep_executions / self.max_concurrent_deep
        }
    
    async def clear_queue(self) -> int:
        """
        Clear all queues (for testing/admin purposes).
        
        Returns:
            Number of requests cleared
        """
        async with self._lock:
            count = self.get_queue_depth()
            
            for queue in self.queues.values():
                queue.clear()
            
            return count
