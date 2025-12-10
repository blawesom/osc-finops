"""Cost API endpoints."""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from datetime import datetime

from backend.services.cost_service import get_current_costs
from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth


cost_bp = Blueprint('cost', __name__)


from backend.utils.session_helpers import get_account_id_from_session


@cost_bp.route('/cost', methods=['GET'])
@require_auth
def get_cost():
    """
    Get current costs for all resources.
    
    Query parameters:
    - region: Region name (optional, uses session region if not provided)
    - tag_key: Tag key to filter by (optional)
    - tag_value: Tag value to filter by (optional)
    - include_oos: Include OOS buckets (default: false, can take up to 10 minutes)
    - format: Response format (json/human/csv/ods, default: json)
    - force_refresh: Force refresh cache (default: false)
    """
    try:
        # Get session info
        session = getattr(request, 'session', None)
        if not session:
            raise APIError("Session not found", status_code=401)
        
        # Get account_id from user
        account_id = get_account_id_from_session()
        if not account_id:
            raise APIError("Could not retrieve account information", status_code=500)
        
        # Get query parameters
        query_region = request.args.get('region', session.region)
        tag_key = request.args.get('tag_key')
        tag_value = request.args.get('tag_value')
        include_oos = request.args.get('include_oos', 'false').lower() == 'true'
        format_type = request.args.get('format', 'json').lower()
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # Validate region
        if query_region not in SUPPORTED_REGIONS:
            raise APIError(f"Unsupported region: {query_region}", status_code=400)
        
        # Validate tag parameters (both or neither)
        if (tag_key and not tag_value) or (tag_value and not tag_key):
            raise APIError("Both tag_key and tag_value must be provided", status_code=400)
        
        # Get current costs
        cost_data = get_current_costs(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            tag_key=tag_key,
            tag_value=tag_value,
            include_oos=include_oos,
            force_refresh=force_refresh
        )
        
        # Format response based on format_type
        if format_type == 'human':
            return format_human_readable(cost_data), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        elif format_type == 'csv':
            return format_csv(cost_data), 200, {'Content-Type': 'text/csv; charset=utf-8'}
        elif format_type == 'ods':
            # ODS export deferred for now, return JSON
            return jsonify({
                "success": True,
                "message": "ODS export not yet implemented, returning JSON",
                "data": cost_data
            }), 200
        else:  # json (default)
            return jsonify({
                "success": True,
                "data": cost_data,
                "metadata": {
                    "fetched_at": cost_data.get("fetched_at"),
                    "region": query_region,
                    "currency": cost_data.get("currency", "EUR"),
                    "filters": {
                        "tag_key": tag_key,
                        "tag_value": tag_value
                    },
                    "include_oos": include_oos
                }
            }), 200
    
    except APIError as e:
        return jsonify({"success": False, "error": {"message": str(e), "code": e.code}}), e.status_code
    except Exception as e:
        return jsonify({"success": False, "error": {"message": str(e), "code": "INTERNAL_ERROR"}}), 500


@cost_bp.route('/cost/export', methods=['GET'])
@require_auth
def export_cost():
    """
    Export current costs.
    
    Query parameters: same as /cost endpoint
    - format: Export format (csv/ods/json, default: csv)
    """
    try:
        # Get session info
        session = getattr(request, 'session', None)
        if not session:
            raise APIError("Session not found", status_code=401)
        
        # Get account_id from user
        account_id = get_account_id_from_session()
        if not account_id:
            raise APIError("Could not retrieve account information", status_code=500)
        
        # Get query parameters
        query_region = request.args.get('region', session.region)
        tag_key = request.args.get('tag_key')
        tag_value = request.args.get('tag_value')
        include_oos = request.args.get('include_oos', 'false').lower() == 'true'
        format_type = request.args.get('format', 'csv').lower()
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # Validate region
        if query_region not in SUPPORTED_REGIONS:
            raise APIError(f"Unsupported region: {query_region}", status_code=400)
        
        # Validate tag parameters
        if (tag_key and not tag_value) or (tag_value and not tag_key):
            raise APIError("Both tag_key and tag_value must be provided", status_code=400)
        
        # Get current costs
        cost_data = get_current_costs(
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=query_region,
            account_id=account_id,
            tag_key=tag_key,
            tag_value=tag_value,
            include_oos=include_oos,
            force_refresh=force_refresh
        )
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_export_{query_region}_{timestamp}"
        
        # Format and return
        if format_type == 'csv':
            csv_data = format_csv(cost_data)
            filename += '.csv'
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
        elif format_type == 'ods':
            # ODS export deferred
            return jsonify({
                "success": False,
                "error": {"message": "ODS export not yet implemented", "code": "NOT_IMPLEMENTED"}
            }), 501
        else:  # json
            json_data = jsonify(cost_data).get_data(as_text=True)
            filename += '.json'
            return Response(
                json_data,
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
    
    except APIError as e:
        return jsonify({"success": False, "error": {"message": str(e), "code": e.code}}), e.status_code
    except Exception as e:
        return jsonify({"success": False, "error": {"message": str(e), "code": "INTERNAL_ERROR"}}), 500


def format_human_readable(cost_data: dict) -> str:
    """
    Format cost data as human-readable text.
    
    Args:
        cost_data: Cost data dictionary
    
    Returns:
        Human-readable text string
    """
    totals = cost_data.get("totals", {})
    breakdown_by_type = cost_data.get("breakdown", {}).get("by_resource_type", {})
    breakdown_by_category = cost_data.get("breakdown", {}).get("by_category", {})
    currency = cost_data.get("currency", "EUR")
    region = cost_data.get("region", "unknown")
    
    output = []
    output.append("=" * 80)
    output.append(f"Current Cost Evaluation - {region}")
    output.append("=" * 80)
    output.append("")
    
    # Totals
    output.append("TOTALS")
    output.append("-" * 80)
    output.append(f"Cost per hour:  {currency} {totals.get('cost_per_hour', 0):.4f}")
    output.append(f"Cost per month: {currency} {totals.get('cost_per_month', 0):.2f}")
    output.append(f"Cost per year:  {currency} {totals.get('cost_per_year', 0):.2f}")
    output.append(f"Resource count: {totals.get('resource_count', 0)}")
    output.append(f"Resource types: {totals.get('resource_type_count', 0)}")
    output.append("")
    
    # Breakdown by resource type
    if breakdown_by_type:
        output.append("BREAKDOWN BY RESOURCE TYPE")
        output.append("-" * 80)
        for resource_type, values in sorted(breakdown_by_type.items()):
            output.append(f"{resource_type:20} | Count: {values.get('count', 0):4} | "
                         f"Hour: {currency} {values.get('cost_per_hour', 0):10.4f} | "
                         f"Month: {currency} {values.get('cost_per_month', 0):10.2f}")
        output.append("")
    
    # Breakdown by category
    if breakdown_by_category:
        output.append("BREAKDOWN BY CATEGORY")
        output.append("-" * 80)
        for category, values in sorted(breakdown_by_category.items()):
            output.append(f"{category:20} | Count: {values.get('count', 0):4} | "
                         f"Hour: {currency} {values.get('cost_per_hour', 0):10.4f} | "
                         f"Month: {currency} {values.get('cost_per_month', 0):10.2f}")
        output.append("")
    
    # Top resources (by cost)
    resources = cost_data.get("resources", [])
    if resources:
        sorted_resources = sorted(resources, key=lambda x: x.get("cost_per_month", 0), reverse=True)
        output.append("TOP 10 RESOURCES BY COST (per month)")
        output.append("-" * 80)
        for i, resource in enumerate(sorted_resources[:10], 1):
            resource_id = resource.get("resource_id", "unknown")
            resource_type = resource.get("resource_type", "unknown")
            cost = resource.get("cost_per_month", 0)
            output.append(f"{i:2}. {resource_type:15} | {resource_id:30} | {currency} {cost:10.2f}")
    
    output.append("")
    output.append("=" * 80)
    
    return "\n".join(output)


def format_csv(cost_data: dict) -> str:
    """
    Format cost data as CSV.
    
    Args:
        cost_data: Cost data dictionary
    
    Returns:
        CSV string
    """
    resources = cost_data.get("resources", [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Resource ID",
        "Resource Type",
        "Region",
        "Zone",
        "Cost per Hour",
        "Cost per Month",
        "Cost per Year",
        "Specs (JSON)"
    ])
    
    # Data rows
    for resource in resources:
        specs_json = str(resource.get("specs", {}))
        writer.writerow([
            resource.get("resource_id", ""),
            resource.get("resource_type", ""),
            resource.get("region", ""),
            resource.get("zone", ""),
            resource.get("cost_per_hour", 0),
            resource.get("cost_per_month", 0),
            resource.get("cost_per_year", 0),
            specs_json
        ])
    
    return output.getvalue()

