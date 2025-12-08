"""Trend service for analyzing cost trends over time."""
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta, date
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import time

from backend.services.consumption_service import (
    get_consumption, 
    aggregate_by_granularity,
    round_to_period_start,
    round_to_period_end,
    split_periods_at_budget_boundaries,
    get_monthly_week_start
)
from backend.utils.date_validators import validate_date_range
from backend.utils.error_logger import log_exception, log_error_message
from calendar import monthrange


def get_monthly_week_end(week_start_date: date, from_date: date = None) -> date:
    """
    Get the end date of a monthly week.
    
    Monthly weeks are:
    - Week 1: Days 1-7 (ends on day 7)
    - Week 2: Days 8-14 (ends on day 14)
    - Week 3: Days 15-21 (ends on day 21)
    - Week 4: Days 22-end (ends on last day of month)
    
    Args:
        week_start_date: Start date of the week (1st, 8th, 15th, or 22nd)
        from_date: Optional from_date to ensure we don't go before it
        
    Returns:
        Date object representing the end of the monthly week
    """
    day_of_month = week_start_date.day
    last_day_of_month = monthrange(week_start_date.year, week_start_date.month)[1]
    
    if day_of_month == 1:
        week_end_day = 7
    elif day_of_month == 8:
        week_end_day = 14
    elif day_of_month == 15:
        week_end_day = 21
    else:  # day_of_month == 22
        week_end_day = last_day_of_month
    
    week_end = week_start_date.replace(day=min(week_end_day, last_day_of_month))
    
    # If from_date is provided and week_start is before from_date, adjust week_end
    if from_date and week_start_date < from_date:
        # This is a partial first week, end should be the normal week end
        pass
    
    return week_end


def get_next_monthly_week_start(current_date: date) -> date:
    """
    Get the start date of the next monthly week.
    
    Args:
        current_date: Current date
        
    Returns:
        Date object representing the start of the next monthly week
    """
    day_of_month = current_date.day
    last_day_of_month = monthrange(current_date.year, current_date.month)[1]
    
    # Determine next week start
    if day_of_month <= 7:
        next_week_start_day = 8
    elif day_of_month <= 14:
        next_week_start_day = 15
    elif day_of_month <= 21:
        next_week_start_day = 22
    else:
        # Week 4, move to first day of next month
        if current_date.month == 12:
            return current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            return current_date.replace(month=current_date.month + 1, day=1)
    
    # Check if next week start is still in same month
    if next_week_start_day <= last_day_of_month:
        return current_date.replace(day=next_week_start_day)
    else:
        # Move to first day of next month
        if current_date.month == 12:
            return current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            return current_date.replace(month=current_date.month + 1, day=1)


def find_last_period_excluding_today(granularity: str, from_date: str, to_date: str) -> Optional[str]:
    """
    Find the last period that doesn't include today.
    
    Args:
        granularity: "day", "week", or "month"
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
    
    Returns:
        Last period date string (ISO format: YYYY-MM-DD) or None
    """
    try:
        today = datetime.utcnow().date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        
        # If to_date is already before today, return to_date
        if to_dt < today:
            return to_date
        
        # Find last period before today
        if granularity == "day":
            last_period = today - timedelta(days=1)
        elif granularity == "week":
            # Get monthly week start for today, then go back one week
            current_week_start = get_monthly_week_start(today)
            # Get previous week start
            if current_week_start.day == 1:
                # Previous week is week 4 of previous month
                if today.month == 1:
                    last_period = today.replace(year=today.year - 1, month=12, day=22)
                else:
                    last_period = today.replace(month=today.month - 1, day=22)
            elif current_week_start.day == 8:
                last_period = today.replace(day=1)
            elif current_week_start.day == 15:
                last_period = today.replace(day=8)
            else:  # day == 22
                last_period = today.replace(day=15)
        elif granularity == "month":
            # Get first day of current month, then go back one month
            first_of_month = today.replace(day=1)
            if first_of_month.month == 1:
                last_period = first_of_month.replace(year=first_of_month.year - 1, month=12)
            else:
                last_period = first_of_month.replace(month=first_of_month.month - 1)
        else:
            return to_date
        
        # Ensure last_period is not before from_date
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        if last_period < from_dt:
            return from_date
        
        return last_period.isoformat()
    except Exception:
        return to_date


def align_periods_to_budget_boundaries(periods: List[Dict], budget) -> List[Dict]:
    """
    Align trend periods to budget period boundaries to ensure periods don't cross budget boundaries.
    
    Args:
        periods: List of period dictionaries with from_date and to_date
        budget: Budget object with period_type, start_date
    
    Returns:
        List of periods aligned to budget boundaries
    """
    if not periods or not budget:
        return periods
    
    return split_periods_at_budget_boundaries(periods, budget)


def _generate_period_ranges(from_date: str, to_date: str, granularity: str) -> List[Dict]:
    """
    Generate period date ranges based on granularity.
    
    Args:
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month"
    
    Returns:
        List of period dictionaries with "period", "from_date", "to_date"
    """
    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    period_ranges = []
    
    if granularity == "day":
        # Generate every day from from_date to to_date (inclusive)
        current_dt = from_dt
        while current_dt <= to_dt:
            period_start = current_dt
            period_end = current_dt
            period_ranges.append({
                "period": period_start.strftime("%Y-%m-%d"),
                "from_date": period_start.strftime("%Y-%m-%d"),
                "to_date": period_end.strftime("%Y-%m-%d")
            })
            current_dt += timedelta(days=1)
    
    elif granularity == "week":
        # Generate every week from from_date to to_date
        # Monthly weeks: 1-7, 8-14, 15-21, 22-end of month
        current_dt = from_dt.date()
        to_dt_date = to_dt.date()
        
        while current_dt <= to_dt_date:
            # Get monthly week start for current date
            week_start = get_monthly_week_start(current_dt)
            
            # For first week, use from_date if it's later than week_start
            if week_start < from_dt.date():
                week_start = from_dt.date()
            
            # Get monthly week end
            week_end = get_monthly_week_end(week_start, from_dt.date())
            
            # Don't go beyond to_date
            if week_end > to_dt_date:
                week_end = to_dt_date
            
            # Don't go beyond month boundary
            if week_end.month != week_start.month:
                # End at last day of week_start's month
                last_day = monthrange(week_start.year, week_start.month)[1]
                week_end = week_start.replace(day=last_day)
                if week_end > to_dt_date:
                    week_end = to_dt_date
            
            period_ranges.append({
                "period": week_start.strftime("%Y-%m-%d"),
                "from_date": week_start.strftime("%Y-%m-%d"),
                "to_date": week_end.strftime("%Y-%m-%d")
            })
            
            # Move to next week
            current_dt = get_next_monthly_week_start(week_end)
    
    elif granularity == "month":
        # Generate every month from from_date to to_date
        current_dt = from_dt
        while current_dt <= to_dt:
            # Get first day of current month
            month_start = current_dt.replace(day=1)
            
            # Get last day of current month
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
            
            # Don't go beyond to_date
            if month_end > to_dt:
                month_end = to_dt
            
            month_key = month_start.strftime("%Y-%m")
            period_ranges.append({
                "period": month_key,
                "from_date": month_start.strftime("%Y-%m-%d"),
                "to_date": month_end.strftime("%Y-%m-%d")
            })
            
            # Move to first day of next month
            if month_start.month == 12:
                current_dt = month_start.replace(year=month_start.year + 1, month=1)
            else:
                current_dt = month_start.replace(month=month_start.month + 1)
    
    return period_ranges


def _fetch_period_costs(
    period_ranges: List[Dict],
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    resource_type: Optional[str],
    force_refresh: bool,
    use_exclusive_todate: bool = True,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    start_progress: int = 0,
    end_progress: int = 80,
    start_time: Optional[float] = None
) -> Tuple[List[Dict], str]:
    """
    Fetch consumption data and calculate costs for each period.
    
    Args:
        period_ranges: List of period dictionaries with from_date and to_date
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        resource_type: Optional resource type filter
        force_refresh: Force refresh cache
        use_exclusive_todate: If True, add 1 day to to_date for API call (exclusive)
        progress_callback: Optional callback for progress updates
        start_progress: Starting progress percentage (default: 0)
        end_progress: Ending progress percentage (default: 80)
        start_time: Optional start time for time estimation (for async)
    
    Returns:
        Tuple of (periods list with cost/value/entry_count, currency string)
    """
    periods = []
    currency = "EUR"  # Default currency
    total_periods = len(period_ranges)
    
    for idx, period_range in enumerate(period_ranges):
        period_from = period_range["from_date"]
        period_to = period_range["to_date"]
        
        # Update progress if callback provided
        if progress_callback and total_periods > 0:
            period_progress = start_progress + int((idx / total_periods) * (end_progress - start_progress))
            
            # Estimate time remaining if start_time provided
            estimated_remaining = None
            if start_time and period_progress > start_progress:
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    estimated_total = elapsed_time / ((period_progress - start_progress) / (end_progress - start_progress))
                    estimated_remaining = int(estimated_total - elapsed_time)
            
            progress_callback(period_progress, estimated_remaining)
        
        # Get consumption data for this specific period
        try:
            # Handle exclusive vs inclusive ToDate
            if use_exclusive_todate:
                # Convert period_to to exclusive ToDate (add 1 day)
                period_to_dt = datetime.strptime(period_to, "%Y-%m-%d")
                period_to_exclusive = (period_to_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                api_to_date = period_to_exclusive
            else:
                api_to_date = period_to
            
            consumption_data = get_consumption(
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                account_id=account_id,
                from_date=period_from,
                to_date=api_to_date,
                force_refresh=force_refresh
            )
            
            # Get currency from first successful consumption fetch
            if currency == "EUR" and consumption_data.get("currency"):
                currency = consumption_data.get("currency", "EUR")
            
            # Filter by resource type if specified
            entries = consumption_data.get("entries", [])
            if resource_type:
                entries = [
                    entry for entry in entries
                    if entry.get("Type", "").lower() == resource_type.lower()
                ]
            
            # Calculate total cost for this period
            period_cost = sum(entry.get("UnitPrice", 0.0) * entry.get("Value", 0.0) for entry in entries)
            period_value = sum(entry.get("Value", 0.0) or 0.0 for entry in entries)
            entry_count = len(entries)
            
        except Exception as e:
            # If consumption fetch fails for this period, use zero values
            period_cost = 0.0
            period_value = 0.0
            entry_count = 0
        
        periods.append({
            "period": period_range["period"],
            "from_date": period_range["from_date"],
            "to_date": period_range["to_date"],
            "cost": round(period_cost, 2),
            "value": round(period_value, 2),
            "entry_count": entry_count
        })
    
    return periods, currency


def _calculate_trend_metrics(periods: List[Dict]) -> Dict:
    """
    Calculate trend metrics from periods.
    
    Args:
        periods: List of period dictionaries with "cost" field
    
    Returns:
        Dictionary with growth_rate, historical_average, period_changes, trend_direction
    """
    # Calculate growth rate (overall)
    growth_rate = calculate_growth_rate(periods)
    
    # Calculate historical average
    historical_average = calculate_historical_average(periods)
    
    # Calculate period-over-period changes
    period_changes = []
    for i in range(1, len(periods)):
        prev_cost = periods[i - 1]["cost"]
        curr_cost = periods[i]["cost"]
        
        if prev_cost > 0:
            change_percent = ((curr_cost - prev_cost) / prev_cost) * 100
        elif curr_cost > 0:
            change_percent = 100.0  # From 0 to positive
        else:
            change_percent = 0.0
        
        period_changes.append({
            "from_period": periods[i - 1]["period"],
            "to_period": periods[i]["period"],
            "previous_cost": prev_cost,
            "current_cost": curr_cost,
            "change_amount": round(curr_cost - prev_cost, 2),
            "change_percent": round(change_percent, 2)
        })
    
    # Determine trend direction
    if growth_rate > 5.0:
        trend_direction = "increasing"
    elif growth_rate < -5.0:
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"
    
    return {
        "growth_rate": round(growth_rate, 2),
        "historical_average": round(historical_average, 2),
        "period_changes": period_changes,
        "trend_direction": trend_direction
    }


def _build_trend_result(
    periods: List[Dict],
    metrics: Dict,
    currency: str,
    region: str,
    granularity: str,
    from_date: str,
    to_date: str,
    resource_type: Optional[str],
    projected: bool = False,
    projected_periods: int = 0
) -> Dict:
    """
    Build the final trend result dictionary.
    
    Args:
        periods: List of period dictionaries
        metrics: Dictionary with growth_rate, historical_average, period_changes, trend_direction
        currency: Currency string
        region: Region name
        granularity: Granularity string
        from_date: Start date
        to_date: End date
        resource_type: Optional resource type
        projected: Whether projection was performed
        projected_periods: Number of projected periods
    
    Returns:
        Complete trend result dictionary
    """
    total_cost = sum(p["cost"] for p in periods)
    
    result = {
        "periods": periods,
        "growth_rate": metrics["growth_rate"],
        "historical_average": metrics["historical_average"],
        "period_changes": metrics["period_changes"],
        "trend_direction": metrics["trend_direction"],
        "total_cost": round(total_cost, 2),
        "period_count": len(periods),
        "currency": currency,
        "region": region,
        "granularity": granularity,
        "from_date": from_date,
        "to_date": to_date,
        "resource_type": resource_type
    }
    
    # Add projection fields if applicable
    if projected:
        result["projected"] = projected
        result["projected_periods"] = projected_periods
    
    return result


def calculate_trends(
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    granularity: str = "day",
    resource_type: Optional[str] = None,
    force_refresh: bool = False,
    budget: Optional[object] = None,
    project_until: Optional[str] = None
) -> Dict:
    """
    Calculate cost trends over time.
    
    Validation rules (enforced by validate_date_range):
    - from_date must be in the past
    - to_date must be >= from_date + 1 granularity period
    
    Functional rules (not validation):
    - If from_date is in the past: do not show projected trend
    - If from_date is in the future: query consumption until last period excluding today, then project trend
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month" (default: "day")
        resource_type: Optional resource type filter
        force_refresh: Force refresh cache
        budget: Optional budget object for boundary alignment
        project_until: Optional end date for trend projection
    
    Returns:
        Dictionary with trend data including:
        - periods: List of periods with costs
        - growth_rate: Overall growth rate percentage
        - historical_average: Average cost per period
        - period_changes: List of period-over-period changes
        - trend_direction: "increasing", "decreasing", or "stable"
        - projected: Boolean indicating if projection was performed
    """
    # Validate date range (validation: from_date in past, to_date >= from_date + 1 period)
    is_valid, error_msg = validate_date_range(from_date, to_date, granularity)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Functional check: determine if to_date is in past or future (for projection logic, not validation)
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    today = datetime.utcnow().date()
    to_date_obj = to_dt.date()
    is_to_date_in_past = to_date_obj < today
    
    # Determine actual query end date
    # If to_date is in future, query until last period excluding today
    if not is_to_date_in_past:
        actual_to_date = find_last_period_excluding_today(granularity, from_date, to_date)
        if actual_to_date:
            query_to_date = actual_to_date
            should_project = True
            project_end_date = project_until or to_date
        else:
            query_to_date = to_date
            should_project = True
            project_end_date = to_date
    else:
        query_to_date = to_date
        should_project = False
        project_end_date = None
    
    # Generate period ranges
    period_ranges = _generate_period_ranges(from_date, query_to_date, granularity)
    
    # Fetch consumption data and calculate costs (using exclusive ToDate)
    periods, currency = _fetch_period_costs(
        period_ranges=period_ranges,
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        account_id=account_id,
        resource_type=resource_type,
        force_refresh=force_refresh,
        use_exclusive_todate=True
    )
    
    # Align periods to budget boundaries if budget is provided
    if budget:
        periods = align_periods_to_budget_boundaries(periods, budget)
    
    # Calculate trend metrics
    metrics = _calculate_trend_metrics(periods)
    
    # Project trend if needed
    projected_periods = []
    if should_project and project_end_date:
        trend_data_for_projection = {
            "periods": periods,
            "growth_rate": metrics["growth_rate"],
            "historical_average": metrics["historical_average"],
            "granularity": granularity
        }
        projected_data = project_trend_until_date(trend_data_for_projection, project_end_date, budget)
        projected_periods = projected_data.get("periods", [])[len(periods):] if len(projected_data.get("periods", [])) > len(periods) else []
        # Combine historical and projected periods
        all_periods = periods + projected_periods
    else:
        all_periods = periods
    
    # Build result
    final_to_date = project_end_date if should_project and project_end_date else to_date
    return _build_trend_result(
        periods=all_periods,
        metrics=metrics,
        currency=currency,
        region=region,
        granularity=granularity,
        from_date=from_date,
        to_date=final_to_date,
        resource_type=resource_type,
        projected=should_project and len(projected_periods) > 0,
        projected_periods=len(projected_periods) if should_project else 0
    )


def calculate_growth_rate(periods: List[Dict]) -> float:
    """
    Calculate overall growth rate from periods.
    
    Args:
        periods: List of period dictionaries with "cost" field
    
    Returns:
        Growth rate percentage
    """
    if len(periods) < 2:
        return 0.0
    
    first_cost = periods[0]["cost"]
    last_cost = periods[-1]["cost"]
    
    if first_cost > 0:
        return ((last_cost - first_cost) / first_cost) * 100
    elif last_cost > 0:
        return 100.0
    else:
        return 0.0


def calculate_historical_average(periods: List[Dict]) -> float:
    """
    Calculate historical average cost per period.
    
    Args:
        periods: List of period dictionaries with "cost" field
    
    Returns:
        Average cost
    """
    if not periods:
        return 0.0
    
    total_cost = sum(p["cost"] for p in periods)
    return total_cost / len(periods)


def identify_cost_changes(periods: List[Dict], threshold: float = 10.0) -> List[Dict]:
    """
    Identify periods with significant cost changes.
    
    Args:
        periods: List of period dictionaries with "cost" field
        threshold: Percentage threshold for significant change (default: 10%)
    
    Returns:
        List of significant changes
    """
    significant_changes = []
    
    for i in range(1, len(periods)):
        prev_cost = periods[i - 1]["cost"]
        curr_cost = periods[i]["cost"]
        
        if prev_cost > 0:
            change_percent = abs(((curr_cost - prev_cost) / prev_cost) * 100)
        elif curr_cost > 0:
            change_percent = 100.0
        else:
            change_percent = 0.0
        
        if change_percent >= threshold:
            significant_changes.append({
                "from_period": periods[i - 1]["period"],
                "to_period": periods[i]["period"],
                "previous_cost": prev_cost,
                "current_cost": curr_cost,
                "change_percent": round(change_percent, 2),
                "direction": "increase" if curr_cost > prev_cost else "decrease"
            })
    
    return significant_changes


def calculate_trends_async(
    job_id: str,
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    granularity: str = "day",
    resource_type: Optional[str] = None,
    force_refresh: bool = False,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None
) -> Dict:
    """
    Calculate cost trends asynchronously with progress updates.
    
    Args:
        job_id: Job ID for progress tracking
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month" (default: "day")
        resource_type: Optional resource type filter
        force_refresh: Force refresh cache
        progress_callback: Optional callback function(progress, estimated_time_remaining)
    
    Returns:
        Dictionary with trend data (same as calculate_trends)
    """
    start_time = time.time()
    
    def update_progress(progress: int, estimated_remaining: Optional[int] = None):
        """Update progress via callback if provided."""
        if progress_callback:
            progress_callback(progress, estimated_remaining)
    
    try:
        # 0%: Starting
        update_progress(0)
        
        # Generate period ranges
        period_ranges = _generate_period_ranges(from_date, to_date, granularity)
        
        # 20%: Periods generated
        update_progress(20)
        
        # Fetch consumption data and calculate costs (using inclusive ToDate for async)
        periods, currency = _fetch_period_costs(
            period_ranges=period_ranges,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            account_id=account_id,
            resource_type=resource_type,
            force_refresh=force_refresh,
            use_exclusive_todate=False,  # Async uses inclusive ToDate
            progress_callback=update_progress,
            start_progress=20,
            end_progress=80,
            start_time=start_time
        )
        
        # 80%: Data mapped to periods, starting calculations
        update_progress(80)
        
        # Calculate trend metrics
        metrics = _calculate_trend_metrics(periods)
        
        # 100%: Done
        update_progress(100, 0)
        
        # Build result
        return _build_trend_result(
            periods=periods,
            metrics=metrics,
            currency=currency,
            region=region,
            granularity=granularity,
            from_date=from_date,
            to_date=to_date,
            resource_type=resource_type
        )
    
    except Exception as e:
        # Update progress to indicate error
        update_progress(0)
        raise e


def project_trend_until_date(trend_data: Dict, end_date: str, budget: Optional[object] = None) -> Dict:
    """
    Extend trend projection until specified end date.
    
    Args:
        trend_data: Trend data dictionary from calculate_trends
        end_date: Target end date (ISO format: YYYY-MM-DD)
        budget: Optional budget object for boundary alignment
    
    Returns:
        Extended trend data with projected periods until end_date
    """
    if not trend_data or not trend_data.get("periods"):
        return trend_data
    
    periods = trend_data["periods"]
    if not periods:
        return trend_data
    
    # Get the last period date
    last_period = periods[-1]
    last_date_str = last_period.get("to_date") or last_period.get("period")
    
    try:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        target_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # If target date is before or equal to last date, return original data
        if target_date <= last_date:
            return trend_data
        
        # Calculate growth rate per period
        growth_rate = trend_data.get("growth_rate", 0.0)
        historical_avg = trend_data.get("historical_average", 0.0)
        granularity = trend_data.get("granularity", "day")
        
        # Get the last cost value
        last_cost = periods[-1].get("cost", historical_avg)
        
        # Generate projected periods
        projected_periods = []
        current_date = last_date
        period_num = len(periods)
        
        # Determine period delta
        if granularity == "day":
            delta = timedelta(days=1)
        elif granularity == "week":
            delta = timedelta(weeks=1)
        else:  # month
            delta = relativedelta(months=1)
        
        # Project forward
        while current_date < target_date:
            current_date += delta
            
            # Don't exceed target date
            if current_date > target_date:
                current_date = target_date
            
            # Calculate projected cost based on growth rate
            # Simple linear projection: cost = last_cost * (1 + growth_rate/100)
            # For multiple periods, compound the growth
            periods_ahead = period_num - len(periods) + 1
            projected_cost = last_cost * ((1 + growth_rate / 100) ** periods_ahead)
            
            # Ensure non-negative
            projected_cost = max(0, projected_cost)
            
            # Calculate period end (exclusive ToDate)
            period_end = current_date + delta if current_date + delta <= target_date else target_date
            
            projected_periods.append({
                "period": current_date.strftime("%Y-%m-%d"),
                "from_date": current_date.strftime("%Y-%m-%d"),
                "to_date": period_end.strftime("%Y-%m-%d"),
                "cost": round(projected_cost, 2),
                "projected": True
            })
            
            period_num += 1
            
            # Stop if we've reached target date
            if current_date >= target_date:
                break
        
        # Align projected periods to budget boundaries if budget is provided
        if budget and projected_periods:
            projected_periods = align_periods_to_budget_boundaries(projected_periods, budget)
        
        # Combine original and projected periods
        extended_periods = periods + projected_periods
        
        # Recalculate totals
        total_cost = sum(p["cost"] for p in extended_periods)
        
        return {
            **trend_data,
            "periods": extended_periods,
            "total_cost": round(total_cost, 2),
            "period_count": len(extended_periods),
            "projected_periods": len(projected_periods),
            "to_date": end_date
        }
    
    except ValueError as e:
        # Invalid date format, return original data
        return trend_data
    except Exception as e:
        # Any other error, return original data
        return trend_data

