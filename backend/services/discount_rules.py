"""Discount rules for commitment-based discounts."""
from typing import Dict, Optional


# Commitment-based discounts per resource type
# Format: resourceType -> commitment period -> discount percentage
COMMITMENT_DISCOUNTS: Dict[str, Dict[str, int]] = {
    "compute": {
        "1month": 30,   # 30% discount for 1 month commitment
        "1year": 40,    # 40% discount for 1 year commitment
        "3years": 50    # 50% discount for 3 years commitment
    },
    "storage": {
        "1month": 0,
        "1year": 0,
        "3years": 0
    },
    "network": {
        "1month": 0,
        "1year": 0,
        "3years": 0
    },
    "licence": {
        "1month": 0,
        "1year": 0,
        "3years": 0
    },
    "default": {
        "1month": 0,
        "1year": 0,
        "3years": 0
    }
}


def get_resource_type(catalog_item: Dict) -> str:
    """
    Get resource type from catalog item using Category field.
    
    Args:
        catalog_item: Catalog entry dictionary
    
    Returns:
        Resource type string (compute, storage, network, licence, or default)
    """
    category = catalog_item.get("Category", "").lower()
    
    # Map category to discount rule keys
    if category == "compute":
        return "compute"
    elif category == "storage":
        return "storage"
    elif category == "network":
        return "network"
    elif category == "licence":
        return "licence"
    else:
        return "default"


def get_commitment_discount(resource_type: str, commitment_period: Optional[str]) -> int:
    """
    Get commitment discount percentage for resource type and period.
    
    Args:
        resource_type: Resource type (compute, storage, network, licence, default)
        commitment_period: Commitment period (1month, 1year, 3years, or None/none)
    
    Returns:
        Discount percentage (0-100)
    """
    if not commitment_period or commitment_period.lower() == "none":
        return 0
    
    type_rules = COMMITMENT_DISCOUNTS.get(resource_type, COMMITMENT_DISCOUNTS["default"])
    return type_rules.get(commitment_period.lower(), 0)

