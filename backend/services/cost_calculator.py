"""Cost calculation service for quotes."""
from typing import Dict, List, Optional

# Constants
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
DAYS_PER_MONTH = 30  # Approximate
DAYS_PER_YEAR = 365  # Approximate
WEEKS_PER_MONTH = 4.33  # Approximate


def convert_duration_to_hours(duration: float, unit: str) -> float:
    """
    Convert duration to hours.
    
    Args:
        duration: Duration value
        unit: Unit (hours, days, weeks, months, years)
    
    Returns:
        Duration in hours
    """
    duration = float(duration) or 0.0
    
    unit_lower = unit.lower()
    if unit_lower == "hours":
        return duration
    elif unit_lower == "days":
        return duration * HOURS_PER_DAY
    elif unit_lower == "weeks":
        return duration * HOURS_PER_DAY * DAYS_PER_WEEK
    elif unit_lower == "months":
        return duration * HOURS_PER_DAY * DAYS_PER_MONTH
    elif unit_lower == "years":
        return duration * HOURS_PER_DAY * DAYS_PER_YEAR
    else:
        return duration


def convert_duration_to_months(duration: float, unit: str) -> float:
    """
    Convert duration to months.
    
    Args:
        duration: Duration value
        unit: Unit (hours, days, weeks, months, years)
    
    Returns:
        Duration in months
    """
    duration = float(duration) or 0.0
    
    unit_lower = unit.lower()
    if unit_lower == "hours":
        return duration / (HOURS_PER_DAY * DAYS_PER_MONTH)
    elif unit_lower == "days":
        return duration / DAYS_PER_MONTH
    elif unit_lower == "weeks":
        return duration / WEEKS_PER_MONTH
    elif unit_lower == "months":
        return duration
    elif unit_lower == "years":
        return duration * 12
    else:
        return duration


def calculate_item_cost(
    item: Dict,
    duration: float,
    duration_unit: str,
    commitment_period: Optional[str],
    global_discount_percent: float = 0.0
) -> Dict:
    """
    Calculate cost for a single quote item.
    
    Args:
        item: Quote item dictionary with quantity, unitPrice, resourceData, etc.
        duration: Duration value
        duration_unit: Duration unit (hours, days, weeks, months, years)
        commitment_period: Commitment period (1month, 1year, 3years, none)
        global_discount_percent: Global discount percentage (0-100)
    
    Returns:
        Dictionary with calculated costs
    """
    from backend.services.discount_rules import get_resource_type, get_commitment_discount
    
    quantity = float(item.get("quantity", 0) or 0)
    unit_price = float(item.get("unit_price", 0) or 0)
    resource_data = item.get("resource_data", {})
    flags = resource_data.get("Flags", "")
    is_monthly = "PER_MONTH" in flags.upper()
    
    # Convert duration to billing unit
    if is_monthly:
        duration_in_billing_unit = convert_duration_to_months(duration, duration_unit)
    else:
        duration_in_billing_unit = convert_duration_to_hours(duration, duration_unit)
    
    # Base cost: quantity × unit price × duration
    base_cost = quantity * unit_price * duration_in_billing_unit
    
    # For io1 BSU storage, add IOPS cost
    iops_cost = 0.0
    if item.get("iops_unit_price") and item.get("parameters", {}).get("iops"):
        iops_quantity = float(item["parameters"]["iops"] or 0)
        iops_unit_price = float(item.get("iops_unit_price", 0) or 0)
        iops_cost = iops_quantity * iops_unit_price * duration_in_billing_unit
        base_cost += iops_cost
    
    # Apply commitment discount
    resource_type = get_resource_type(resource_data)
    commitment_discount_percent = get_commitment_discount(resource_type, commitment_period)
    commitment_discount_amount = base_cost * (commitment_discount_percent / 100.0)
    cost_after_commitment_discount = base_cost - commitment_discount_amount
    
    # Apply global discount
    global_discount_amount = cost_after_commitment_discount * (global_discount_percent / 100.0)
    final_cost = cost_after_commitment_discount - global_discount_amount
    
    return {
        "base_cost": round(base_cost, 2),
        "iops_cost": round(iops_cost, 2),
        "commitment_discount_percent": commitment_discount_percent,
        "commitment_discount_amount": round(commitment_discount_amount, 2),
        "cost_after_commitment_discount": round(cost_after_commitment_discount, 2),
        "global_discount_percent": global_discount_percent,
        "global_discount_amount": round(global_discount_amount, 2),
        "final_cost": round(final_cost, 2),
        "quantity": quantity,
        "unit_price": unit_price,
        "duration_in_billing_unit": round(duration_in_billing_unit, 4),
        "is_monthly": is_monthly
    }


def calculate_quote_total(
    items: List[Dict],
    duration: float,
    duration_unit: str,
    commitment_period: Optional[str],
    global_discount_percent: float = 0.0
) -> Dict:
    """
    Calculate total quote cost with all discounts.
    
    Args:
        items: List of quote items
        duration: Duration value
        duration_unit: Duration unit
        commitment_period: Commitment period
        global_discount_percent: Global discount percentage
    
    Returns:
        Dictionary with quote totals and breakdown
    """
    items_with_costs = []
    base_total = 0.0
    total_commitment_discounts = 0.0
    subtotal = 0.0
    
    for item in items:
        item_cost = calculate_item_cost(
            item, duration, duration_unit, commitment_period, global_discount_percent
        )
        
        # Create item with costs
        item_with_cost = {**item, **item_cost}
        items_with_costs.append(item_with_cost)
        
        # Accumulate totals
        base_total += item_cost["base_cost"]
        total_commitment_discounts += item_cost["commitment_discount_amount"]
        subtotal += item_cost["cost_after_commitment_discount"]
    
    # Calculate global discount on subtotal
    global_discount_amount = subtotal * (global_discount_percent / 100.0)
    total = subtotal - global_discount_amount
    
    return {
        "items": items_with_costs,
        "base_total": round(base_total, 2),
        "total_commitment_discounts": round(total_commitment_discounts, 2),
        "subtotal": round(subtotal, 2),
        "global_discount_percent": global_discount_percent,
        "global_discount_amount": round(global_discount_amount, 2),
        "total": round(total, 2),
        "item_count": len(items),
        "summary": {
            "base_total": round(base_total, 2),
            "commitment_discounts": round(total_commitment_discounts, 2),
            "subtotal": round(subtotal, 2),
            "global_discount": round(global_discount_amount, 2),
            "total": round(total, 2)
        }
    }

