"""Budget API endpoints."""
from flask import Blueprint, request, jsonify
from datetime import datetime

from backend.services.budget_service import (
    create_budget,
    get_budgets,
    get_budget,
    update_budget,
    delete_budget,
    calculate_budget_status,
    get_budget_periods
)
from backend.utils.errors import APIError
from backend.middleware.auth_middleware import require_auth
from backend.database import SessionLocal
from backend.models.user import User
from backend.utils.session_helpers import get_user_id_from_session, get_account_id_from_session


budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/budgets', methods=['POST'])
@require_auth
def create_budget_endpoint():
    """
    Create a new budget.
    Authentication required.
    
    Request body:
        - name: Budget name (required)
        - amount: Budget amount per period (required, > 0)
        - period_type: Period type - "monthly", "quarterly", or "yearly" (required)
        - start_date: Start date (required, ISO format: YYYY-MM-DD)
        - end_date: End date (optional, ISO format: YYYY-MM-DD)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    data = request.get_json() or {}
    
    # Validate required fields
    name = data.get('name')
    if not name:
        raise APIError("name is required", status_code=400)
    
    amount = data.get('amount')
    if amount is None:
        raise APIError("amount is required", status_code=400)
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise APIError("amount must be a number", status_code=400)
    
    period_type = data.get('period_type')
    if not period_type:
        raise APIError("period_type is required", status_code=400)
    
    start_date = data.get('start_date')
    if not start_date:
        raise APIError("start_date is required", status_code=400)
    
    end_date = data.get('end_date')  # Optional
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise APIError("Invalid date format. Use YYYY-MM-DD", status_code=400)
    
    try:
        budget = create_budget(
            user_id=user_id,
            name=name,
            amount=amount,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "success": True,
            "data": budget.to_dict()
        }), 201
    
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except Exception as e:
        raise APIError(f"Failed to create budget: {str(e)}", status_code=500)


@budget_bp.route('/budgets', methods=['GET'])
@require_auth
def list_budgets_endpoint():
    """
    List all budgets for the authenticated user.
    Authentication required.
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    try:
        budgets = get_budgets(user_id)
        return jsonify({
            "success": True,
            "data": [budget.to_dict() for budget in budgets]
        }), 200
    
    except Exception as e:
        raise APIError(f"Failed to list budgets: {str(e)}", status_code=500)


@budget_bp.route('/budgets/<budget_id>', methods=['GET'])
@require_auth
def get_budget_endpoint(budget_id):
    """
    Get a budget by ID.
    Authentication required.
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    try:
        budget = get_budget(budget_id, user_id)
        if not budget:
            raise APIError("Budget not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": budget.to_dict()
        }), 200
    
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to get budget: {str(e)}", status_code=500)


@budget_bp.route('/budgets/<budget_id>', methods=['PUT'])
@require_auth
def update_budget_endpoint(budget_id):
    """
    Update a budget.
    Authentication required.
    
    Request body (all fields optional):
        - name: Budget name
        - amount: Budget amount per period (> 0)
        - period_type: Period type - "monthly", "quarterly", or "yearly"
        - start_date: Start date (ISO format: YYYY-MM-DD)
        - end_date: End date (ISO format: YYYY-MM-DD, or null to remove)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    data = request.get_json() or {}
    
    # Validate date format if provided
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise APIError("Invalid start_date format. Use YYYY-MM-DD", status_code=400)
    
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise APIError("Invalid end_date format. Use YYYY-MM-DD", status_code=400)
    
    # Validate amount if provided
    amount = data.get('amount')
    if amount is not None:
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise APIError("amount must be a number", status_code=400)
    
    try:
        budget = update_budget(
            budget_id=budget_id,
            user_id=user_id,
            name=data.get('name'),
            amount=amount,
            period_type=data.get('period_type'),
            start_date=start_date,
            end_date=end_date
        )
        
        if not budget:
            raise APIError("Budget not found", status_code=404)
        
        return jsonify({
            "success": True,
            "data": budget.to_dict()
        }), 200
    
    except ValueError as e:
        raise APIError(str(e), status_code=400)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to update budget: {str(e)}", status_code=500)


@budget_bp.route('/budgets/<budget_id>', methods=['DELETE'])
@require_auth
def delete_budget_endpoint(budget_id):
    """
    Delete a budget.
    Authentication required.
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    try:
        deleted = delete_budget(budget_id, user_id)
        if not deleted:
            raise APIError("Budget not found", status_code=404)
        
        return jsonify({
            "success": True,
            "message": "Budget deleted successfully"
        }), 200
    
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to delete budget: {str(e)}", status_code=500)


@budget_bp.route('/budgets/<budget_id>/status', methods=['GET'])
@require_auth
def get_budget_status_endpoint(budget_id):
    """
    Get budget status (spent vs. budget) for a date range.
    Authentication required.
    
    Query parameters:
        - from_date: Start date (required, ISO format: YYYY-MM-DD)
        - to_date: End date (required, ISO format: YYYY-MM-DD)
        - force_refresh: Force refresh consumption cache (optional: true/false)
    """
    session = getattr(request, 'session', None)
    if not session:
        raise APIError("Authentication required", status_code=401)
    
    user_id = get_user_id_from_session()
    if not user_id:
        raise APIError("Could not retrieve user information", status_code=401)
    
    account_id = get_account_id_from_session()
    if not account_id:
        raise APIError("Could not retrieve account information", status_code=401)
    
    # Get query parameters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
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
    
    try:
        # Get budget
        budget = get_budget(budget_id, user_id)
        if not budget:
            raise APIError("Budget not found", status_code=404)
        
        # Calculate budget status
        status = calculate_budget_status(
            budget=budget,
            access_key=session.access_key,
            secret_key=session.secret_key,
            region=session.region,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh
        )
        
        return jsonify({
            "success": True,
            "data": status
        }), 200
    
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Failed to get budget status: {str(e)}", status_code=500)

