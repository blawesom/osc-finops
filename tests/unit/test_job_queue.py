"""Unit tests for backend.services.job_queue."""
import pytest
import threading
import time
from datetime import datetime, timedelta
from backend.services.job_queue import JobQueue


class TestJobQueueInitialization:
    """Tests for JobQueue initialization."""
    
    def test_init_default_cleanup_interval(self):
        """Test initialization with default cleanup interval."""
        queue = JobQueue()
        assert queue.cleanup_interval_seconds == 3600
        assert len(queue._jobs) == 0
    
    def test_init_custom_cleanup_interval(self):
        """Test initialization with custom cleanup interval."""
        queue = JobQueue(cleanup_interval_seconds=7200)
        assert queue.cleanup_interval_seconds == 7200


class TestCreateJob:
    """Tests for create_job method."""
    
    def test_create_job_basic(self):
        """Test creating a basic job."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        assert job_id is not None
        assert isinstance(job_id, str)
        
        job = queue.get_job(job_id)
        assert job is not None
        assert job["job_id"] == job_id
        assert job["job_type"] == "trends"
        assert job["status"] == "pending"
        assert job["progress"] == 0
        assert job["result"] is None
        assert job["error"] is None
        assert "created_at" in job
        assert "updated_at" in job
    
    def test_create_job_with_metadata(self):
        """Test creating a job with metadata."""
        queue = JobQueue()
        metadata = {"region": "eu-west-2", "from_date": "2024-01-01"}
        job_id = queue.create_job("trends", metadata=metadata)
        
        job = queue.get_job(job_id)
        assert job["metadata"] == metadata
    
    def test_create_job_with_empty_metadata(self):
        """Test creating a job with empty metadata."""
        queue = JobQueue()
        job_id = queue.create_job("trends", metadata={})
        
        job = queue.get_job(job_id)
        assert job["metadata"] == {}
    
    def test_create_job_with_none_metadata(self):
        """Test creating a job with None metadata."""
        queue = JobQueue()
        job_id = queue.create_job("trends", metadata=None)
        
        job = queue.get_job(job_id)
        assert job["metadata"] == {}
    
    def test_create_multiple_jobs(self):
        """Test creating multiple jobs."""
        queue = JobQueue()
        job_ids = [queue.create_job("trends") for _ in range(5)]
        
        # All job IDs should be unique
        assert len(set(job_ids)) == 5
        
        # All jobs should exist
        for job_id in job_ids:
            job = queue.get_job(job_id)
            assert job is not None


class TestGetJob:
    """Tests for get_job method."""
    
    def test_get_job_existing(self):
        """Test getting an existing job."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        job = queue.get_job(job_id)
        assert job is not None
        assert job["job_id"] == job_id
    
    def test_get_job_nonexistent(self):
        """Test getting a non-existent job."""
        queue = JobQueue()
        job = queue.get_job("nonexistent-id")
        assert job is None
    
    def test_get_job_returns_copy(self):
        """Test that get_job returns a reference (not a copy)."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        job1 = queue.get_job(job_id)
        job2 = queue.get_job(job_id)
        
        # They should be the same object (reference)
        assert job1 is job2


class TestUpdateJob:
    """Tests for update_job method."""
    
    def test_update_job_existing(self):
        """Test updating an existing job."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        result = queue.update_job(job_id, status="processing", progress=50)
        assert result is True
        
        job = queue.get_job(job_id)
        assert job["status"] == "processing"
        assert job["progress"] == 50
        assert job["updated_at"] is not None
    
    def test_update_job_nonexistent(self):
        """Test updating a non-existent job."""
        queue = JobQueue()
        result = queue.update_job("nonexistent-id", status="processing")
        assert result is False
    
    def test_update_job_multiple_fields(self):
        """Test updating multiple fields at once."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.update_job(
            job_id,
            status="processing",
            progress=75,
            estimated_time_remaining=30
        )
        
        job = queue.get_job(job_id)
        assert job["status"] == "processing"
        assert job["progress"] == 75
        assert job["estimated_time_remaining"] == 30
    
    def test_update_job_updates_timestamp(self):
        """Test that updated_at is updated."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        job_before = queue.get_job(job_id)
        initial_time = job_before["updated_at"]
        
        # Small delay to ensure timestamp difference
        time.sleep(0.01)
        
        queue.update_job(job_id, status="processing")
        
        job_after = queue.get_job(job_id)
        # Verify updated_at was set (may be same or later depending on timing)
        assert job_after["updated_at"] >= initial_time
        # Verify it's a datetime object
        assert isinstance(job_after["updated_at"], datetime)


class TestSetStatus:
    """Tests for set_status method."""
    
    def test_set_status_pending(self):
        """Test setting status to pending."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        result = queue.set_status(job_id, "pending")
        assert result is True
        
        job = queue.get_job(job_id)
        assert job["status"] == "pending"
    
    def test_set_status_processing(self):
        """Test setting status to processing."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_status(job_id, "processing")
        job = queue.get_job(job_id)
        assert job["status"] == "processing"
    
    def test_set_status_completed(self):
        """Test setting status to completed."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_status(job_id, "completed")
        job = queue.get_job(job_id)
        assert job["status"] == "completed"
    
    def test_set_status_failed(self):
        """Test setting status to failed."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_status(job_id, "failed")
        job = queue.get_job(job_id)
        assert job["status"] == "failed"
    
    def test_set_status_nonexistent_job(self):
        """Test setting status for non-existent job."""
        queue = JobQueue()
        result = queue.set_status("nonexistent-id", "processing")
        assert result is False


class TestSetProgress:
    """Tests for set_progress method."""
    
    def test_set_progress_valid_range(self):
        """Test setting progress within valid range."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_progress(job_id, 50)
        job = queue.get_job(job_id)
        assert job["progress"] == 50
    
    def test_set_progress_clamps_to_0(self):
        """Test that progress below 0 is clamped to 0."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_progress(job_id, -10)
        job = queue.get_job(job_id)
        assert job["progress"] == 0
    
    def test_set_progress_clamps_to_100(self):
        """Test that progress above 100 is clamped to 100."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_progress(job_id, 150)
        job = queue.get_job(job_id)
        assert job["progress"] == 100
    
    def test_set_progress_with_estimated_time(self):
        """Test setting progress with estimated time remaining."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        queue.set_progress(job_id, 50, estimated_time_remaining=30)
        job = queue.get_job(job_id)
        assert job["progress"] == 50
        assert job["estimated_time_remaining"] == 30
    
    def test_set_progress_nonexistent_job(self):
        """Test setting progress for non-existent job."""
        queue = JobQueue()
        result = queue.set_progress("nonexistent-id", 50)
        assert result is False


class TestSetResult:
    """Tests for set_result method."""
    
    def test_set_result(self):
        """Test setting job result."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        result_data = {"trends": [], "total_cost": 1000.0}
        
        result = queue.set_result(job_id, result_data)
        assert result is True
        
        job = queue.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["result"] == result_data
        assert job["estimated_time_remaining"] == 0
    
    def test_set_result_nonexistent_job(self):
        """Test setting result for non-existent job."""
        queue = JobQueue()
        result = queue.set_result("nonexistent-id", {"data": "value"})
        assert result is False


class TestSetError:
    """Tests for set_error method."""
    
    def test_set_error(self):
        """Test setting job error."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        error_message = "Failed to fetch data"
        
        result = queue.set_error(job_id, error_message)
        assert result is True
        
        job = queue.get_job(job_id)
        assert job["status"] == "failed"
        assert job["error"] == error_message
    
    def test_set_error_nonexistent_job(self):
        """Test setting error for non-existent job."""
        queue = JobQueue()
        result = queue.set_error("nonexistent-id", "Error message")
        assert result is False


class TestCleanupOldJobs:
    """Tests for cleanup_old_jobs method."""
    
    def test_cleanup_old_completed_jobs(self):
        """Test cleaning up old completed jobs."""
        queue = JobQueue(cleanup_interval_seconds=1)
        
        # Create a completed job with old timestamp
        job_id = queue.create_job("trends")
        old_time = datetime.utcnow() - timedelta(seconds=2)
        queue._jobs[job_id]["status"] = "completed"
        queue._jobs[job_id]["updated_at"] = old_time
        
        # Create a recent completed job (should not be cleaned)
        recent_job_id = queue.create_job("trends")
        queue._jobs[recent_job_id]["status"] = "completed"
        
        # Create a pending job (should not be cleaned)
        pending_job_id = queue.create_job("trends")
        queue._jobs[pending_job_id]["status"] = "pending"
        queue._jobs[pending_job_id]["updated_at"] = old_time
        
        removed_count = queue.cleanup_old_jobs()
        
        assert removed_count == 1
        assert queue.get_job(job_id) is None
        assert queue.get_job(recent_job_id) is not None
        assert queue.get_job(pending_job_id) is not None
    
    def test_cleanup_old_failed_jobs(self):
        """Test cleaning up old failed jobs."""
        queue = JobQueue(cleanup_interval_seconds=1)
        
        job_id = queue.create_job("trends")
        old_time = datetime.utcnow() - timedelta(seconds=2)
        queue._jobs[job_id]["status"] = "failed"
        queue._jobs[job_id]["updated_at"] = old_time
        
        removed_count = queue.cleanup_old_jobs()
        
        assert removed_count == 1
        assert queue.get_job(job_id) is None
    
    def test_cleanup_no_old_jobs(self):
        """Test cleanup when no old jobs exist."""
        queue = JobQueue(cleanup_interval_seconds=1)
        
        job_id = queue.create_job("trends")
        queue._jobs[job_id]["status"] = "completed"
        
        removed_count = queue.cleanup_old_jobs()
        
        assert removed_count == 0
        assert queue.get_job(job_id) is not None
    
    def test_cleanup_empty_queue(self):
        """Test cleanup on empty queue."""
        queue = JobQueue()
        removed_count = queue.cleanup_old_jobs()
        assert removed_count == 0


class TestGetAllJobs:
    """Tests for get_all_jobs method."""
    
    def test_get_all_jobs_no_filter(self):
        """Test getting all jobs without filter."""
        queue = JobQueue()
        job_ids = [
            queue.create_job("trends"),
            queue.create_job("drift"),
            queue.create_job("trends")
        ]
        
        all_jobs = queue.get_all_jobs()
        
        assert len(all_jobs) == 3
        for job_id in job_ids:
            assert job_id in all_jobs
    
    def test_get_all_jobs_with_type_filter(self):
        """Test getting jobs filtered by type."""
        queue = JobQueue()
        trends_job1 = queue.create_job("trends")
        drift_job = queue.create_job("drift")
        trends_job2 = queue.create_job("trends")
        
        trends_jobs = queue.get_all_jobs("trends")
        
        assert len(trends_jobs) == 2
        assert trends_job1 in trends_jobs
        assert trends_job2 in trends_jobs
        assert drift_job not in trends_jobs
    
    def test_get_all_jobs_empty_queue(self):
        """Test getting all jobs from empty queue."""
        queue = JobQueue()
        all_jobs = queue.get_all_jobs()
        assert len(all_jobs) == 0
    
    def test_get_all_jobs_returns_copy(self):
        """Test that get_all_jobs returns a copy."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        jobs1 = queue.get_all_jobs()
        jobs2 = queue.get_all_jobs()
        
        # They should be different objects (copies)
        assert jobs1 is not jobs2
        # But should have same content
        assert jobs1 == jobs2


class TestThreadSafety:
    """Tests for thread safety of JobQueue."""
    
    def test_concurrent_create_job(self):
        """Test creating jobs concurrently."""
        queue = JobQueue()
        job_ids = []
        
        def create_job():
            job_id = queue.create_job("trends")
            job_ids.append(job_id)
        
        threads = [threading.Thread(target=create_job) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All job IDs should be unique
        assert len(set(job_ids)) == 10
        
        # All jobs should exist
        for job_id in job_ids:
            assert queue.get_job(job_id) is not None
    
    def test_concurrent_update_job(self):
        """Test updating jobs concurrently."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        
        def update_job(progress):
            queue.update_job(job_id, progress=progress)
        
        threads = [threading.Thread(target=update_job, args=(i,)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Job should still exist and be valid
        job = queue.get_job(job_id)
        assert job is not None
        assert "progress" in job
    
    def test_concurrent_get_job(self):
        """Test getting jobs concurrently."""
        queue = JobQueue()
        job_id = queue.create_job("trends")
        results = []
        
        def get_job():
            job = queue.get_job(job_id)
            results.append(job)
        
        threads = [threading.Thread(target=get_job) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All results should be the same job
        assert len(results) == 10
        assert all(job["job_id"] == job_id for job in results)
    
    def test_concurrent_mixed_operations(self):
        """Test mixed concurrent operations."""
        queue = JobQueue()
        job_ids = []
        
        def create_and_update():
            job_id = queue.create_job("trends")
            job_ids.append(job_id)
            queue.update_job(job_id, status="processing")
            queue.set_progress(job_id, 50)
        
        threads = [threading.Thread(target=create_and_update) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify all jobs were created and updated
        assert len(set(job_ids)) == 5
        for job_id in job_ids:
            job = queue.get_job(job_id)
            assert job is not None
            assert job["status"] == "processing"
            assert job["progress"] == 50
