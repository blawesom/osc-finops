"""Trends API endpoints."""
import threading
from typing import Optional
from flask import Blueprint, request, jsonify
from datetime import datetime

from backend.services.trend_service import calculate_trends_async
from backend.utils.date_validators import validate_date_range
from backend.services.job_queue import job_queue
from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth


trends_bp = Blueprint('trends', __name__)


from backend.utils.session_helpers import get_account_id_from_session


@trends_bp.route('/trends/async', methods=['POST'])
@require_auth
def submit_trends_job():
    """
    Submit async trend calculation job.
    Authentication required.
    
    Request body:
        - from_date: Start date (required, ISO format: YYYY-MM-DD)
        - to_date: End date (required, ISO format: YYYY-MM-DD)
        - granularity: "day", "week", or "month" (optional, default: "day")
        - region: Filter by region (optional, uses session region if not provided)
        - resource_type: Filter by resource type (optional)
        - force_refresh: Force refresh cache (optional: true/false)
    
    Returns:
        Job ID and initial status
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    # Get request body
    data = request.get_json() or {}
    from_date = data.get('from_date')
    to_date = data.get('to_date')
    granularity = data.get('granularity', 'day')
    region = data.get('region')
    resource_type = data.get('resource_type')
    force_refresh = data.get('force_refresh', False)
    
    # Validate required parameters
    if not from_date or not to_date:
        raise APIError("from_date and to_date are required", status_code=400)
    
    # Validate date range using centralized validator
    is_valid, error_msg = validate_date_range(from_date, to_date, granularity)
    if not is_valid:
        raise APIError(error_msg, status_code=400)
    
    # Validate granularity
    if granularity not in ['day', 'week', 'month']:
        raise APIError("granularity must be 'day', 'week', or 'month'", status_code=400)
    
    # Validate region if provided
    if region and region not in SUPPORTED_REGIONS:
        raise APIError(
            f"Unsupported region: {region}. Supported regions: {', '.join(SUPPORTED_REGIONS)}",
            status_code=400
        )
    
    # Get account_id from session
    account_id = get_account_id_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    # Use session region if region not specified
    query_region = region or session.region
    
    # Create job
    job_id = job_queue.create_job(
        job_type="trends",
        metadata={
            "from_date": from_date,
            "to_date": to_date,
            "granularity": granularity,
            "region": query_region,
            "resource_type": resource_type
        }
    )
    
    # Start background thread to process job
    def process_job():
        """Process job in background thread."""
        try:
            # Set status to processing
            job_queue.set_status(job_id, "processing")
            
            # Progress callback
            def progress_callback(progress: int, estimated_remaining: Optional[int]):
                job_queue.set_progress(job_id, progress, estimated_remaining)
            
            # Calculate trends
            result = calculate_trends_async(
                job_id=job_id,
                access_key=session.access_key,
                secret_key=session.secret_key,
                region=query_region,
                account_id=account_id,
                from_date=from_date,
                to_date=to_date,
                granularity=granularity,
                resource_type=resource_type,
                force_refresh=force_refresh,
                progress_callback=progress_callback
            )
            
            # Set result
            job_queue.set_result(job_id, result)
            
        except Exception as e:
            # Set error
            job_queue.set_error(job_id, str(e))
    
    # Start background thread
    thread = threading.Thread(target=process_job, daemon=True)
    thread.start()
    
    return jsonify({
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "message": "Job submitted successfully"
    }), 202


@trends_bp.route('/trends/jobs/<job_id>', methods=['GET'])
@require_auth
def get_job_status(job_id):
    """
    Get job status and results.
    Authentication required.
    
    Path parameters:
        - job_id: Job identifier
    
    Returns:
        Job status, progress, result (if completed), or error (if failed)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    # Get job
    job = job_queue.get_job(job_id)
    
    if not job:
        raise APIError("Job not found", status_code=404)
    
    # Verify job belongs to current user (optional security check)
    # For now, we'll allow any authenticated user to check any job
    
    # Format response
    response_data = {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "estimated_time_remaining": job.get("estimated_time_remaining"),
        "created_at": job["created_at"].isoformat() if isinstance(job["created_at"], datetime) else str(job["created_at"]),
        "updated_at": job["updated_at"].isoformat() if isinstance(job["updated_at"], datetime) else str(job["updated_at"])
    }
    
    # Add result if completed
    if job["status"] == "completed" and job["result"]:
        response_data["result"] = job["result"]
    
    # Add error if failed
    if job["status"] == "failed" and job["error"]:
        response_data["error"] = job["error"]
    
    return jsonify(response_data), 200

