"""Trend service for analyzing cost trends over time."""
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import time

from backend.services.consumption_service import get_consumption, aggregate_by_granularity


def calculate_trends(
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    granularity: str = "day",
    resource_type: Optional[str] = None,
    force_refresh: bool = False
) -> Dict:
    """
    Calculate cost trends over time.
    
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
    
    Returns:
        Dictionary with trend data including:
        - periods: List of periods with costs
        - growth_rate: Overall growth rate percentage
        - historical_average: Average cost per period
        - period_changes: List of period-over-period changes
        - trend_direction: "increasing", "decreasing", or "stable"
    """
    # Generate ALL periods between from_date and to_date based on granularity first
    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    current_dt = from_dt
    
    # Generate period date ranges
    period_ranges = []
    
    if granularity == "day":
        # Generate every day from from_date to to_date (inclusive)
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
        # Weeks start on Monday
        current_dt = from_dt
        while current_dt <= to_dt:
            # Get Monday of the current week
            days_since_monday = current_dt.weekday()
            week_start = current_dt - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)
            
            # Don't go beyond to_date
            if week_end > to_dt:
                week_end = to_dt
            
            period_ranges.append({
                "period": week_start.strftime("%Y-%m-%d"),
                "from_date": week_start.strftime("%Y-%m-%d"),
                "to_date": week_end.strftime("%Y-%m-%d")
            })
            
            # Move to next week (Monday)
            current_dt = week_start + timedelta(days=7)
    
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
    
    # Now fetch consumption data for each period individually
    periods = []
    currency = "EUR"  # Default currency
    
    for period_range in period_ranges:
        period_from = period_range["from_date"]
        period_to = period_range["to_date"]
        
        # Get consumption data for this specific period
        try:
            consumption_data = get_consumption(
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                account_id=account_id,
                from_date=period_from,
                to_date=period_to,
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
            period_cost = sum(entry.get("Price", 0.0) or 0.0 for entry in entries)
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
    
    # Periods are already in chronological order
    
    # Calculate growth rate (overall)
    growth_rate = 0.0
    if len(periods) >= 2:
        first_cost = periods[0]["cost"]
        last_cost = periods[-1]["cost"]
        if first_cost > 0:
            growth_rate = ((last_cost - first_cost) / first_cost) * 100
        elif last_cost > 0:
            growth_rate = 100.0  # From 0 to positive
    
    # Calculate historical average
    total_cost = sum(p["cost"] for p in periods)
    historical_average = total_cost / len(periods) if periods else 0.0
    
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
    
    # Currency is already set from consumption fetches above
    
    return {
        "periods": periods,
        "growth_rate": round(growth_rate, 2),
        "historical_average": round(historical_average, 2),
        "period_changes": period_changes,
        "trend_direction": trend_direction,
        "total_cost": round(total_cost, 2),
        "period_count": len(periods),
        "currency": currency,
        "region": region,
        "granularity": granularity,
        "from_date": from_date,
        "to_date": to_date,
        "resource_type": resource_type
    }


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
        
        # Generate ALL periods between from_date and to_date based on granularity first
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        current_dt = from_dt
        
        # Generate period date ranges
        period_ranges = []
        
        if granularity == "day":
            # Generate every day from from_date to to_date (inclusive)
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
            # Weeks start on Monday
            current_dt = from_dt
            while current_dt <= to_dt:
                # Get Monday of the current week
                days_since_monday = current_dt.weekday()
                week_start = current_dt - timedelta(days=days_since_monday)
                week_end = week_start + timedelta(days=6)
                
                # Don't go beyond to_date
                if week_end > to_dt:
                    week_end = to_dt
                
                period_ranges.append({
                    "period": week_start.strftime("%Y-%m-%d"),
                    "from_date": week_start.strftime("%Y-%m-%d"),
                    "to_date": week_end.strftime("%Y-%m-%d")
                })
                
                # Move to next week (Monday)
                current_dt = week_start + timedelta(days=7)
        
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
        
        # 20%: Periods generated
        update_progress(20)
        
        # Now fetch consumption data for each period individually
        periods = []
        currency = "EUR"  # Default currency
        total_periods = len(period_ranges)
        
        for idx, period_range in enumerate(period_ranges):
            period_from = period_range["from_date"]
            period_to = period_range["to_date"]
            
            # Update progress: 20% + (60% * progress through periods)
            period_progress = 20 + int((idx / total_periods) * 60) if total_periods > 0 else 20
            elapsed_time = time.time() - start_time
            
            # Estimate time remaining
            if period_progress > 20 and elapsed_time > 0:
                estimated_total = elapsed_time / (period_progress / 100)
                estimated_remaining = int(estimated_total - elapsed_time)
            else:
                estimated_remaining = None
            
            update_progress(period_progress, estimated_remaining)
            
            # Get consumption data for this specific period
            try:
                consumption_data = get_consumption(
                    access_key=access_key,
                    secret_key=secret_key,
                    region=region,
                    account_id=account_id,
                    from_date=period_from,
                    to_date=period_to,
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
                period_cost = sum(entry.get("UnitPrice", 0.0) or 0.0 for entry in entries)
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
        
        # 80%: Data mapped to periods, starting calculations
        update_progress(80)
        
        # Calculate growth rate (overall)
        growth_rate = 0.0
        if len(periods) >= 2:
            first_cost = periods[0]["cost"]
            last_cost = periods[-1]["cost"]
            if first_cost > 0:
                growth_rate = ((last_cost - first_cost) / first_cost) * 100
            elif last_cost > 0:
                growth_rate = 100.0  # From 0 to positive
        
        # Calculate historical average
        total_cost = sum(p["cost"] for p in periods)
        historical_average = total_cost / len(periods) if periods else 0.0
        
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
        
        # 100%: Done
        update_progress(100, 0)
        
        return {
            "periods": periods,
            "growth_rate": round(growth_rate, 2),
            "historical_average": round(historical_average, 2),
            "period_changes": period_changes,
            "trend_direction": trend_direction,
            "total_cost": round(total_cost, 2),
            "period_count": len(periods),
            "currency": currency,
            "region": region,
            "granularity": granularity,
            "from_date": from_date,
            "to_date": to_date,
            "resource_type": resource_type
        }
    
    except Exception as e:
        # Update progress to indicate error
        update_progress(0)
        raise e

