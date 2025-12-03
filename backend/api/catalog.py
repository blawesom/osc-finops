"""Catalog API endpoints."""
from flask import Blueprint, request, jsonify
from backend.services.catalog_service import get_catalog, filter_catalog_by_category, get_catalog_categories
from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.errors import APIError

catalog_bp = Blueprint('catalog', __name__)


@catalog_bp.route('/catalog', methods=['GET'])
def get_catalog_endpoint():
    """
    Get catalog for a region.
    No authentication required (ReadPublicCatalog API doesn't require auth).
    
    Query parameters:
        - region: Region name (required)
        - category: Filter by category (optional: Compute, Storage, Network, Licence)
        - force_refresh: Force refresh cache (optional: true/false)
    """
    region = request.args.get('region')
    category = request.args.get('category')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    if not region:
        raise APIError("Region parameter is required", status_code=400)
    
    if region not in SUPPORTED_REGIONS:
        raise APIError(
            f"Unsupported region: {region}. Supported regions: {', '.join(SUPPORTED_REGIONS)}",
            status_code=400
        )
    
    try:
        catalog = get_catalog(region, force_refresh=force_refresh)
        
        # Filter by category if specified
        if category:
            filtered_entries = filter_catalog_by_category(catalog, category)
            catalog = {
                **catalog,
                "entries": filtered_entries,
                "entry_count": len(filtered_entries),
                "filtered_by": category
            }
        
        return jsonify({
            "success": True,
            "data": catalog
        }), 200
    
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to fetch catalog: {str(e)}", status_code=500)


@catalog_bp.route('/catalog/categories', methods=['GET'])
def get_categories_endpoint():
    """
    Get available categories for a region.
    No authentication required.
    
    Query parameters:
        - region: Region name (required)
    """
    region = request.args.get('region')
    
    if not region:
        raise APIError("Region parameter is required", status_code=400)
    
    if region not in SUPPORTED_REGIONS:
        raise APIError(
            f"Unsupported region: {region}. Supported regions: {', '.join(SUPPORTED_REGIONS)}",
            status_code=400
        )
    
    try:
        catalog = get_catalog(region)
        categories = get_catalog_categories(catalog)
        
        return jsonify({
            "success": True,
            "data": {
                "region": region,
                "categories": categories
            }
        }), 200
    
    except Exception as e:
        raise APIError(f"Failed to fetch categories: {str(e)}", status_code=500)

