"""Consumption service for fetching and caching Outscale consumption data."""
from typing import Dict, Optional, List
from datetime import datetime, timedelta, date
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from backend.config.settings import CONSUMPTION_CACHE_TTL
from backend.services.catalog_service import get_catalog
from backend.utils.api_call_logger import create_logged_gateway, process_and_log_api_call
from backend.utils.date_validators import validate_date_range


class ConsumptionCache:
    """In-memory consumption cache with TTL."""
    
    def __init__(self, ttl_seconds: int = CONSUMPTION_CACHE_TTL):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.ttl_seconds = ttl_seconds
    
    def _make_key(self, account_id: str, region: Optional[str], from_date: str, to_date: str) -> str:
        """Create cache key from parameters."""
        return f"{account_id}:{region or 'all'}:{from_date}:{to_date}"
    
    def get(self, account_id: str, region: Optional[str], from_date: str, to_date: str) -> Optional[Dict]:
        """Get consumption from cache if not expired."""
        key = self._make_key(account_id, region, from_date, to_date)
        
        if key not in self._cache:
            return None
        
        timestamp = self._timestamps.get(key)
        if timestamp and datetime.utcnow() - timestamp < timedelta(seconds=self.ttl_seconds):
            return self._cache[key]
        
        # Cache expired
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        return None
    
    def set(self, account_id: str, region: Optional[str], from_date: str, to_date: str, data: Dict) -> None:
        """Store consumption in cache with current timestamp."""
        key = self._make_key(account_id, region, from_date, to_date)
        self._cache[key] = data
        self._timestamps[key] = datetime.utcnow()
    
    def invalidate(self, account_id: Optional[str] = None, region: Optional[str] = None) -> None:
        """Invalidate cache for specific account/region or all."""
        if account_id or region:
            keys_to_remove = []
            for key in self._cache.keys():
                if account_id and account_id not in key:
                    continue
                if region and region not in key:
                    continue
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()
    
    def is_cached(self, account_id: str, region: Optional[str], from_date: str, to_date: str) -> bool:
        """Check if consumption is cached and not expired."""
        return self.get(account_id, region, from_date, to_date) is not None


# Global consumption cache instance
consumption_cache = ConsumptionCache()


def fetch_consumption(
    access_key: str,
    secret_key: str,
    region: str,
    from_date: str,
    to_date: str
) -> Dict:
    """
    Fetch consumption from Outscale API via ReadConsumptionAccount.
    
    Note: ReadAccountConsumption returns:
    - Data separated by type (each resource/service type has its own entry)
    - Consolidated quantity over the queried period
    - Unit price (does not vary with period - per hour or per month)
    - Total cost per type still requires calculation: quantity × unit_price
    
    Date range semantics:
    - FromDate is inclusive (included in the time period)
    - ToDate is exclusive (excluded from the time period, must be later than FromDate)
    
    Validation (enforced by validate_date_range):
    - from_date must be in the past
    - to_date must be > from_date
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        from_date: Start date (ISO format: YYYY-MM-DD) - inclusive
        to_date: End date (ISO format: YYYY-MM-DD) - exclusive
    
    Returns:
        Consumption data dictionary with entries (total cost calculated per type)
    
    Raises:
        ValueError: If dates are invalid
        Exception: If API call fails
    """
    try:
        # Validate date range using centralized validator
        # Note: fetch_consumption doesn't have granularity, so we validate basic rules only
        # The validation ensures from_date < to_date and from_date is in past
        is_valid, error_msg = validate_date_range(from_date, to_date, granularity=None)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Create gateway with credentials and logging enabled
        gateway = create_logged_gateway(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        
        # Call ReadConsumptionAccount API with ShowPrice=True to get UnitPrice
        # Note: API returns consolidated quantity per type, we need to calculate total cost
        response = process_and_log_api_call(
            gateway=gateway,
            api_method="ReadConsumptionAccount",
            call_func=lambda: gateway.ReadConsumptionAccount(
                FromDate=from_date,
                ToDate=to_date,
                ShowPrice=True
            ),
            from_date=from_date,
            to_date=to_date
        )
        
        # Extract consumption entries
        entries = response.get("ConsumptionEntries", [])
        
        # Process entries: calculate total cost per type (quantity × unit_price)
        processed_entries = []
        for entry in entries:
            # Get quantity (consolidated over the period)
            quantity = entry.get("Value", 0.0) or 0.0
            # Get unit price (does not vary with period)
            unit_price = entry.get("UnitPrice", 0.0) or 0.0
            # Calculate total cost: quantity × unit_price
            total_cost = quantity * unit_price
            
            # Create processed entry with calculated total cost
            processed_entry = {
                **entry,
                "Value": quantity,
                "UnitPrice": unit_price,
                "Price": total_cost,  # Total cost for this type over the period
                "Region": entry.get("Region") or region
            }
            processed_entries.append(processed_entry)
        
        # Get currency from catalog for this region
        currency = None
        try:
            catalog = get_catalog(region, force_refresh=False)
            currency = catalog.get("currency", "EUR")
        except Exception:
            # If catalog fetch fails, default to EUR
            currency = "EUR"
        
        return {
            "from_date": from_date,
            "to_date": to_date,
            "region": region,
            "currency": currency,
            "entries": processed_entries,
            "entry_count": len(processed_entries),
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise ValueError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to fetch consumption: {str(e)}")


def get_consumption(
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    force_refresh: bool = False
) -> Dict:
    """
    Get consumption data, using cache if available.
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        force_refresh: If True, bypass cache and fetch fresh data
    
    Returns:
        Consumption data dictionary
    """
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = consumption_cache.get(account_id, region, from_date, to_date)
        if cached:
            return cached
    
    # Fetch from API
    consumption = fetch_consumption(access_key, secret_key, region, from_date, to_date)
    
    # Store in cache
    consumption_cache.set(account_id, region, from_date, to_date, consumption)
    
    return consumption


def aggregate_by_granularity(consumption_data: Dict, granularity: str) -> List[Dict]:
    """
    Aggregate consumption entries by granularity (day/week/month).
    
    Args:
        consumption_data: Consumption data dictionary with entries
        granularity: "day", "week", or "month"
    
    Returns:
        List of aggregated entries
    """
    entries = consumption_data.get("entries", [])
    
    if not entries:
        return []
    
    if granularity == "day":
        # Group by date (from_date == to_date)
        grouped = defaultdict(lambda: {"value": 0.0, "price": 0.0, "count": 0})
        
        for entry in entries:
            from_date = entry.get("FromDate", "")
            # Use from_date as key (assuming single day entries)
            date_key = from_date[:10] if len(from_date) >= 10 else from_date
            
            grouped[date_key]["value"] += entry.get("Value", 0.0) or 0.0
            grouped[date_key]["price"] += entry.get("Price", 0.0) or 0.0
            grouped[date_key]["count"] += 1
        
        # Get region from consumption data
        data_region = consumption_data.get("region", "")
        
        result = []
        for date_key in sorted(grouped.keys()):
            result.append({
                "from_date": date_key,
                "to_date": date_key,
                "value": grouped[date_key]["value"],
                "price": grouped[date_key]["price"],
                "entry_count": grouped[date_key]["count"],
                "region": data_region
            })
        
        return result
    
    elif granularity == "week":
        # Group by monthly week (1-7, 8-14, 15-21, 22-end of month)
        grouped = defaultdict(lambda: {"value": 0.0, "price": 0.0, "count": 0, "dates": set()})
        
        for entry in entries:
            from_date_str = entry.get("FromDate", "")
            if len(from_date_str) >= 10:
                try:
                    date_obj = datetime.strptime(from_date_str[:10], "%Y-%m-%d").date()
                    # Get monthly week start (1st, 8th, 15th, or 22nd of month)
                    week_start = get_monthly_week_start(date_obj)
                    week_key = week_start.strftime("%Y-%m-%d")
                    
                    grouped[week_key]["value"] += entry.get("Value", 0.0) or 0.0
                    grouped[week_key]["price"] += entry.get("Price", 0.0) or 0.0
                    grouped[week_key]["count"] += 1
                    grouped[week_key]["dates"].add(date_obj)
                except ValueError:
                    continue
        
        # Get region from consumption data
        data_region = consumption_data.get("region", "")
        
        result = []
        for week_key in sorted(grouped.keys()):
            dates = sorted(grouped[week_key]["dates"])
            result.append({
                "from_date": dates[0].strftime("%Y-%m-%d") if dates else week_key,
                "to_date": dates[-1].strftime("%Y-%m-%d") if dates else week_key,
                "value": grouped[week_key]["value"],
                "price": grouped[week_key]["price"],
                "entry_count": grouped[week_key]["count"],
                "region": data_region
            })
        
        return result
    
    elif granularity == "month":
        # Group by calendar month
        grouped = defaultdict(lambda: {"value": 0.0, "price": 0.0, "count": 0, "dates": set()})
        
        for entry in entries:
            from_date_str = entry.get("FromDate", "")
            if len(from_date_str) >= 10:
                try:
                    date_obj = datetime.strptime(from_date_str[:10], "%Y-%m-%d")
                    month_key = date_obj.strftime("%Y-%m")
                    
                    grouped[month_key]["value"] += entry.get("Value", 0.0) or 0.0
                    grouped[month_key]["price"] += entry.get("Price", 0.0) or 0.0
                    grouped[month_key]["count"] += 1
                    grouped[month_key]["dates"].add(date_obj)
                except ValueError:
                    continue
        
        # Get region from consumption data
        data_region = consumption_data.get("region", "")
        
        result = []
        for month_key in sorted(grouped.keys()):
            dates = sorted(grouped[month_key]["dates"])
            result.append({
                "from_date": dates[0].strftime("%Y-%m-%d") if dates else f"{month_key}-01",
                "to_date": dates[-1].strftime("%Y-%m-%d") if dates else f"{month_key}-28",
                "value": grouped[month_key]["value"],
                "price": grouped[month_key]["price"],
                "entry_count": grouped[month_key]["count"],
                "region": data_region
            })
        
        return result
    
    else:
        # Return original entries if granularity not recognized
        return entries


def filter_consumption(
    consumption_data: Dict,
    region: Optional[str] = None,
    service: Optional[str] = None,
    resource_type: Optional[str] = None
) -> Dict:
    """
    Filter consumption entries by region, service, or resource type.
    
    Args:
        consumption_data: Consumption data dictionary with entries
        region: Filter by region (zone)
        service: Filter by service name
        resource_type: Filter by resource type
    
    Returns:
        Filtered consumption data dictionary
    """
    entries = consumption_data.get("entries", [])
    
    filtered_entries = entries
    
    if region:
        filtered_entries = [
            entry for entry in filtered_entries
            if entry.get("Zone", "").startswith(region) or entry.get("Zone", "") == region
        ]
    
    if service:
        filtered_entries = [
            entry for entry in filtered_entries
            if entry.get("Service", "").lower() == service.lower()
        ]
    
    if resource_type:
        filtered_entries = [
            entry for entry in filtered_entries
            if entry.get("Type", "").lower() == resource_type.lower()
        ]
    
    # Ensure region is included in each filtered entry
    data_region = consumption_data.get("region", "")
    for entry in filtered_entries:
        if "Region" not in entry and "region" not in entry:
            entry["Region"] = data_region
    
    return {
        **consumption_data,
        "entries": filtered_entries,
        "entry_count": len(filtered_entries),
        "filters": {
            "region": region,
            "service": service,
            "resource_type": resource_type
        }
    }


def aggregate_by_dimension(consumption_data: Dict, dimension: str) -> List[Dict]:
    """
    Aggregate consumption by dimension (resource_type, region, or tag).
    
    Args:
        consumption_data: Consumption data dictionary with entries
        dimension: "resource_type", "region", or "tag"
    
    Returns:
        List of aggregated entries grouped by dimension
    """
    entries = consumption_data.get("entries", [])
    
    if not entries:
        return []
    
    grouped = defaultdict(lambda: {"value": 0.0, "price": 0.0, "count": 0})
    
    for entry in entries:
        if dimension == "resource_type":
            key = entry.get("Type", "Unknown")
        elif dimension == "region":
            zone = entry.get("Zone", "")
            # Extract region from zone (remove trailing letter if present)
            key = zone[:-1] if len(zone) > 0 and zone[-1].isalpha() else zone
            if not key:
                key = "Unknown"
        elif dimension == "tag":
            # Tags might be in entry metadata, for now use service+type as key
            key = f"{entry.get('Service', 'Unknown')}/{entry.get('Type', 'Unknown')}"
        else:
            key = "Unknown"
        
        grouped[key]["value"] += entry.get("Value", 0.0) or 0.0
        grouped[key]["price"] += entry.get("Price", 0.0) or 0.0
        grouped[key]["count"] += 1
    
    # Get region from consumption data
    data_region = consumption_data.get("region", "")
    
    result = []
    for key in sorted(grouped.keys()):
        result.append({
            dimension: key,
            "value": grouped[key]["value"],
            "price": grouped[key]["price"],
            "entry_count": grouped[key]["count"],
            "region": data_region
        })
    
    return result


def calculate_totals(consumption_data: Dict) -> Dict:
    """
    Calculate total costs per period.
    
    Args:
        consumption_data: Consumption data dictionary with entries
    
    Returns:
        Dictionary with total value, total price, entry count
    """
    entries = consumption_data.get("entries", [])
    
    total_value = sum(entry.get("Value", 0.0) or 0.0 for entry in entries)
    total_price = sum(entry.get("Price", 0.0) or 0.0 for entry in entries)
    
    return {
        "total_value": total_value,
        "total_price": total_price,
        "entry_count": len(entries)
    }


def round_to_period_start(date_str: str, granularity: str) -> str:
    """
    Round date down to period start/beginning.
    
    Args:
        date_str: Date string (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month"
    
    Returns:
        Rounded date string (ISO format: YYYY-MM-DD)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        if granularity == "day":
            return date_obj.isoformat()
        elif granularity == "week":
            # Round down to start of monthly week (1st, 8th, 15th, or 22nd)
            week_start = get_monthly_week_start(date_obj)
            return week_start.isoformat()
        elif granularity == "month":
            # Round down to first day of the month
            first_day = date_obj.replace(day=1)
            return first_day.isoformat()
        else:
            return date_str
    except ValueError:
        return date_str


def round_to_period_end(date_str: str, granularity: str) -> str:
    """
    Round date up to period end/beginning (exclusive ToDate).
    
    Args:
        date_str: Date string (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month"
    
    Returns:
        Rounded date string (ISO format: YYYY-MM-DD) - exclusive ToDate
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        if granularity == "day":
            # Round up to next day (exclusive)
            next_day = date_obj + timedelta(days=1)
            return next_day.isoformat()
        elif granularity == "week":
            # Round up to start of next monthly week (exclusive)
            week_start = get_monthly_week_start(date_obj)
            day_of_month = date_obj.day
            
            # Determine next week start
            if day_of_month <= 7:
                next_week_start_day = 8
            elif day_of_month <= 14:
                next_week_start_day = 15
            elif day_of_month <= 21:
                next_week_start_day = 22
            else:
                # Week 4, move to first day of next month
                if date_obj.month == 12:
                    next_week_start = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
                else:
                    next_week_start = date_obj.replace(month=date_obj.month + 1, day=1)
                return next_week_start.isoformat()
            
            # Check if next week start is still in same month
            last_day_of_month = monthrange(date_obj.year, date_obj.month)[1]
            if next_week_start_day <= last_day_of_month:
                next_week_start = date_obj.replace(day=next_week_start_day)
            else:
                # Move to first day of next month
                if date_obj.month == 12:
                    next_week_start = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
                else:
                    next_week_start = date_obj.replace(month=date_obj.month + 1, day=1)
            
            return next_week_start.isoformat()
        elif granularity == "month":
            # Round up to first day of next month (exclusive)
            if date_obj.month == 12:
                next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
            else:
                next_month = date_obj.replace(month=date_obj.month + 1, day=1)
            return next_month.isoformat()
        else:
            return date_str
    except ValueError:
        return date_str


def get_consumption_granularity_from_budget(period_type: str) -> str:
    """
    Determine consumption granularity from budget period type.
    
    Rules:
    - Budget yearly or quarterly → monthly
    - Budget monthly → weekly
    - Budget weekly → daily
    
    Args:
        period_type: Budget period type ("monthly", "quarterly", "yearly")
    
    Returns:
        Consumption granularity ("day", "week", or "month")
    """
    if period_type == "yearly" or period_type == "quarterly":
        return "month"
    elif period_type == "monthly":
        return "week"
    else:
        # Default to day for weekly budgets or unknown types
        return "day"


def get_monthly_week_start(date_obj: date) -> date:
    """
    Get the start date of the monthly week for a given date.
    
    Monthly weeks are:
    - Week 1: Days 1-7 (starts on day 1)
    - Week 2: Days 8-14 (starts on day 8)
    - Week 3: Days 15-21 (starts on day 15)
    - Week 4: Days 22-end (starts on day 22)
    
    Args:
        date_obj: Date object
        
    Returns:
        Date object representing the start of the monthly week
    """
    day_of_month = date_obj.day
    if day_of_month <= 7:
        week_start_day = 1
    elif day_of_month <= 14:
        week_start_day = 8
    elif day_of_month <= 21:
        week_start_day = 15
    else:
        week_start_day = 22
    
    return date_obj.replace(day=week_start_day)


def calculate_monthly_weeks(year: int, month: int) -> List[Dict[str, str]]:
    """
    Calculate weeks for a month with special rules:
    - Always start on the 1st of the month
    - First 3 weeks are standard 7-day weeks
    - Fourth week extends to 8-10 days depending on actual month length
    
    Args:
        year: Year
        month: Month (1-12)
    
    Returns:
        List of week dictionaries with from_date and to_date (exclusive)
    """
    # Get first day of month
    first_day = date(year, month, 1)
    # Get last day of month
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    
    weeks = []
    
    # Week 1: Days 1-7
    week1_start = first_day
    week1_end = min(date(year, month, 7), last_day)
    weeks.append({
        "from_date": week1_start.isoformat(),
        "to_date": (week1_end + timedelta(days=1)).isoformat()  # Exclusive
    })
    
    # Week 2: Days 8-14
    if last_day_num >= 8:
        week2_start = date(year, month, 8)
        week2_end = min(date(year, month, 14), last_day)
        weeks.append({
            "from_date": week2_start.isoformat(),
            "to_date": (week2_end + timedelta(days=1)).isoformat()  # Exclusive
        })
    
    # Week 3: Days 15-21
    if last_day_num >= 15:
        week3_start = date(year, month, 15)
        week3_end = min(date(year, month, 21), last_day)
        weeks.append({
            "from_date": week3_start.isoformat(),
            "to_date": (week3_end + timedelta(days=1)).isoformat()  # Exclusive
        })
    
    # Week 4: Days 22 to end of month (8-10 days depending on month length)
    if last_day_num >= 22:
        week4_start = date(year, month, 22)
        week4_end = last_day
        weeks.append({
            "from_date": week4_start.isoformat(),
            "to_date": (week4_end + timedelta(days=1)).isoformat()  # Exclusive
        })
    
    return weeks


def align_consumption_periods_to_budget(consumption_data: Dict, budget) -> Dict:
    """
    Align consumption periods to budget period boundaries to ensure periods don't cross budget boundaries.
    
    Args:
        consumption_data: Consumption data dictionary with entries
        budget: Budget object with period_type
    
    Returns:
        Consumption data with periods aligned to budget boundaries
    """
    # This function will be used to split/truncate periods at budget boundaries
    # Implementation depends on how periods are structured in consumption_data
    # For now, return as-is - actual alignment will be done during period generation
    return consumption_data


def split_periods_at_budget_boundaries(periods: List[Dict], budget) -> List[Dict]:
    """
    Split periods at budget boundaries to ensure no period crosses a budget boundary.
    
    Args:
        periods: List of period dictionaries with from_date and to_date
        budget: Budget object with period_type, start_date
    
    Returns:
        List of periods split at budget boundaries
    """
    if not periods or not budget:
        return periods
    
    split_periods = []
    
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
    
    # Split periods at boundaries
    for period in periods:
        period_from = datetime.strptime(period.get("from_date", ""), "%Y-%m-%d").date()
        period_to = datetime.strptime(period.get("to_date", ""), "%Y-%m-%d").date()
        
        # Find boundaries that intersect with this period
        intersecting_boundaries = [
            b for b in budget_boundaries
            if period_from < b < period_to
        ]
        
        if not intersecting_boundaries:
            # No boundaries to split at, keep period as-is
            split_periods.append(period)
        else:
            # Split period at each boundary
            current_start = period_from
            for boundary in sorted(intersecting_boundaries):
                # Add period from current_start to boundary
                split_periods.append({
                    **period,
                    "from_date": current_start.isoformat(),
                    "to_date": boundary.isoformat()
                })
                current_start = boundary
            
            # Add remaining period
            if current_start < period_to:
                split_periods.append({
                    **period,
                    "from_date": current_start.isoformat(),
                    "to_date": period_to.isoformat()
                })
    
    return split_periods


