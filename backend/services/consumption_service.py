"""Consumption service for fetching and caching Outscale consumption data."""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from osc_sdk_python import Gateway

from backend.config.settings import CONSUMPTION_CACHE_TTL
from backend.services.catalog_service import get_catalog


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
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
    
    Returns:
        Consumption data dictionary with entries
    
    Raises:
        ValueError: If dates are invalid
        Exception: If API call fails
    """
    try:
        # Validate date format
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
        
        if from_date > to_date:
            raise ValueError("from_date must be <= to_date")
        
        # Create gateway with credentials
        gateway = Gateway(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        
        # Call ReadConsumptionAccount API with ShowPrice=True to get UnitPrice and Price
        response = gateway.ReadConsumptionAccount(
            FromDate=from_date,
            ToDate=to_date,
            ShowPrice=True
        )
        
        # Extract consumption entries
        entries = response.get("ConsumptionEntries", [])
        
        # Add region to each entry if not already present
        for entry in entries:
            if "Region" not in entry and "region" not in entry:
                entry["Region"] = region
        
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
            "entries": entries,
            "entry_count": len(entries),
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
        # Group by calendar week (Monday-Sunday)
        grouped = defaultdict(lambda: {"value": 0.0, "price": 0.0, "count": 0, "dates": set()})
        
        for entry in entries:
            from_date_str = entry.get("FromDate", "")
            if len(from_date_str) >= 10:
                try:
                    date_obj = datetime.strptime(from_date_str[:10], "%Y-%m-%d")
                    # Get Monday of the week
                    days_since_monday = date_obj.weekday()
                    monday = date_obj - timedelta(days=days_since_monday)
                    week_key = monday.strftime("%Y-%m-%d")
                    
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


def get_top_cost_drivers(consumption_data: Dict, limit: int = 10) -> List[Dict]:
    """
    Identify top cost drivers sorted by total cost.
    
    Args:
        consumption_data: Consumption data dictionary with entries
        limit: Number of top drivers to return
    
    Returns:
        List of top cost drivers with breakdown
    """
    entries = consumption_data.get("entries", [])
    
    if not entries:
        return []
    
    # Group by service+type+operation
    grouped = defaultdict(lambda: {"price": 0.0, "value": 0.0, "count": 0})
    
    for entry in entries:
        service = entry.get("Service", "Unknown")
        resource_type = entry.get("Type", "Unknown")
        operation = entry.get("Operation", "Unknown")
        key = f"{service}/{resource_type}/{operation}"
        
        grouped[key]["price"] += entry.get("Price", 0.0) or 0.0
        grouped[key]["value"] += entry.get("Value", 0.0) or 0.0
        grouped[key]["count"] += 1
    
    # Sort by price (descending) and take top N
    sorted_drivers = sorted(
        grouped.items(),
        key=lambda x: x[1]["price"],
        reverse=True
    )[:limit]
    
    result = []
    for key, data in sorted_drivers:
        parts = key.split("/")
        result.append({
            "service": parts[0] if len(parts) > 0 else "Unknown",
            "resource_type": parts[1] if len(parts) > 1 else "Unknown",
            "operation": parts[2] if len(parts) > 2 else "Unknown",
            "total_price": data["price"],
            "total_value": data["value"],
            "entry_count": data["count"]
        })
    
    return result

