"""Consumption API endpoints."""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from datetime import datetime

from backend.services.consumption_service import (
    get_consumption,
    aggregate_by_granularity,
    filter_consumption,
    aggregate_by_dimension,
    calculate_totals,
    get_top_cost_drivers
)
from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth
from backend.database import SessionLocal
from backend.models.user import User


consumption_bp = Blueprint('consumption', __name__)


def get_owner_from_session():
    """Get account_id from session."""
    session = getattr(request, 'session', None)
    if not session:
        return None
    
    # Get account_id from user_id in session
    db = SessionLocal()
    try:
        if hasattr(session, 'user_id') and session.user_id:
            user = db.query(User).filter(User.user_id == session.user_id).first()
            if user:
                return user.account_id
    except Exception:
        pass
    finally:
        db.close()
    
    return None


@consumption_bp.route('/consumption', methods=['GET'])
@require_auth
def get_consumption_endpoint():
    """
    Get consumption data for a date range.
    Authentication required.
    
    Query parameters:
        - from_date: Start date (required, ISO format: YYYY-MM-DD)
        - to_date: End date (required, ISO format: YYYY-MM-DD)
        - granularity: "day", "week", "month" (optional, default: "day")
        - region: Filter by region (optional)
        - service: Filter by service name (optional)
        - resource_type: Filter by resource type (optional)
        - aggregate_by: "resource_type", "region", "tag" (optional)
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
    service = request.args.get('service')
    resource_type = request.args.get('resource_type')
    aggregate_by = request.args.get('aggregate_by')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
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
    account_id = get_owner_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    # Use session region if region not specified
    query_region = region or session.region
    
    try:
        # Get consumption data
        consumption_data = get_consumption(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh
        )
        
        # Apply filters
        if region or service or resource_type:
            consumption_data = filter_consumption(
                consumption_data,
                region=region,
                service=service,
                resource_type=resource_type
            )
        
        # Aggregate by granularity if specified
        if granularity != 'day' or aggregate_by:
            if aggregate_by:
                # Aggregate by dimension
                aggregated = aggregate_by_dimension(consumption_data, aggregate_by)
                consumption_data = {
                    **consumption_data,
                    "entries": aggregated,
                    "aggregated_by": aggregate_by
                }
            else:
                # Aggregate by granularity
                aggregated = aggregate_by_granularity(consumption_data, granularity)
                consumption_data = {
                    **consumption_data,
                    "entries": aggregated,
                    "granularity": granularity
                }
        
        # Calculate totals
        totals = calculate_totals(consumption_data)
        
        # Get currency from consumption data if available
        currency = consumption_data.get("currency")
        
        return jsonify({
            "success": True,
            "data": consumption_data,
            "totals": totals,
            "metadata": {
                "from_date": from_date,
                "to_date": to_date,
                "region": query_region,
                "currency": currency,
                "granularity": granularity,
                "filters": {
                    "region": region,
                    "service": service,
                    "resource_type": resource_type
                },
                "aggregate_by": aggregate_by
            }
        }), 200
    
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to fetch consumption: {str(e)}", status_code=500)


@consumption_bp.route('/consumption/export', methods=['GET'])
@require_auth
def export_consumption_endpoint():
    """
    Export consumption data to CSV or JSON.
    Authentication required.
    
    Query parameters:
        - Same as /consumption endpoint
        - format: "csv" or "json" (required)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    export_format = request.args.get('format', 'json').lower()
    
    if export_format not in ['csv', 'json']:
        raise APIError("format must be 'csv' or 'json'", status_code=400)
    
    # Get consumption data using same logic as main endpoint
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    granularity = request.args.get('granularity', 'day')
    region = request.args.get('region')
    service = request.args.get('service')
    resource_type = request.args.get('resource_type')
    aggregate_by = request.args.get('aggregate_by')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    if not from_date or not to_date:
        raise APIError("from_date and to_date parameters are required", status_code=400)
    
    # Get account_id from session
    account_id = get_owner_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    query_region = region or session.region
    
    try:
        # Get consumption data
        consumption_data = get_consumption(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh
        )
        
        # Apply filters
        if region or service or resource_type:
            consumption_data = filter_consumption(
                consumption_data,
                region=region,
                service=service,
                resource_type=resource_type
            )
        
        # Aggregate if needed
        if aggregate_by:
            aggregated = aggregate_by_dimension(consumption_data, aggregate_by)
            consumption_data = {
                **consumption_data,
                "entries": aggregated
            }
        elif granularity != 'day':
            aggregated = aggregate_by_granularity(consumption_data, granularity)
            consumption_data = {
                **consumption_data,
                "entries": aggregated
            }
        
        entries = consumption_data.get("entries", [])
        
        if export_format == 'csv':
            # Generate CSV
            output = io.StringIO()
            if entries:
                # Get all unique keys from entries
                fieldnames = set()
                for entry in entries:
                    fieldnames.update(entry.keys())
                fieldnames = sorted(fieldnames)
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(entries)
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=consumption_{from_date}_to_{to_date}.csv'
                }
            )
        else:
            # Return JSON
            return jsonify({
                "success": True,
                "data": consumption_data
            }), 200
    
    except Exception as e:
        raise APIError(f"Failed to export consumption: {str(e)}", status_code=500)


@consumption_bp.route('/consumption/top-drivers', methods=['GET'])
@require_auth
def get_top_drivers_endpoint():
    """
    Get top cost drivers for consumption data.
    Authentication required.
    
    Query parameters:
        - Same as /consumption endpoint
        - limit: Number of top drivers (optional, default: 10)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    # Get query parameters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    region = request.args.get('region')
    service = request.args.get('service')
    resource_type = request.args.get('resource_type')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 10))
    
    if not from_date or not to_date:
        raise APIError("from_date and to_date parameters are required", status_code=400)
    
    # Get account_id from session
    account_id = get_owner_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    query_region = region or session.region
    
    try:
        # Get consumption data
        consumption_data = get_consumption(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh
        )
        
        # Apply filters
        if region or service or resource_type:
            consumption_data = filter_consumption(
                consumption_data,
                region=region,
                service=service,
                resource_type=resource_type
            )
        
        # Get top drivers
        top_drivers = get_top_cost_drivers(consumption_data, limit=limit)
        
        # Get currency from consumption data if available
        currency = consumption_data.get("currency")
        
        return jsonify({
            "success": True,
            "data": {
                "top_drivers": top_drivers,
                "limit": limit,
                "currency": currency
            },
            "metadata": {
                "region": query_region
            }
        }), 200
    
    except Exception as e:
        raise APIError(f"Failed to fetch top drivers: {str(e)}", status_code=500)

