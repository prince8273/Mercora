"""Ingestion scheduler for managing data collection tasks"""
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of an ingestion task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class IngestionTask:
    """Represents a data ingestion task"""
    task_id: str
    source_name: str
    task_type: str  # 'api', 'scraper', 'file'
    schedule: str  # cron-like schedule or interval
    handler: Callable
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    failure_count: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class IngestionScheduler:
    """
    Manages scheduling and execution of data ingestion tasks.
    
    In production, this would integrate with Celery Beat for distributed task scheduling.
    For MVP, provides a simplified in-memory scheduler.
    
    Responsibilities:
    - Schedule periodic data ingestion tasks
    - Execute tasks with retry logic
    - Handle task failures with isolation
    - Track task execution history
    """
    
    def __init__(self):
        """Initialize the scheduler"""
        self.tasks: Dict[str, IngestionTask] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def schedule_task(
        self,
        task_id: str,
        source_name: str,
        task_type: str,
        handler: Callable,
        schedule: str = "hourly",
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionTask:
        """
        Schedule a new ingestion task.
        
        Args:
            task_id: Unique task identifier
            source_name: Name of data source
            task_type: Type of task (api, scraper, file)
            handler: Function to execute for ingestion
            schedule: Schedule string (hourly, daily, etc.)
            max_retries: Maximum retry attempts on failure
            metadata: Additional task metadata
            
        Returns:
            Created IngestionTask
        """
        task = IngestionTask(
            task_id=task_id,
            source_name=source_name,
            task_type=task_type,
            schedule=schedule,
            handler=handler,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_run(schedule)
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled task {task_id} for source {source_name}")
        
        return task
    
    def execute_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a specific ingestion task.
        
        Args:
            task_id: Task identifier
            **kwargs: Additional arguments for task handler
            
        Returns:
            Execution result dictionary
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.utcnow()
        
        result = {
            'task_id': task_id,
            'source_name': task.source_name,
            'start_time': task.last_run,
            'status': 'success',
            'records_ingested': 0,
            'errors': []
        }
        
        try:
            # Execute the handler
            logger.info(f"Executing task {task_id} for source {task.source_name}")
            handler_result = task.handler(**kwargs)
            
            # Update result
            result['records_ingested'] = handler_result.get('records_count', 0)
            result['end_time'] = datetime.utcnow()
            result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.failure_count = 0
            task.next_run = self._calculate_next_run(task.schedule, from_time=task.last_run)
            
            logger.info(f"Task {task_id} completed successfully: {result['records_ingested']} records")
            
        except Exception as e:
            # Handle failure
            logger.error(f"Task {task_id} failed: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
            result['errors'].append(str(e))
            result['end_time'] = datetime.utcnow()
            result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
            
            task.failure_count += 1
            
            # Determine if retry is needed
            if task.failure_count < task.max_retries:
                task.status = TaskStatus.RETRYING
                task.next_run = datetime.utcnow() + timedelta(seconds=task.retry_delay * task.failure_count)
                logger.info(f"Task {task_id} will retry in {task.retry_delay * task.failure_count} seconds")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed after {task.max_retries} retries")
        
        # Store execution history
        self.execution_history.append(result)
        
        return result
    
    def execute_all_due_tasks(self) -> List[Dict[str, Any]]:
        """
        Execute all tasks that are due to run.
        
        Returns:
            List of execution results
        """
        now = datetime.utcnow()
        results = []
        
        for task_id, task in self.tasks.items():
            if task.next_run and task.next_run <= now:
                try:
                    result = self.execute_task(task_id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute task {task_id}: {str(e)}")
                    # Continue with other tasks (failure isolation)
                    results.append({
                        'task_id': task_id,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        return {
            'task_id': task.task_id,
            'source_name': task.source_name,
            'status': task.status.value,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'failure_count': task.failure_count,
            'max_retries': task.max_retries
        }
    
    def get_execution_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history for tasks.
        
        Args:
            task_id: Optional task ID to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        history = self.execution_history
        
        if task_id:
            history = [h for h in history if h['task_id'] == task_id]
        
        return history[-limit:]
    
    def _calculate_next_run(self, schedule: str, from_time: Optional[datetime] = None) -> datetime:
        """
        Calculate next run time based on schedule.
        
        Args:
            schedule: Schedule string
            from_time: Base time for calculation (default: now)
            
        Returns:
            Next run datetime
        """
        base_time = from_time or datetime.utcnow()
        
        if schedule == "hourly":
            return base_time + timedelta(hours=1)
        elif schedule == "daily":
            return base_time + timedelta(days=1)
        elif schedule == "weekly":
            return base_time + timedelta(weeks=1)
        elif schedule.startswith("every_"):
            # Parse "every_X_minutes" or "every_X_hours"
            parts = schedule.split("_")
            if len(parts) == 3:
                interval = int(parts[1])
                unit = parts[2]
                if unit == "minutes":
                    return base_time + timedelta(minutes=interval)
                elif unit == "hours":
                    return base_time + timedelta(hours=interval)
        
        # Default to hourly
        return base_time + timedelta(hours=1)
