"""Quote API endpoints."""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from backend.services.quote_service_db import QuoteServiceDB
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth
from backend.database import SessionLocal
from backend.utils.session_helpers import get_user_id_from_session

quote_bp = Blueprint('quote', __name__)


@quote_bp.route('/quotes', methods=['POST'])
@require_auth
def create_quote():
    """
    Create a new quote.
    Requires authentication.
    New quote becomes active, previous active quote is saved.
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    name = data.get('name', 'Untitled Quote')
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.create_quote(db, name, user_id)
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 201
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to create quote: {str(e)}", status_code=500)
    finally:
        db.close()


@quote_bp.route('/quotes', methods=['GET'])
@require_auth
def list_quotes():
    """
    List all user's quotes (summary).
    Requires authentication.
    Returns only quotes owned by the authenticated user.
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        quotes = QuoteServiceDB.list_quotes(db, user_id)
        return jsonify({
            "success": True,
            "data": quotes
        }), 200
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>', methods=['GET'])
@require_auth
def get_quote(quote_id):
    """
    Get quote by ID.
    Requires authentication.
    Verifies ownership.
    If loading a saved quote, it becomes active and previous active is saved.
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            raise APIError("Quote not found", status_code=404)
        
        # If quote is saved, loading it makes it active
        if quote.status == "saved":
            quote = QuoteServiceDB.load_quote(db, quote_id, user_id)
        
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 200
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>', methods=['PUT'])
@require_auth
def update_quote(quote_id):
    """
    Update quote configuration, name, or status.
    Requires authentication.
    Verifies ownership.
    Handles status transitions (active/saved).
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.update_quote(
            db,
            quote_id,
            user_id=user_id,
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
        db.rollback()
        raise APIError(f"Failed to update quote: {str(e)}", status_code=500)
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>', methods=['DELETE'])
@require_auth
def delete_quote(quote_id):
    """
    Delete quote.
    Requires authentication.
    Verifies ownership.
    If deleting active quote, automatically loads next saved quote.
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        replacement = QuoteServiceDB.delete_quote_and_get_replacement(db, quote_id, user_id)
        
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
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    data = request.get_json() or {}
    
    # Generate item ID if not provided
    if 'id' not in data:
        import uuid
        data['id'] = str(uuid.uuid4())
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.add_item(db, quote_id, data, user_id)
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
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.remove_item(db, quote_id, item_id, user_id)
        if not quote:
            raise APIError("Quote or item not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": quote.to_dict()
        }), 200
    finally:
        db.close()


@quote_bp.route('/quotes/<quote_id>/export/csv', methods=['GET'])
@require_auth
def export_quote_csv(quote_id):
    """
    Export quote to CSV.
    Requires authentication.
    Verifies ownership.
    """
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Authentication required", status_code=401)
    
    db = SessionLocal()
    try:
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            raise APIError("Quote not found", status_code=404)
        
        quote_dict = quote.to_dict()
        calculation = quote_dict['calculation']
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['OSC-FinOps Quote Export'])
        writer.writerow(['Quote Name:', quote.name])
        writer.writerow(['Created:', quote.created_at.isoformat() if quote.created_at else ''])
        writer.writerow(['Updated:', quote.updated_at.isoformat() if quote.updated_at else ''])
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
    finally:
        db.close()

