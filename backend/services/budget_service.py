"""Budget service for managing budgets and calculating budget status."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from backend.database import SessionLocal
from backend.models.budget import Budget
from backend.models.user import User
from backend.services.consumption_service import (
    get_consumption, 
    aggregate_by_granularity,
    round_to_period_start,
    round_to_period_end,
    get_consumption_granularity_from_budget,
    calculate_monthly_weeks,
    split_periods_at_budget_boundaries
)
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


def round_dates_to_budget_period(from_date: str, to_date: str, budget: Budget) -> tuple[str, str]:
    """
    Round dates to budget period boundaries.
    - from_date: round down to period start/beginning
    - to_date: round up to period end/beginning (exclusive)
    
    Args:
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        budget: Budget object
    
    Returns:
        Tuple of (rounded_from_date, rounded_to_date)
    """
    # Determine budget granularity
    if budget.period_type == 'monthly':
        budget_granularity = 'month'
    elif budget.period_type == 'quarterly':
        budget_granularity = 'month'  # Quarters are made of months
    else:  # yearly
        budget_granularity = 'month'  # Years are made of months
    
    # Round from_date down
    rounded_from = round_to_period_start(from_date, budget_granularity)
    
    # Round to_date up (exclusive)
    rounded_to = round_to_period_end(to_date, budget_granularity)
    
    return rounded_from, rounded_to


def validate_period_boundaries(periods: List[Dict], budget: Budget) -> bool:
    """
    Validate that periods don't cross budget period boundaries.
    
    Args:
        periods: List of period dictionaries with from_date and to_date
        budget: Budget object
    
    Returns:
        True if all periods respect budget boundaries
    """
    if not periods or not budget:
        return True
    
    # Get budget period boundaries
    budget_start = budget.start_date
    if isinstance(budget_start, str):
        budget_start = datetime.strptime(budget_start, "%Y-%m-%d").date()
    
    # Determine budget period delta
    if budget.period_type == 'monthly':
        delta = relativedelta(months=1)
    elif budget.period_type == 'quarterly':
        delta = relativedelta(months=3)
    else:  # yearly
        delta = relativedelta(years=1)
    
    # Generate budget boundaries
    budget_boundaries = []
    current_boundary = budget_start
    max_date = max(
        datetime.strptime(p.get("to_date", "1900-01-01"), "%Y-%m-%d").date()
        for p in periods
    ) if periods else budget_start
    
    while current_boundary <= max_date:
        budget_boundaries.append(current_boundary)
        current_boundary = current_boundary + delta
        if budget.end_date and current_boundary > budget.end_date:
            break
    
    # Check each period
    for period in periods:
        period_from = datetime.strptime(period.get("from_date", ""), "%Y-%m-%d").date()
        period_to = datetime.strptime(period.get("to_date", ""), "%Y-%m-%d").date()
        
        # Check if period crosses any boundary
        for boundary in budget_boundaries:
            if period_from < boundary < period_to:
                return False
    
    return True


def align_periods_to_budget_boundaries(periods: List[Dict], budget: Budget) -> List[Dict]:
    """
    Align periods to budget period boundaries to ensure periods don't cross budget boundaries.
    
    Args:
        periods: List of period dictionaries with from_date and to_date
        budget: Budget object
    
    Returns:
        List of periods aligned to budget boundaries
    """
    if not periods or not budget:
        return periods
    
    return split_periods_at_budget_boundaries(periods, budget)


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
    
    Rules:
    - All dates are rounded to budget period boundaries (from_date down, to_date up)
    - Consumption granularity is one level under budget granularity
    - Consumption is progressively cumulated within budget periods, reset at period start
    - Periods must not cross budget boundaries
    
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
        Dictionary with budget status per period (with cumulative consumption)
    """
    # Round dates to budget period boundaries
    rounded_from, rounded_to = round_dates_to_budget_period(from_date, to_date, budget)
    
    # Get budget periods
    periods = get_budget_periods(budget, rounded_from, rounded_to)
    
    if not periods:
        return {
            "budget_id": budget.budget_id,
            "budget_name": budget.name,
            "periods": [],
            "total_budget": 0.0,
            "total_spent": 0.0,
            "total_remaining": 0.0
        }
    
    # Determine consumption granularity (one level under budget)
    consumption_granularity = get_consumption_granularity_from_budget(budget.period_type)
    
    # Get consumption data with appropriate granularity
    # For monthly budgets, we need to handle special weekly calculation
    consumption_periods = []
    
    if budget.period_type == 'monthly' and consumption_granularity == 'week':
        # Special case: monthly weeks (start on 1st, 4th week extends to month end)
        for period in periods:
            period_start = datetime.strptime(period["start_date"], "%Y-%m-%d").date()
            period_end = datetime.strptime(period["end_date"], "%Y-%m-%d").date()
            
            # Generate monthly weeks for this budget period
            current_date = period_start
            while current_date <= period_end:
                year = current_date.year
                month = current_date.month
                weeks = calculate_monthly_weeks(year, month)
                
                for week in weeks:
                    week_start = datetime.strptime(week["from_date"], "%Y-%m-%d").date()
                    week_end = datetime.strptime(week["to_date"], "%Y-%m-%d").date() - timedelta(days=1)  # Convert to inclusive
                    
                    # Only include weeks within this budget period
                    if week_start >= period_start and week_end <= period_end:
                        consumption_periods.append({
                            "from_date": week["from_date"],
                            "to_date": week_end.isoformat(),  # Inclusive end date
                            "budget_period": period["period"]
                        })
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
    else:
        # For other granularities, generate periods normally
        # This would need to be implemented based on consumption_granularity
        # For now, we'll query consumption for each budget period
        for period in periods:
            consumption_periods.append({
                "from_date": period["start_date"],
                "to_date": period["end_date"],
                "budget_period": period["period"]
            })
    
    # Fetch consumption data for each consumption period
    all_consumption_entries = []
    currency = "EUR"
    
    for cons_period in consumption_periods:
        try:
            # Note: ToDate is exclusive, so we need to add 1 day
            period_to_exclusive = (datetime.strptime(cons_period["to_date"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            
            consumption_data = get_consumption(
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                account_id=account_id,
                        from_date=cons_period["from_date"],
                        to_date=period_to_exclusive,  # Exclusive ToDate
                force_refresh=force_refresh
                )
            
            if currency == "EUR" and consumption_data.get("currency"):
                currency = consumption_data.get("currency", "EUR")
                
                # Add budget period info to entries
                for entry in consumption_data.get("entries", []):
                    entry["budget_period"] = cons_period["budget_period"]
                    all_consumption_entries.append(entry)
        except Exception as e:
            continue
        
    # Calculate cumulative consumption per budget period
    period_statuses = []
    total_spent = 0.0
    total_budget = 0.0
    
    for period in periods:
        period_start = period["start_date"]
        period_end = period["end_date"]
        budget_amount = period["budget_amount"]
        period_num = period["period"]
        
        # Get consumption entries for this budget period
        period_entries = [
            entry for entry in all_consumption_entries
            if entry.get("budget_period") == period_num
        ]
        
        # Calculate cumulative consumption (progressive within period, reset at start)
        cumulative_spent = 0.0
        consumption_by_subperiod = {}
        
        # Group by consumption sub-period and calculate cumulative
        for entry in period_entries:
            entry_date = entry.get("FromDate", "")
            if len(entry_date) >= 10:
                entry_date_obj = datetime.strptime(entry_date[:10], "%Y-%m-%d").date()
                # Use date as key for sub-period
                subperiod_key = entry_date_obj.isoformat()
                
                if subperiod_key not in consumption_by_subperiod:
                    consumption_by_subperiod[subperiod_key] = 0.0
                
                consumption_by_subperiod[subperiod_key] += float(entry.get("Price", 0) or 0)
        
        # Calculate cumulative (progressive accumulation within budget period)
        cumulative_spent = sum(consumption_by_subperiod.values())
        
        remaining = budget_amount - cumulative_spent
        
        period_statuses.append({
            "period": period_num,
            "start_date": period_start,
            "end_date": period_end,
            "budget_amount": budget_amount,
            "spent": round(cumulative_spent, 2),
            "cumulative_spent": round(cumulative_spent, 2),  # Same as spent for now
            "remaining": round(remaining, 2),
            "utilization_percent": round((cumulative_spent / budget_amount * 100) if budget_amount > 0 else 0.0, 2)
        })
        
        total_spent += cumulative_spent
        total_budget += budget_amount
    
    return {
        "budget_id": budget.budget_id,
        "budget_name": budget.name,
        "periods": period_statuses,
        "total_budget": round(total_budget, 2),
        "total_spent": round(total_spent, 2),
        "total_remaining": round(total_budget - total_spent, 2),
        "currency": currency
    }

