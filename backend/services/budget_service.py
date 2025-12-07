"""Budget service for managing budgets and calculating budget status."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from backend.database import SessionLocal
from backend.models.budget import Budget
from backend.models.user import User
from backend.services.consumption_service import get_consumption, aggregate_by_granularity
from backend.utils.error_logger import log_exception


def create_budget(
    user_id: str,
    name: str,
    amount: float,
    period_type: str,
    start_date: str,
    end_date: Optional[str] = None
) -> Budget:
    """
    Create a new budget.
    
    Args:
        user_id: User ID
        name: Budget name
        amount: Budget amount per period
        period_type: Period type (monthly, quarterly, yearly)
        start_date: Start date (ISO format: YYYY-MM-DD)
        end_date: Optional end date (ISO format: YYYY-MM-DD)
    
    Returns:
        Created Budget object
    
    Raises:
        ValueError: If validation fails
    """
    # Validate period_type
    if period_type not in ['monthly', 'quarterly', 'yearly']:
        raise ValueError("period_type must be 'monthly', 'quarterly', or 'yearly'")
    
    # Validate amount
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    
    # Validate dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = None
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            if end_dt <= start_dt:
                raise ValueError("end_date must be after start_date")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {str(e)}")
    
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Create budget
        budget = Budget(
            user_id=user_id,
            name=name,
            amount=amount,
            period_type=period_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
        return budget
    except Exception as e:
        db.rollback()
        log_exception(e)
        raise
    finally:
        db.close()


def get_budgets(user_id: str) -> List[Budget]:
    """
    Get all budgets for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        List of Budget objects
    """
    db = SessionLocal()
    try:
        budgets = db.query(Budget).filter(Budget.user_id == user_id).order_by(Budget.created_at.desc()).all()
        return budgets
    finally:
        db.close()


def get_budget(budget_id: str, user_id: str) -> Optional[Budget]:
    """
    Get a budget by ID (with ownership verification).
    
    Args:
        budget_id: Budget ID
        user_id: User ID for ownership verification
    
    Returns:
        Budget object or None if not found or not owned by user
    """
    db = SessionLocal()
    try:
        budget = db.query(Budget).filter(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        ).first()
        return budget
    finally:
        db.close()


def update_budget(
    budget_id: str,
    user_id: str,
    name: Optional[str] = None,
    amount: Optional[float] = None,
    period_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[Budget]:
    """
    Update a budget.
    
    Args:
        budget_id: Budget ID
        user_id: User ID for ownership verification
        name: Optional new name
        amount: Optional new amount
        period_type: Optional new period type
        start_date: Optional new start date
        end_date: Optional new end date
    
    Returns:
        Updated Budget object or None if not found
    """
    db = SessionLocal()
    try:
        budget = db.query(Budget).filter(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        ).first()
        
        if not budget:
            return None
        
        # Update fields
        if name is not None:
            budget.name = name
        if amount is not None:
            if amount <= 0:
                raise ValueError("amount must be greater than 0")
            budget.amount = amount
        if period_type is not None:
            if period_type not in ['monthly', 'quarterly', 'yearly']:
                raise ValueError("period_type must be 'monthly', 'quarterly', or 'yearly'")
            budget.period_type = period_type
        if start_date is not None:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            if budget.end_date and start_dt >= budget.end_date:
                raise ValueError("start_date must be before end_date")
            budget.start_date = start_dt
        if end_date is not None:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            if end_dt and end_dt <= budget.start_date:
                raise ValueError("end_date must be after start_date")
            budget.end_date = end_dt
        
        budget.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(budget)
        
        return budget
    except Exception as e:
        db.rollback()
        log_exception(e)
        raise
    finally:
        db.close()


def delete_budget(budget_id: str, user_id: str) -> bool:
    """
    Delete a budget.
    
    Args:
        budget_id: Budget ID
        user_id: User ID for ownership verification
    
    Returns:
        True if deleted, False if not found
    """
    db = SessionLocal()
    try:
        budget = db.query(Budget).filter(
            Budget.budget_id == budget_id,
            Budget.user_id == user_id
        ).first()
        
        if not budget:
            return False
        
        db.delete(budget)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        log_exception(e)
        raise
    finally:
        db.close()


def get_budget_periods(budget: Budget, from_date: str, to_date: str) -> List[Dict]:
    """
    Get all budget periods within a date range.
    
    Args:
        budget: Budget object
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
    
    Returns:
        List of period dictionaries with start_date, end_date, and period number
    """
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
    
    periods = []
    current_start = budget.start_date
    period_num = 0
    
    # Determine period delta based on period_type
    if budget.period_type == 'monthly':
        delta = relativedelta(months=1)
    elif budget.period_type == 'quarterly':
        delta = relativedelta(months=3)
    else:  # yearly
        delta = relativedelta(years=1)
    
    # Generate periods until we exceed to_date or budget end_date
    while current_start <= to_dt:
        # Check if we've exceeded budget end_date
        if budget.end_date and current_start > budget.end_date:
            break
        
        # Calculate period end
        if budget.period_type == 'monthly':
            # Last day of the month
            if current_start.month == 12:
                period_end = current_start.replace(year=current_start.year + 1, month=1) - timedelta(days=1)
            else:
                period_end = current_start.replace(month=current_start.month + 1) - timedelta(days=1)
        elif budget.period_type == 'quarterly':
            # Last day of the quarter
            quarter_end_month = ((current_start.month - 1) // 3 + 1) * 3
            if quarter_end_month == 12:
                period_end = current_start.replace(year=current_start.year + 1, month=1) - timedelta(days=1)
            else:
                period_end = current_start.replace(month=quarter_end_month + 1) - timedelta(days=1)
        else:  # yearly
            period_end = current_start.replace(year=current_start.year + 1) - timedelta(days=1)
        
        # Only include periods that overlap with the requested date range
        if period_end >= from_dt and current_start <= to_dt:
            periods.append({
                "period": period_num,
                "start_date": current_start.isoformat(),
                "end_date": period_end.isoformat(),
                "budget_amount": budget.amount
            })
        
        # Move to next period
        current_start = current_start + delta
        period_num += 1
    
    return periods


def calculate_budget_status(
    budget: Budget,
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    force_refresh: bool = False
) -> Dict:
    """
    Calculate budget status (spent vs. budget) for all periods in the date range.
    
    Args:
        budget: Budget object
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        force_refresh: Force refresh consumption cache
    
    Returns:
        Dictionary with budget status per period
    """
    # Get budget periods
    periods = get_budget_periods(budget, from_date, to_date)
    
    if not periods:
        return {
            "budget_id": budget.budget_id,
            "budget_name": budget.name,
            "periods": [],
            "total_budget": 0.0,
            "total_spent": 0.0,
            "total_remaining": 0.0
        }
    
    # Get consumption data for the entire date range
    consumption_data = get_consumption(
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        force_refresh=force_refresh
    )
    
    # Aggregate consumption by period
    period_statuses = []
    total_spent = 0.0
    total_budget = 0.0
    
    for period in periods:
        period_start = period["start_date"]
        period_end = period["end_date"]
        budget_amount = period["budget_amount"]
        
        # Filter consumption entries for this period
        # An entry overlaps with the period if its date range intersects with the period
        period_entries = [
            entry for entry in consumption_data.get("entries", [])
            if entry.get("FromDate") and entry.get("ToDate")
            and entry.get("FromDate") <= period_end and entry.get("ToDate") >= period_start
        ]
        
        # Calculate total cost for this period
        period_spent = sum(
            float(entry.get("Price", 0) or 0) for entry in period_entries
        )
        
        remaining = budget_amount - period_spent
        
        period_statuses.append({
            "period": period["period"],
            "start_date": period_start,
            "end_date": period_end,
            "budget_amount": budget_amount,
            "spent": period_spent,
            "remaining": remaining,
            "utilization_percent": (period_spent / budget_amount * 100) if budget_amount > 0 else 0.0
        })
        
        total_spent += period_spent
        total_budget += budget_amount
    
    currency = consumption_data.get("currency", "EUR")
    
    return {
        "budget_id": budget.budget_id,
        "budget_name": budget.name,
        "periods": period_statuses,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent,
        "currency": currency
    }

