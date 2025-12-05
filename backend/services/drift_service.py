"""Drift service for comparing estimated costs with actual consumption."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.services.consumption_service import get_consumption, aggregate_by_granularity
from backend.services.cost_service import get_current_costs


def calculate_drift(
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    from_date: str,
    to_date: str,
    threshold: float = 10.0,
    force_refresh: bool = False
) -> Dict:
    """
    Calculate cost drift by comparing estimated costs with actual consumption.
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        threshold: Percentage threshold for significant drift (default: 10%)
        force_refresh: Force refresh cache
    
    Returns:
        Dictionary with drift analysis including:
        - drift_by_category: Drift per resource category
        - significant_drifts: Resources with drift > threshold
        - total_estimated: Total estimated cost
        - total_actual: Total actual cost
        - overall_drift: Overall drift percentage
    """
    # Get current costs (estimated)
    cost_data = get_current_costs(
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        account_id=account_id,
        include_oos=False,
        force_refresh=force_refresh
    )
    
    # Get consumption data (actual)
    consumption_data = get_consumption(
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        force_refresh=force_refresh
    )
    
    # Aggregate consumption by resource type
    entries = consumption_data.get("entries", [])
    
    # Group consumption by resource type
    actual_by_type = defaultdict(lambda: {"cost": 0.0, "count": 0})
    for entry in entries:
        resource_type = entry.get("Type", "Unknown")
        price = entry.get("Price", 0.0) or 0.0
        actual_by_type[resource_type]["cost"] += price
        actual_by_type[resource_type]["count"] += 1
    
    # Get estimated costs by resource type
    resources = cost_data.get("resources", [])
    estimated_by_type = defaultdict(lambda: {"cost_per_month": 0.0, "count": 0})
    
    # Calculate estimated monthly cost for each resource
    # We need to estimate the cost for the date range
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        days_diff = (to_dt - from_dt).days + 1
        months_diff = days_diff / 30.0  # Approximate months
    except ValueError:
        days_diff = 30
        months_diff = 1.0
    
    for resource in resources:
        resource_type = resource.get("resource_type", "Unknown")
        cost_per_month = resource.get("cost_per_month", 0.0)
        estimated_cost = cost_per_month * months_diff
        
        estimated_by_type[resource_type]["cost_per_month"] += cost_per_month
        estimated_by_type[resource_type]["count"] += 1
    
    # Calculate drift per resource type
    drift_by_category = []
    significant_drifts = []
    
    all_types = set(list(actual_by_type.keys()) + list(estimated_by_type.keys()))
    
    for resource_type in all_types:
        actual_cost = actual_by_type[resource_type]["cost"]
        estimated_cost = estimated_by_type[resource_type]["cost_per_month"] * months_diff
        
        # Calculate drift percentage
        if actual_cost > 0:
            drift_percent = ((estimated_cost - actual_cost) / actual_cost) * 100
        elif estimated_cost > 0:
            drift_percent = 100.0  # Estimated but no actual
        else:
            drift_percent = 0.0
        
        drift_amount = estimated_cost - actual_cost
        
        drift_info = {
            "resource_type": resource_type,
            "estimated_cost": round(estimated_cost, 2),
            "actual_cost": round(actual_cost, 2),
            "drift_amount": round(drift_amount, 2),
            "drift_percent": round(drift_percent, 2),
            "estimated_count": estimated_by_type[resource_type]["count"],
            "actual_count": actual_by_type[resource_type]["count"]
        }
        
        drift_by_category.append(drift_info)
        
        # Check if significant drift
        if abs(drift_percent) >= threshold:
            significant_drifts.append(drift_info)
    
    # Sort by absolute drift percentage
    drift_by_category.sort(key=lambda x: abs(x["drift_percent"]), reverse=True)
    significant_drifts.sort(key=lambda x: abs(x["drift_percent"]), reverse=True)
    
    # Calculate overall totals
    total_estimated = sum(et["cost_per_month"] * months_diff for et in estimated_by_type.values())
    total_actual = sum(at["cost"] for at in actual_by_type.values())
    
    if total_actual > 0:
        overall_drift = ((total_estimated - total_actual) / total_actual) * 100
    elif total_estimated > 0:
        overall_drift = 100.0
    else:
        overall_drift = 0.0
    
    # Get currency
    currency = consumption_data.get("currency", cost_data.get("currency", "EUR"))
    
    return {
        "drift_by_category": drift_by_category,
        "significant_drifts": significant_drifts,
        "total_estimated": round(total_estimated, 2),
        "total_actual": round(total_actual, 2),
        "overall_drift": round(overall_drift, 2),
        "overall_drift_amount": round(total_estimated - total_actual, 2),
        "threshold": threshold,
        "currency": currency,
        "region": region,
        "from_date": from_date,
        "to_date": to_date,
        "period_days": int(days_diff),
        "period_months": round(months_diff, 2)
    }


def calculate_drift_by_category(
    estimated_costs: Dict,
    actual_consumption: Dict,
    threshold: float = 10.0
) -> List[Dict]:
    """
    Calculate drift grouped by resource category.
    
    Args:
        estimated_costs: Estimated cost data from cost service
        actual_consumption: Actual consumption data
        threshold: Percentage threshold for significant drift
    
    Returns:
        List of drift information by category
    """
    # Category mapping
    category_map = {
        "Vm": "Compute",
        "Volume": "Storage",
        "Snapshot": "Storage",
        "PublicIp": "Network",
        "NatService": "Network",
        "LoadBalancer": "Network",
        "Vpn": "Network",
        "Oos": "Storage"
    }
    
    # Group by category
    estimated_by_category = defaultdict(lambda: {"cost": 0.0, "count": 0})
    actual_by_category = defaultdict(lambda: {"cost": 0.0, "count": 0})
    
    # Process estimated costs
    resources = estimated_costs.get("resources", [])
    for resource in resources:
        resource_type = resource.get("resource_type", "Unknown")
        category = category_map.get(resource_type, "Other")
        cost_per_month = resource.get("cost_per_month", 0.0)
        
        estimated_by_category[category]["cost"] += cost_per_month
        estimated_by_category[category]["count"] += 1
    
    # Process actual consumption
    entries = actual_consumption.get("entries", [])
    for entry in entries:
        resource_type = entry.get("Type", "Unknown")
        category = category_map.get(resource_type, "Other")
        price = entry.get("Price", 0.0) or 0.0
        
        actual_by_category[category]["cost"] += price
        actual_by_category[category]["count"] += 1
    
    # Calculate drift per category
    drift_by_category = []
    all_categories = set(list(estimated_by_category.keys()) + list(actual_by_category.keys()))
    
    for category in all_categories:
        estimated = estimated_by_category[category]["cost"]
        actual = actual_by_category[category]["cost"]
        
        if actual > 0:
            drift_percent = ((estimated - actual) / actual) * 100
        elif estimated > 0:
            drift_percent = 100.0
        else:
            drift_percent = 0.0
        
        drift_by_category.append({
            "category": category,
            "estimated_cost": round(estimated, 2),
            "actual_cost": round(actual, 2),
            "drift_percent": round(drift_percent, 2),
            "is_significant": abs(drift_percent) >= threshold
        })
    
    # Sort by absolute drift
    drift_by_category.sort(key=lambda x: abs(x["drift_percent"]), reverse=True)
    
    return drift_by_category

