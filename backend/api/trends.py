"""Trends API endpoints."""
import csv
import io
import threading
from typing import Optional
from flask import Blueprint, request, jsonify, Response
from datetime import datetime

from backend.services.trend_service import calculate_trends, calculate_trends_async, project_trend_until_date
from backend.services.job_queue import job_queue
from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth
from backend.database import SessionLocal
from backend.models.user import User


trends_bp = Blueprint('trends', __name__)


from backend.utils.session_helpers import get_account_id_from_session


@trends_bp.route('/trends', methods=['GET'])
@require_auth
def get_trends():
    """
    Get trend analysis for a date range.
    Authentication required.
    
    Query parameters:
        - from_date: Start date (required, ISO format: YYYY-MM-DD)
        - to_date: End date (required, ISO format: YYYY-MM-DD)
        - granularity: "day", "week", or "month" (optional, default: "day")
        - region: Filter by region (optional, uses session region if not provided)
        - resource_type: Filter by resource type (optional)
        - force_refresh: Force refresh cache (optional: true/false)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    # Get query parameters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    granularity = request.args.get('granularity', 'day')
    region = request.args.get('region')
    resource_type = request.args.get('resource_type')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    project_until = request.args.get('project_until')  # Optional projection end date
    
    # Validate required parameters
    if not from_date or not to_date:
        raise APIError("from_date and to_date parameters are required", status_code=400)
    
    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise APIError("Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    # Validate date range
    if from_date > to_date:
        raise APIError("from_date must be <= to_date", status_code=400)
    
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
    
    try:
        # Calculate trends
        trend_data = calculate_trends(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            granularity=granularity,
            resource_type=resource_type,
            force_refresh=force_refresh
        )
        
        # Project trend until specified date if requested
        if project_until:
            try:
                datetime.strptime(project_until, "%Y-%m-%d")
                if project_until > to_date:
                    trend_data = project_trend_until_date(trend_data, project_until)
            except ValueError:
                # Invalid date format, ignore projection
                pass
        
        return jsonify({
            "success": True,
            "data": trend_data,
            "metadata": {
                "from_date": from_date,
                "to_date": project_until or to_date,
                "region": query_region,
                "granularity": granularity,
                "resource_type": resource_type,
                "projected": bool(project_until)
            }
        }), 200
    
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to calculate trends: {str(e)}", status_code=500)


@trends_bp.route('/trends/export', methods=['GET'])
@require_auth
def export_trends():
    """
    Export trend data to CSV or JSON.
    Authentication required.
    
    Query parameters:
        - Same as /trends endpoint
        - format: "csv" or "json" (required)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    export_format = request.args.get('format', 'json').lower()
    
    if export_format not in ['csv', 'json']:
        raise APIError("format must be 'csv' or 'json'", status_code=400)
    
    # Get trend data using same logic as main endpoint
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    granularity = request.args.get('granularity', 'day')
    region = request.args.get('region')
    resource_type = request.args.get('resource_type')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    if not from_date or not to_date:
        raise APIError("from_date and to_date parameters are required", status_code=400)
    
    # Get account_id from session
    account_id = get_account_id_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    query_region = region or session.region
    
    try:
        # Calculate trends
        trend_data = calculate_trends(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            granularity=granularity,
            resource_type=resource_type,
            force_refresh=force_refresh
        )
        
        periods = trend_data.get("periods", [])
        
        if export_format == 'csv':
            # Generate CSV
            output = io.StringIO()
            if periods:
                fieldnames = ["period", "from_date", "to_date", "cost", "value", "entry_count"]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(periods)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=trends_{from_date}_to_{to_date}.csv'
                }
            )
        else:
            # Return JSON
            return jsonify({
                "success": True,
                "data": trend_data
            }), 200
    
    except Exception as e:
        raise APIError(f"Failed to export trends: {str(e)}", status_code=500)


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
    
    # Validate date format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise APIError("Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    # Validate date range
    if from_date > to_date:
        raise APIError("from_date must be <= to_date", status_code=400)
    
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

