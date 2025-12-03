"""Catalog service for fetching and caching Outscale catalogs."""
import time
import json
import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from backend.config.settings import SUPPORTED_REGIONS, CATALOG_CACHE_TTL


class CatalogCache:
    """In-memory catalog cache with TTL."""
    
    def __init__(self, ttl_seconds: int = CATALOG_CACHE_TTL):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, region: str) -> Optional[Dict]:
        """Get catalog from cache if not expired."""
        if region not in self._cache:
            return None
        
        timestamp = self._timestamps.get(region)
        if timestamp and datetime.utcnow() - timestamp < timedelta(seconds=self.ttl_seconds):
            return self._cache[region]
        
        # Cache expired
        self._cache.pop(region, None)
        self._timestamps.pop(region, None)
        return None
    
    def set(self, region: str, catalog: Dict) -> None:
        """Store catalog in cache with current timestamp."""
        self._cache[region] = catalog
        self._timestamps[region] = datetime.utcnow()
    
    def invalidate(self, region: Optional[str] = None) -> None:
        """Invalidate cache for a region or all regions."""
        if region:
            self._cache.pop(region, None)
            self._timestamps.pop(region, None)
        else:
            self._cache.clear()
            self._timestamps.clear()
    
    def is_cached(self, region: str) -> bool:
        """Check if catalog is cached and not expired."""
        return self.get(region) is not None


# Global catalog cache instance
catalog_cache = CatalogCache()


def _get_api_url(region: str) -> str:
    """
    Get API URL for a region.
    
    Args:
        region: Region name
    
    Returns:
        API base URL
    """
    # Map regions to API endpoints
    region_map = {
        "cloudgouv-eu-west-1": "api.cloudgouv-eu-west-1.outscale.com",
        "eu-west-2": "api.eu-west-2.outscale.com",
        "us-west-1": "api.us-west-1.outscale.com",
        "us-east-2": "api.us-east-2.outscale.com"
    }
    
    api_host = region_map.get(region)
    if not api_host:
        raise ValueError(f"Unsupported region: {region}")
    
    return f"https://{api_host}/api/v1/ReadPublicCatalog"


def fetch_catalog(region: str) -> Dict:
    """
    Fetch catalog from Outscale API (no authentication required).
    Uses direct HTTP request to ReadPublicCatalog endpoint.
    
    Args:
        region: Region name (must be in SUPPORTED_REGIONS)
    
    Returns:
        Catalog data dictionary
    
    Raises:
        ValueError: If region is not supported
        Exception: If API call fails
    """
    if region not in SUPPORTED_REGIONS:
        raise ValueError(f"Unsupported region: {region}. Supported: {', '.join(SUPPORTED_REGIONS)}")
    
    try:
        # ReadPublicCatalog does not require authentication
        # Use direct requests.post call
        url = _get_api_url(region)
        
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({}),
            timeout=30
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Extract catalog entries
        catalog = response_data.get("Catalog", {})
        entries = catalog.get("Entries", [])
        
        return {
            "region": region,
            "entries": entries,
            "fetched_at": datetime.utcnow().isoformat(),
            "entry_count": len(entries)
        }
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch catalog for region {region}: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to fetch catalog for region {region}: {str(e)}")


def get_catalog(region: str, force_refresh: bool = False) -> Dict:
    """
    Get catalog for a region, using cache if available.
    
    Args:
        region: Region name
        force_refresh: If True, bypass cache and fetch fresh data
    
    Returns:
        Catalog data dictionary
    """
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = catalog_cache.get(region)
        if cached:
            return cached
    
    # Fetch from API
    catalog = fetch_catalog(region)
    
    # Store in cache
    catalog_cache.set(region, catalog)
    
    return catalog


def filter_catalog_by_category(catalog: Dict, category: Optional[str] = None) -> List[Dict]:
    """
    Filter catalog entries by category.
    
    Args:
        catalog: Catalog dictionary with entries
        category: Category to filter by (Compute, Storage, Network, Licence) or None for all
    
    Returns:
        Filtered list of catalog entries
    """
    entries = catalog.get("entries", [])
    
    if not category or category.lower() == "all":
        return entries
    
    category_lower = category.lower()
    return [
        entry for entry in entries
        if entry.get("Category", "").lower() == category_lower
    ]


def get_catalog_categories(catalog: Dict) -> List[str]:
    """
    Get list of unique categories in catalog.
    
    Args:
        catalog: Catalog dictionary with entries
    
    Returns:
        List of unique category names
    """
    entries = catalog.get("entries", [])
    categories = set()
    
    for entry in entries:
        category = entry.get("Category")
        if category:
            categories.add(category)
    
    return sorted(list(categories))

