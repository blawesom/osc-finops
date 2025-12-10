"""Simple in-memory job queue for async processing."""
import uuid
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta


class JobQueue:
    """Simple in-memory job queue with thread-safe operations."""
    
    def __init__(self, cleanup_interval_seconds: int = 3600):
        """
        Initialize job queue.
        
        Args:
            cleanup_interval_seconds: How long to keep completed jobs (default: 1 hour)
        """
        self._jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.cleanup_interval_seconds = cleanup_interval_seconds
    
    def create_job(self, job_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a new job and return job_id.
        
        Args:
            job_type: Type of job (e.g., "trends", "drift")
            metadata: Optional metadata to store with job
        
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": job_type,
                "status": "pending",
                "progress": 0,
                "result": None,
                "error": None,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
                "estimated_time_remaining": None
            }
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job dictionary or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs) -> bool:
        """
        Update job fields.
        
        Args:
            job_id: Job identifier
            **kwargs: Fields to update (status, progress, result, error, etc.)
        
        Returns:
            True if job was updated, False if not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            job.update(kwargs)
            job["updated_at"] = datetime.utcnow()
            
            return True
    
    def set_status(self, job_id: str, status: str) -> bool:
        """
        Set job status.
        
        Args:
            job_id: Job identifier
            status: New status ("pending", "processing", "completed", "failed")
        
        Returns:
            True if job was updated, False if not found
        """
        return self.update_job(job_id, status=status)
    
    def set_progress(self, job_id: str, progress: int, estimated_time_remaining: Optional[int] = None) -> bool:
        """
        Update job progress.
        
        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            estimated_time_remaining: Estimated seconds remaining (optional)
        
        Returns:
            True if job was updated, False if not found
        """
        update_data = {"progress": max(0, min(100, progress))}
        if estimated_time_remaining is not None:
            update_data["estimated_time_remaining"] = estimated_time_remaining
        
        return self.update_job(job_id, **update_data)
    
    def set_result(self, job_id: str, result: Dict) -> bool:
        """
        Set job result and mark as completed.
        
        Args:
            job_id: Job identifier
            result: Result data
        
        Returns:
            True if job was updated, False if not found
        """
        return self.update_job(
            job_id,
            status="completed",
            progress=100,
            result=result,
            estimated_time_remaining=0
        )
    
    def set_error(self, job_id: str, error_message: str) -> bool:
        """
        Set job error and mark as failed.
        
        Args:
            job_id: Job identifier
            error_message: Error message
        
        Returns:
            True if job was updated, False if not found
        """
        return self.update_job(
            job_id,
            status="failed",
            error=error_message
        )
    
    def cleanup_old_jobs(self) -> int:
        """
        Remove completed/failed jobs older than cleanup_interval_seconds.
        
        Returns:
            Number of jobs removed
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=self.cleanup_interval_seconds)
        
        jobs_to_remove = []
        
        with self._lock:
            for job_id, job in self._jobs.items():
                if job["status"] in ("completed", "failed"):
                    if job["updated_at"] < cutoff_time:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                self._jobs.pop(job_id, None)
        
        return len(jobs_to_remove)
    
    def get_all_jobs(self, job_type: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get all jobs, optionally filtered by type.
        
        Args:
            job_type: Optional job type filter
        
        Returns:
            Dictionary of job_id -> job data
        """
        with self._lock:
            if job_type:
                return {
                    job_id: job
                    for job_id, job in self._jobs.items()
                    if job.get("job_type") == job_type
                }
            return self._jobs.copy()


# Global job queue instance
job_queue = JobQueue()

