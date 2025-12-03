"""Quote API endpoints."""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from backend.services.quote_service import quote_manager
from backend.services.quote_service_db import QuoteServiceDB
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth
from backend.database import SessionLocal

quote_bp = Blueprint('quote', __name__)


def get_owner_from_session():
    """Get owner identifier from session (user_id from database)."""
    if hasattr(request, 'session') and request.session:
        # Try to get user_id from session (database-backed)
        if hasattr(request.session, 'user_id') and request.session.user_id:
            return request.session.user_id
        # Fallback to access_key for backward compatibility
        return request.session.access_key
    return None


@quote_bp.route('/quotes', methods=['POST'])
@require_auth
def create_quote():
    """
    Create a new quote.
    Requires authentication.
    New quote becomes active, previous active quote is saved.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    name = data.get('name', 'Untitled Quote')
    
    quote = quote_manager.create_quote(name, owner=owner)
    
    return jsonify({
        "success": True,
        "data": quote.to_dict()
    }), 201


@quote_bp.route('/quotes', methods=['GET'])
@require_auth
def list_quotes():
    """
    List all user's quotes (summary).
    Requires authentication.
    Returns only quotes owned by the authenticated user.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    quotes = quote_manager.list_quotes(owner=owner)
    
    return jsonify({
        "success": True,
        "data": quotes
    }), 200


@quote_bp.route('/quotes/<quote_id>', methods=['GET'])
@require_auth
def get_quote(quote_id):
    """
    Get quote by ID.
    Requires authentication.
    Verifies ownership.
    If loading a saved quote, it becomes active and previous active is saved.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    quote = quote_manager.get_quote(quote_id, owner=owner)
    
    if not quote:
        raise APIError("Quote not found", status_code=404)
    
    # If quote is saved, loading it makes it active
    if quote.status == "saved":
        quote = quote_manager.load_quote(quote_id, owner)
    
    return jsonify({
        "success": True,
        "data": quote.to_dict()
    }), 200


@quote_bp.route('/quotes/<quote_id>', methods=['PUT'])
@require_auth
def update_quote(quote_id):
    """
    Update quote configuration, name, or status.
    Requires authentication.
    Verifies ownership.
    Handles status transitions (active/saved).
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    
    try:
        quote = quote_manager.update_quote(
            quote_id,
            owner=owner,
            name=data.get('name'),
            status=data.get('status'),
            duration=data.get('duration'),
            duration_unit=data.get('duration_unit'),
            commitment_period=data.get('commitment_period'),
            global_discount_percent=data.get('global_discount_percent')
        )
        
        if not quote:
            raise APIError("Quote not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 200
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to update quote: {str(e)}", status_code=500)


@quote_bp.route('/quotes/<quote_id>', methods=['DELETE'])
@require_auth
def delete_quote(quote_id):
    """
    Delete quote.
    Requires authentication.
    Verifies ownership.
    If deleting active quote, automatically loads next saved quote.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        replacement = QuoteServiceDB.delete_quote_and_get_replacement(db, quote_id, owner)
        
        response_data = {
            "success": True,
            "message": "Quote deleted"
        }
        
        if replacement:
            response_data["replacement_quote"] = replacement.to_dict()
        
        return jsonify(response_data), 200
    except Exception as e:
        db.rollback()
        raise APIError(f"Failed to delete quote: {str(e)}", status_code=500)
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>/items', methods=['POST'])
@require_auth
def add_quote_item(quote_id):
    """
    Add item to quote.
    Requires authentication.
    Verifies ownership.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    
    # Generate item ID if not provided
    if 'id' not in data:
        import uuid
        data['id'] = str(uuid.uuid4())
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.add_item(db, quote_id, data, owner)
        if not quote:
            raise APIError("Quote not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 200
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        db.rollback()
        raise APIError(f"Failed to add item: {str(e)}", status_code=500)
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>/items/<item_id>', methods=['DELETE'])
@require_auth
def remove_quote_item(quote_id, item_id):
    """
    Remove item from quote.
    Requires authentication.
    Verifies ownership.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.remove_item(db, quote_id, item_id, owner)
        if not quote:
            raise APIError("Quote or item not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 200
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>/calculate', methods=['GET'])
@require_auth
def calculate_quote(quote_id):
    """
    Calculate quote totals.
    Requires authentication.
    Verifies ownership.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    quote = quote_manager.get_quote(quote_id, owner=owner)
    if not quote:
        raise APIError("Quote not found", status_code=404)
    
    calculation = quote.calculate()
    
    return jsonify({
        "success": True,
        "data": calculation
    }), 200


@quote_bp.route('/quotes/<quote_id>/export/csv', methods=['GET'])
@require_auth
def export_quote_csv(quote_id):
    """
    Export quote to CSV.
    Requires authentication.
    Verifies ownership.
    """
    owner = get_owner_from_session()
    if not owner:
        raise APIError("Authentication required", status_code=401)
    
    quote = quote_manager.get_quote(quote_id, owner=owner)
    if not quote:
        raise APIError("Quote not found", status_code=404)
    
    calculation = quote.calculate()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['OSC-FinOps Quote Export'])
    writer.writerow(['Quote Name:', quote.name])
    writer.writerow(['Created:', quote.created_at.isoformat()])
    writer.writerow(['Updated:', quote.updated_at.isoformat()])
    writer.writerow([])
    
    # Configuration
    writer.writerow(['Configuration'])
    writer.writerow(['Duration:', f"{quote.duration} {quote.duration_unit}"])
    writer.writerow(['Commitment Period:', quote.commitment_period or 'None'])
    writer.writerow(['Global Discount:', f"{quote.global_discount_percent}%"])
    writer.writerow([])
    
    # Items header
    writer.writerow([
        'Resource Name', 'Category', 'Quantity', 'Unit Price', 'Base Cost',
        'Commitment Discount', 'After Commitment', 'Global Discount', 'Final Cost'
    ])
    
    # Items
    for item in calculation['items']:
        resource_name = item.get('resource_name', item.get('name', 'Unknown'))
        category = item.get('resource_data', {}).get('Category', 'Unknown')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        base_cost = item.get('base_cost', 0)
        commitment_discount = item.get('commitment_discount_amount', 0)
        after_commitment = item.get('cost_after_commitment_discount', 0)
        global_discount = item.get('global_discount_amount', 0)
        final_cost = item.get('final_cost', 0)
        
        writer.writerow([
            resource_name, category, quantity, unit_price, base_cost,
            commitment_discount, after_commitment, global_discount, final_cost
        ])
    
    writer.writerow([])
    
    # Summary
    writer.writerow(['Summary'])
    writer.writerow(['Base Total:', calculation['summary']['base_total']])
    writer.writerow(['Commitment Discounts:', calculation['summary']['commitment_discounts']])
    writer.writerow(['Subtotal:', calculation['summary']['subtotal']])
    writer.writerow(['Global Discount:', calculation['summary']['global_discount']])
    writer.writerow(['Total:', calculation['summary']['total']])
    
    # Prepare response
    output.seek(0)
    filename = f"quote_{quote.name.replace(' ', '_')}_{quote.quote_id[:8]}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

