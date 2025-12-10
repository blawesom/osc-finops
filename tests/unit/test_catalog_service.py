"""Unit tests for backend.services.catalog_service."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

from backend.services.catalog_service import (
    CatalogCache,
    catalog_cache,
    _get_api_url,
    fetch_catalog,
    get_catalog,
    filter_catalog_by_category
)
from backend.config.settings import SUPPORTED_REGIONS, CATALOG_CACHE_TTL


class TestCatalogCache:
    """Tests for CatalogCache class."""
    
    def test_init_default_ttl(self):
        """Test CatalogCache initialization with default TTL."""
        cache = CatalogCache()
        assert cache.ttl_seconds == CATALOG_CACHE_TTL
        assert cache._cache == {}
        assert cache._timestamps == {}
    
    def test_init_custom_ttl(self):
        """Test CatalogCache initialization with custom TTL."""
        cache = CatalogCache(ttl_seconds=3600)
        assert cache.ttl_seconds == 3600
    
    @patch('backend.services.catalog_service.datetime')
    def test_get_not_cached(self, mock_datetime):
        """Test get when region is not cached."""
        cache = CatalogCache()
        assert cache.get("eu-west-2") is None
    
    @patch('backend.services.catalog_service.datetime')
    def test_get_cached_valid(self, mock_datetime):
        """Test get when region is cached and not expired."""
        cache = CatalogCache(ttl_seconds=3600)
        catalog_data = {"entries": [], "region": "eu-west-2"}
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        cache.set("eu-west-2", catalog_data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=1800)  # 30 min later
        
        result = cache.get("eu-west-2")
        assert result == catalog_data
    
    @patch('backend.services.catalog_service.datetime')
    def test_get_cached_expired(self, mock_datetime):
        """Test get when region is cached but expired."""
        cache = CatalogCache(ttl_seconds=3600)
        catalog_data = {"entries": [], "region": "eu-west-2"}
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        cache.set("eu-west-2", catalog_data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=3700)  # Expired
        
        result = cache.get("eu-west-2")
        assert result is None
        assert "eu-west-2" not in cache._cache
    
    @patch('backend.services.catalog_service.datetime')
    def test_set(self, mock_datetime):
        """Test set stores catalog with timestamp."""
        cache = CatalogCache()
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        catalog_data = {"entries": [], "region": "eu-west-2"}
        
        cache.set("eu-west-2", catalog_data)
        
        assert cache._cache["eu-west-2"] == catalog_data
        assert cache._timestamps["eu-west-2"] == now
    
    def test_invalidate_specific_region(self):
        """Test invalidate for specific region."""
        cache = CatalogCache()
        cache._cache["eu-west-2"] = {"entries": []}
        cache._cache["us-west-1"] = {"entries": []}
        cache._timestamps["eu-west-2"] = datetime.utcnow()
        cache._timestamps["us-west-1"] = datetime.utcnow()
        
        cache.invalidate("eu-west-2")
        
        assert "eu-west-2" not in cache._cache
        assert "us-west-1" in cache._cache
        assert "eu-west-2" not in cache._timestamps
    
    def test_invalidate_all(self):
        """Test invalidate for all regions."""
        cache = CatalogCache()
        cache._cache["eu-west-2"] = {"entries": []}
        cache._cache["us-west-1"] = {"entries": []}
        cache._timestamps["eu-west-2"] = datetime.utcnow()
        cache._timestamps["us-west-1"] = datetime.utcnow()
        
        cache.invalidate()
        
        assert len(cache._cache) == 0
        assert len(cache._timestamps) == 0
    
    @patch('backend.services.catalog_service.datetime')
    def test_is_cached_true(self, mock_datetime):
        """Test is_cached returns True when cached and valid."""
        cache = CatalogCache(ttl_seconds=3600)
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        catalog_data = {"entries": []}
        
        cache.set("eu-west-2", catalog_data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=1800)
        
        assert cache.is_cached("eu-west-2") is True
    
    @patch('backend.services.catalog_service.datetime')
    def test_is_cached_false_expired(self, mock_datetime):
        """Test is_cached returns False when expired."""
        cache = CatalogCache(ttl_seconds=3600)
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        catalog_data = {"entries": []}
        
        cache.set("eu-west-2", catalog_data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=3700)
        
        assert cache.is_cached("eu-west-2") is False
    
    def test_is_cached_false_not_cached(self):
        """Test is_cached returns False when not cached."""
        cache = CatalogCache()
        assert cache.is_cached("eu-west-2") is False


class TestGetApiUrl:
    """Tests for _get_api_url function."""
    
    def test_all_supported_regions(self):
        """Test _get_api_url for all supported regions."""
        for region in SUPPORTED_REGIONS:
            url = _get_api_url(region)
            assert url.startswith("https://")
            assert "api." in url
            assert region.replace("-", ".") in url or region in url
            assert url.endswith("/api/v1/ReadPublicCatalog")
    
    def test_unsupported_region(self):
        """Test _get_api_url raises ValueError for unsupported region."""
        with pytest.raises(ValueError, match="Unsupported region"):
            _get_api_url("invalid-region")


class TestFetchCatalog:
    """Tests for fetch_catalog function."""
    
    def test_unsupported_region(self):
        """Test fetch_catalog raises ValueError for unsupported region."""
        with pytest.raises(ValueError, match="Unsupported region"):
            fetch_catalog("invalid-region")
    
    @patch('backend.services.catalog_service.requests.post')
    @patch('backend.services.catalog_service.datetime')
    def test_fetch_catalog_success(self, mock_datetime, mock_post):
        """Test successful catalog fetch."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "Catalog": {
                "Entries": [
                    {"Category": "compute", "UnitPrice": 0.1, "Currency": "EUR"},
                    {"Category": "storage", "UnitPrice": 0.05, "Currency": "EUR"}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = fetch_catalog("eu-west-2")
        
        assert result["region"] == "eu-west-2"
        assert len(result["entries"]) == 2
        assert result["currency"] == "EUR"
        assert result["entry_count"] == 2
        assert "fetched_at" in result
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    
    @patch('backend.services.catalog_service.requests.post')
    @patch('backend.services.catalog_service.datetime')
    def test_fetch_catalog_no_currency_fallback(self, mock_datetime, mock_post):
        """Test catalog fetch with no currency falls back to EUR."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "Catalog": {
                "Entries": [
                    {"Category": "compute", "UnitPrice": 0.1}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = fetch_catalog("eu-west-2")
        
        assert result["currency"] == "EUR"
    
    @patch('backend.services.catalog_service.requests.post')
    @patch('backend.services.catalog_service.datetime')
    def test_fetch_catalog_empty_entries(self, mock_datetime, mock_post):
        """Test catalog fetch with empty entries."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_response = Mock()
        mock_response.json.return_value = {"Catalog": {"Entries": []}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = fetch_catalog("eu-west-2")
        
        assert result["entries"] == []
        assert result["entry_count"] == 0
        assert result["currency"] == "EUR"
    
    @patch('backend.services.catalog_service.requests.post')
    def test_fetch_catalog_request_exception(self, mock_post):
        """Test fetch_catalog handles RequestException."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        with pytest.raises(Exception, match="Failed to fetch catalog"):
            fetch_catalog("eu-west-2")
    
    @patch('backend.services.catalog_service.requests.post')
    def test_fetch_catalog_http_error(self, mock_post):
        """Test fetch_catalog handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to fetch catalog"):
            fetch_catalog("eu-west-2")
    
    @patch('backend.services.catalog_service.requests.post')
    def test_fetch_catalog_generic_exception(self, mock_post):
        """Test fetch_catalog handles generic exceptions."""
        mock_post.side_effect = Exception("Unexpected error")
        
        with pytest.raises(Exception, match="Failed to fetch catalog"):
            fetch_catalog("eu-west-2")


class TestGetCatalog:
    """Tests for get_catalog function."""
    
    @patch('backend.services.catalog_service.fetch_catalog')
    @patch('backend.services.catalog_service.catalog_cache')
    def test_get_catalog_from_cache(self, mock_cache, mock_fetch):
        """Test get_catalog returns cached catalog when available."""
        cached_catalog = {"region": "eu-west-2", "entries": []}
        mock_cache.get.return_value = cached_catalog
        
        result = get_catalog("eu-west-2")
        
        assert result == cached_catalog
        mock_fetch.assert_not_called()
    
    @patch('backend.services.catalog_service.fetch_catalog')
    @patch('backend.services.catalog_service.catalog_cache')
    def test_get_catalog_fetches_when_not_cached(self, mock_cache, mock_fetch):
        """Test get_catalog fetches when not cached."""
        mock_cache.get.return_value = None
        fetched_catalog = {"region": "eu-west-2", "entries": []}
        mock_fetch.return_value = fetched_catalog
        
        result = get_catalog("eu-west-2")
        
        assert result == fetched_catalog
        mock_fetch.assert_called_once_with("eu-west-2")
        mock_cache.set.assert_called_once_with("eu-west-2", fetched_catalog)
    
    @patch('backend.services.catalog_service.fetch_catalog')
    @patch('backend.services.catalog_service.catalog_cache')
    def test_get_catalog_force_refresh(self, mock_cache, mock_fetch):
        """Test get_catalog with force_refresh bypasses cache."""
        cached_catalog = {"region": "eu-west-2", "entries": []}
        fetched_catalog = {"region": "eu-west-2", "entries": [{"new": "data"}]}
        mock_cache.get.return_value = cached_catalog
        mock_fetch.return_value = fetched_catalog
        
        result = get_catalog("eu-west-2", force_refresh=True)
        
        assert result == fetched_catalog
        mock_cache.get.assert_not_called()
        mock_fetch.assert_called_once_with("eu-west-2")
        mock_cache.set.assert_called_once_with("eu-west-2", fetched_catalog)


class TestFilterCatalogByCategory:
    """Tests for filter_catalog_by_category function."""
    
    def test_filter_all_categories(self):
        """Test filter_catalog_by_category with None category returns all."""
        catalog = {
            "entries": [
                {"Category": "compute"},
                {"Category": "storage"},
                {"Category": "network"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, None)
        
        assert len(result) == 3
    
    def test_filter_all_explicit(self):
        """Test filter_catalog_by_category with 'all' returns all."""
        catalog = {
            "entries": [
                {"Category": "compute"},
                {"Category": "storage"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, "all")
        
        assert len(result) == 2
    
    def test_filter_compute_category(self):
        """Test filter_catalog_by_category filters by compute."""
        catalog = {
            "entries": [
                {"Category": "compute", "Type": "VM"},
                {"Category": "storage", "Type": "Volume"},
                {"Category": "compute", "Type": "GPU"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, "compute")
        
        assert len(result) == 2
        assert all(entry["Category"] == "compute" for entry in result)
    
    def test_filter_case_insensitive(self):
        """Test filter_catalog_by_category is case-insensitive."""
        catalog = {
            "entries": [
                {"Category": "Compute"},
                {"Category": "COMPUTE"},
                {"Category": "storage"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, "compute")
        
        assert len(result) == 2
    
    def test_filter_no_matches(self):
        """Test filter_catalog_by_category with no matches."""
        catalog = {
            "entries": [
                {"Category": "compute"},
                {"Category": "storage"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, "network")
        
        assert len(result) == 0
    
    def test_filter_empty_entries(self):
        """Test filter_catalog_by_category with empty entries."""
        catalog = {"entries": []}
        
        result = filter_catalog_by_category(catalog, "compute")
        
        assert len(result) == 0
    
    def test_filter_missing_category_field(self):
        """Test filter_catalog_by_category handles entries without Category."""
        catalog = {
            "entries": [
                {"Category": "compute"},
                {"Type": "Volume"},  # No Category field
                {"Category": "storage"}
            ]
        }
        
        result = filter_catalog_by_category(catalog, "compute")
        
        assert len(result) == 1



class TestCatalogServiceWithFixtures:
    """Tests for catalog service using fixture data."""
    
    def test_get_catalog_with_fixture_data(self, formatted_catalog_data):
        """Test get_catalog using fixture data."""
        if not formatted_catalog_data:
            pytest.skip("Catalog fixture not available")
        
        with patch('backend.services.catalog_service.catalog_cache') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            with patch('backend.services.catalog_service.fetch_catalog') as mock_fetch:
                mock_fetch.return_value = formatted_catalog_data
                
                result = get_catalog("eu-west-2", force_refresh=False)
                
                assert result is not None
                assert "entries" in result
                assert len(result["entries"]) > 0
                assert result["currency"] == "EUR"
    
    def test_filter_catalog_by_category_with_fixture(self, formatted_catalog_data):
        """Test filtering catalog by category using fixture data."""
        if not formatted_catalog_data:
            pytest.skip("Catalog fixture not available")
        
        # Filter for compute category (returns list, not dict)
        filtered = filter_catalog_by_category(formatted_catalog_data, "compute")
        
        assert isinstance(filtered, list)
        # All entries should be compute category
        for entry in filtered:
            assert entry.get("Category", "").lower() == "compute"
    
    def test_catalog_fixture_structure(self, catalog_fixture_data):
        """Test that catalog fixture has expected structure."""
        if not catalog_fixture_data:
            pytest.skip("Catalog fixture not available")
        
        assert "Catalog" in catalog_fixture_data
        assert "Entries" in catalog_fixture_data["Catalog"]
        entries = catalog_fixture_data["Catalog"]["Entries"]
        assert len(entries) > 0
        
        # Verify entry structure
        first_entry = entries[0]
        assert "UnitPrice" in first_entry
        assert "Type" in first_entry
        assert "Service" in first_entry
        assert "Operation" in first_entry
        assert "Category" in first_entry
    
    def test_catalog_fixture_has_multiple_categories(self, formatted_catalog_data):
        """Test that catalog fixture contains multiple resource categories."""
        if not formatted_catalog_data:
            pytest.skip("Catalog fixture not available")
        
        categories = set()
        for entry in formatted_catalog_data["entries"]:
            category = entry.get("Category", "").lower()
            if category:
                categories.add(category)
        
        # Should have multiple categories
        assert len(categories) > 1
        assert "compute" in categories or "storage" in categories or "network" in categories
