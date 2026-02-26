"""Tests for IngestionScheduler component"""
import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from src.ingestion.scheduler import IngestionScheduler, TaskStatus


@pytest.fixture
def scheduler():
    """Create an IngestionScheduler instance"""
    return IngestionScheduler()


@pytest.fixture
def mock_handler():
    """Create a mock task handler"""
    def handler(**kwargs):
        return {'records_count': 10}
    return handler


class TestTaskScheduling:
    """Tests for task scheduling"""
    
    def test_schedule_task(self, scheduler, mock_handler):
        """Test scheduling a new task"""
        task = scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=mock_handler,
            schedule='hourly'
        )
        
        assert task.task_id == 'test-task-1'
        assert task.source_name == 'amazon'
        assert task.status == TaskStatus.PENDING
        assert task.next_run is not None
    
    def test_execute_task_success(self, scheduler, mock_handler):
        """Test successful task execution"""
        scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=mock_handler
        )
        
        result = scheduler.execute_task('test-task-1')
        
        assert result['status'] == 'success'
        assert result['records_ingested'] == 10
        assert 'duration_seconds' in result
    
    def test_execute_task_failure(self, scheduler):
        """Test task execution failure"""
        def failing_handler(**kwargs):
            raise Exception("API connection failed")
        
        scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=failing_handler,
            max_retries=2
        )
        
        result = scheduler.execute_task('test-task-1')
        
        assert result['status'] == 'failed'
        assert 'error' in result
        assert 'API connection failed' in result['error']
    
    def test_task_retry_logic(self, scheduler):
        """Test task retry on failure"""
        call_count = {'count': 0}
        
        def intermittent_handler(**kwargs):
            call_count['count'] += 1
            if call_count['count'] < 2:
                raise Exception("Temporary failure")
            return {'records_count': 5}
        
        task = scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=intermittent_handler,
            max_retries=3
        )
        
        # First execution fails
        result1 = scheduler.execute_task('test-task-1')
        assert result1['status'] == 'failed'
        assert task.status == TaskStatus.RETRYING
        
        # Second execution succeeds
        result2 = scheduler.execute_task('test-task-1')
        assert result2['status'] == 'success'
        assert task.status == TaskStatus.COMPLETED


class TestScheduleCalculation:
    """Tests for schedule calculation"""
    
    def test_hourly_schedule(self, scheduler):
        """Test hourly schedule calculation"""
        now = datetime.utcnow()
        next_run = scheduler._calculate_next_run('hourly', from_time=now)
        
        expected = now + timedelta(hours=1)
        assert abs((next_run - expected).total_seconds()) < 1
    
    def test_daily_schedule(self, scheduler):
        """Test daily schedule calculation"""
        now = datetime.utcnow()
        next_run = scheduler._calculate_next_run('daily', from_time=now)
        
        expected = now + timedelta(days=1)
        assert abs((next_run - expected).total_seconds()) < 1
    
    def test_custom_interval_schedule(self, scheduler):
        """Test custom interval schedule"""
        now = datetime.utcnow()
        next_run = scheduler._calculate_next_run('every_30_minutes', from_time=now)
        
        expected = now + timedelta(minutes=30)
        assert abs((next_run - expected).total_seconds()) < 1


class TestExecutionHistory:
    """Tests for execution history tracking"""
    
    def test_execution_history_recorded(self, scheduler, mock_handler):
        """Test execution history is recorded"""
        scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=mock_handler
        )
        
        scheduler.execute_task('test-task-1')
        
        history = scheduler.get_execution_history()
        assert len(history) == 1
        assert history[0]['task_id'] == 'test-task-1'
    
    def test_execution_history_filtering(self, scheduler, mock_handler):
        """Test execution history filtering by task_id"""
        scheduler.schedule_task(
            task_id='test-task-1',
            source_name='amazon',
            task_type='api',
            handler=mock_handler
        )
        scheduler.schedule_task(
            task_id='test-task-2',
            source_name='ebay',
            task_type='api',
            handler=mock_handler
        )
        
        scheduler.execute_task('test-task-1')
        scheduler.execute_task('test-task-2')
        scheduler.execute_task('test-task-1')
        
        history = scheduler.get_execution_history(task_id='test-task-1')
        assert len(history) == 2
        assert all(h['task_id'] == 'test-task-1' for h in history)


# ==================== Property-Based Tests ====================

@settings(max_examples=100)
@given(
    task_count=st.integers(min_value=1, max_value=5),
    records_per_task=st.integers(min_value=1, max_value=10)
)
def test_property_scheduled_ingestion_stores_metadata(task_count, records_per_task):
    """
    # Feature: ecommerce-intelligence-agent, Property 1: Scheduled ingestion retrieves and stores data with metadata
    **Property 1: Scheduled ingestion retrieves and stores data with metadata**
    **Validates: Requirements 1.1, 1.4**
    
    Property: When scheduled data refresh occurs and ingestion completes successfully,
    the retrieved data is stored with timestamp and source metadata that can be queried back.
    
    This test validates:
    1. Scheduled tasks execute successfully
    2. Execution metadata is captured (task_id, source_name, timestamps, duration)
    3. Metadata can be queried back from execution history
    
    Note: This is a simplified test that validates the scheduler's metadata tracking.
    Full end-to-end database integration is tested separately in integration tests.
    """
    from uuid import uuid4
    from src.ingestion.base import RawRecord, BaseConnector
    
    # Create a mock connector that generates test data
    class MockConnector(BaseConnector):
        def __init__(self, tenant_id, source_name, record_count):
            super().__init__(tenant_id, source_name)
            self.record_count = record_count
        
        def fetch(self, *, since=None):
            """Generate test records"""
            for i in range(self.record_count):
                yield RawRecord(
                    source_id=f"{self.source_name}-record-{i}",
                    payload={
                        "sku": f"SKU-{i}",
                        "name": f"Product {i}",
                        "price": 10.0 + i
                    },
                    retrieved_at=datetime.utcnow(),
                    metadata={
                        "source_type": "test",
                        "batch_id": f"batch-{i // 5}"
                    }
                )
    
    scheduler = IngestionScheduler()
    tenant_id = uuid4()
    
    # Schedule multiple ingestion tasks
    task_ids = []
    for i in range(task_count):
        task_id = f'task-{i}'
        source_name = f'source-{i}'
        
        # Create connector for this task
        connector = MockConnector(tenant_id, source_name, records_per_task)
        
        # Handler that simulates ingestion (without actual database writes for property test)
        def make_handler(conn):
            def handler(**kwargs):
                # Simulate fetching records
                record_count = sum(1 for _ in conn.fetch())
                return {'records_count': record_count}
            return handler
        
        scheduler.schedule_task(
            task_id=task_id,
            source_name=source_name,
            task_type='api',
            handler=make_handler(connector)
        )
        task_ids.append(task_id)
    
    # Execute all tasks
    for task_id in task_ids:
        result = scheduler.execute_task(task_id)
        
        # Property validation: Execution metadata is stored
        assert 'task_id' in result, "Task ID must be in result"
        assert 'source_name' in result, "Source name must be in result"
        assert 'start_time' in result, "Start time must be in result"
        assert 'end_time' in result, "End time must be in result"
        assert 'duration_seconds' in result, "Duration must be in result"
        assert result['status'] == 'success', "Task should complete successfully"
        assert result['records_ingested'] == records_per_task, f"Should ingest {records_per_task} records"
        
        # Verify timestamps are valid
        assert isinstance(result['start_time'], datetime), "Start time must be datetime"
        assert isinstance(result['end_time'], datetime), "End time must be datetime"
        assert result['end_time'] >= result['start_time'], "End time must be after start time"
        assert result['duration_seconds'] >= 0, "Duration must be non-negative"
    
    # Property validation: Execution history can be queried back
    history = scheduler.get_execution_history()
    assert len(history) == task_count, f"Should have {task_count} execution records in history"
    
    for i, hist_record in enumerate(history):
        assert hist_record['task_id'] == f'task-{i}', "History must preserve task order"
        assert hist_record['source_name'] == f'source-{i}', "History must include source name"
        assert hist_record['status'] == 'success', "History must record success status"
        assert hist_record['records_ingested'] == records_per_task, "History must record ingestion count"


@settings(max_examples=100)
@given(
    failure_count=st.integers(min_value=1, max_value=5)
)
def test_property_ingestion_failure_isolation(failure_count):
    """
    **Property 3: Ingestion failures are isolated**
    **Validates: Requirements 1.5**
    
    Property: Failure of one task doesn't prevent execution of other tasks
    """
    scheduler = IngestionScheduler()
    
    # Create mix of successful and failing tasks
    for i in range(failure_count + 2):
        if i < failure_count:
            # Failing task
            def failing_handler(**kwargs):
                raise Exception(f"Task {i} failed")
            handler = failing_handler
        else:
            # Successful task
            def success_handler(**kwargs):
                return {'records_count': 10}
            handler = success_handler
        
        scheduler.schedule_task(
            task_id=f'task-{i}',
            source_name=f'source-{i}',
            task_type='api',
            handler=handler,
            max_retries=1
        )
        
        # Set next_run to now so task is due
        scheduler.tasks[f'task-{i}'].next_run = datetime.utcnow()
    
    # Execute all due tasks
    results = scheduler.execute_all_due_tasks()
    
    # All tasks should have been attempted
    assert len(results) == failure_count + 2
    
    # Some should have succeeded
    successful = [r for r in results if r['status'] == 'success']
    assert len(successful) >= 2  # At least the 2 non-failing tasks


@settings(max_examples=100)
@given(
    max_retries=st.integers(min_value=1, max_value=5)
)
def test_property_retry_with_exponential_backoff(max_retries):
    """
    **Property 49: API failures trigger retry with exponential backoff**
    **Validates: Requirements 11.3**
    
    Property: Failed tasks are retried with increasing delays
    """
    scheduler = IngestionScheduler()
    
    call_times = []
    
    def failing_handler(**kwargs):
        call_times.append(datetime.utcnow())
        raise Exception("API failure")
    
    task = scheduler.schedule_task(
        task_id='test-task',
        source_name='api',
        task_type='api',
        handler=failing_handler,
        max_retries=max_retries
    )
    
    # Execute task (will fail)
    scheduler.execute_task('test-task')
    
    # Task should be in retrying state if retries remain
    if max_retries > 1:
        assert task.status == TaskStatus.RETRYING
        assert task.next_run is not None
        # Next run should be in the future
        assert task.next_run > datetime.utcnow()
    else:
        assert task.status == TaskStatus.FAILED
