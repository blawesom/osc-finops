"""Unit tests for backend.services.consumption_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.services.consumption_service import (
    ConsumptionCache,
    consumption_cache,
    fetch_consumption,
    get_consumption,
    aggregate_by_granularity,
    filter_consumption,
    aggregate_by_dimension,
    calculate_totals,
    get_top_cost_drivers
)


class TestConsumptionCache:
    """Tests for ConsumptionCache class."""
    
    def test_init_default_ttl(self):
        """Test ConsumptionCache initialization with default TTL."""
        cache = ConsumptionCache()
        assert cache.ttl_seconds > 0
        assert cache._cache == {}
        assert cache._timestamps == {}
    
    def test_make_key(self):
        """Test _make_key creates correct cache key."""
        cache = ConsumptionCache()
        key = cache._make_key("account-123", "eu-west-2", "2024-01-01", "2024-01-31")
        assert "account-123" in key
        assert "eu-west-2" in key
        assert "2024-01-01" in key
        assert "2024-01-31" in key
    
    def test_make_key_no_region(self):
        """Test _make_key with None region."""
        cache = ConsumptionCache()
        key = cache._make_key("account-123", None, "2024-01-01", "2024-01-31")
        assert "all" in key
    
    @patch('backend.services.consumption_service.datetime')
    def test_get_not_cached(self, mock_datetime):
        """Test get when not cached."""
        cache = ConsumptionCache()
        assert cache.get("account-123", "eu-west-2", "2024-01-01", "2024-01-31") is None
    
    @patch('backend.services.consumption_service.datetime')
    def test_get_cached_valid(self, mock_datetime):
        """Test get when cached and not expired."""
        cache = ConsumptionCache(ttl_seconds=3600)
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        data = {"entries": []}
        cache.set("account-123", "eu-west-2", "2024-01-01", "2024-01-31", data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=1800)
        
        result = cache.get("account-123", "eu-west-2", "2024-01-01", "2024-01-31")
        assert result == data
    
    @patch('backend.services.consumption_service.datetime')
    def test_get_cached_expired(self, mock_datetime):
        """Test get when cached but expired."""
        cache = ConsumptionCache(ttl_seconds=3600)
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        data = {"entries": []}
        cache.set("account-123", "eu-west-2", "2024-01-01", "2024-01-31", data)
        mock_datetime.utcnow.return_value = now + timedelta(seconds=3700)
        
        result = cache.get("account-123", "eu-west-2", "2024-01-01", "2024-01-31")
        assert result is None
    
    @patch('backend.services.consumption_service.datetime')
    def test_set(self, mock_datetime):
        """Test set stores data with timestamp."""
        cache = ConsumptionCache()
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        data = {"entries": []}
        cache.set("account-123", "eu-west-2", "2024-01-01", "2024-01-31", data)
        
        assert len(cache._cache) == 1
        assert len(cache._timestamps) == 1
    
    def test_invalidate_specific_account(self):
        """Test invalidate for specific account."""
        cache = ConsumptionCache()
        cache.set("account-1", "eu-west-2", "2024-01-01", "2024-01-31", {"entries": []})
        cache.set("account-2", "eu-west-2", "2024-01-01", "2024-01-31", {"entries": []})
        
        cache.invalidate(account_id="account-1")
        
        assert len(cache._cache) == 1
        assert "account-2" in list(cache._cache.keys())[0]
    
    def test_invalidate_all(self):
        """Test invalidate for all."""
        cache = ConsumptionCache()
        cache.set("account-1", "eu-west-2", "2024-01-01", "2024-01-31", {"entries": []})
        cache.set("account-2", "us-west-1", "2024-01-01", "2024-01-31", {"entries": []})
        
        cache.invalidate()
        
        assert len(cache._cache) == 0
    
    @patch('backend.services.consumption_service.datetime')
    def test_is_cached_true(self, mock_datetime):
        """Test is_cached returns True when cached."""
        cache = ConsumptionCache(ttl_seconds=3600)
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        cache.set("account-123", "eu-west-2", "2024-01-01", "2024-01-31", {"entries": []})
        mock_datetime.utcnow.return_value = now + timedelta(seconds=1800)
        
        assert cache.is_cached("account-123", "eu-west-2", "2024-01-01", "2024-01-31") is True


class TestFetchConsumption:
    """Tests for fetch_consumption function."""
    
    @patch('backend.services.consumption_service.get_catalog')
    @patch('backend.services.consumption_service.Gateway')
    @patch('backend.services.consumption_service.datetime')
    def test_fetch_consumption_success(self, mock_datetime, mock_gateway_class, mock_get_catalog):
        """Test successful consumption fetch."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        mock_gateway.ReadConsumptionAccount.return_value = {
            "ConsumptionEntries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-02T00:00:00Z", "Price": 100.0}
            ]
        }
        mock_get_catalog.return_value = {"currency": "EUR"}
        
        result = fetch_consumption("access_key", "secret_key", "eu-west-2", "2024-01-01", "2024-01-31")
        
        assert result["from_date"] == "2024-01-01"
        assert result["to_date"] == "2024-01-31"
        assert result["region"] == "eu-west-2"
        assert result["currency"] == "EUR"
        assert len(result["entries"]) == 1
        assert result["entry_count"] == 1
        mock_gateway.ReadConsumptionAccount.assert_called_once_with(
            FromDate="2024-01-01",
            ToDate="2024-01-31",
            ShowPrice=True
        )
    
    def test_fetch_consumption_invalid_date_format(self):
        """Test fetch_consumption with invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            fetch_consumption("key", "secret", "eu-west-2", "invalid", "2024-01-31")
    
    def test_fetch_consumption_from_after_to(self):
        """Test fetch_consumption with from_date after to_date."""
        with pytest.raises(ValueError, match="from_date must be <= to_date"):
            fetch_consumption("key", "secret", "eu-west-2", "2024-01-31", "2024-01-01")
    
    @patch('backend.services.consumption_service.get_catalog')
    @patch('backend.services.consumption_service.Gateway')
    def test_fetch_consumption_adds_region(self, mock_gateway_class, mock_get_catalog):
        """Test fetch_consumption adds region to entries."""
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        mock_gateway.ReadConsumptionAccount.return_value = {
            "ConsumptionEntries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-02T00:00:00Z"}
            ]
        }
        mock_get_catalog.return_value = {"currency": "EUR"}
        
        result = fetch_consumption("key", "secret", "eu-west-2", "2024-01-01", "2024-01-31")
        
        assert result["entries"][0]["Region"] == "eu-west-2"
    
    @patch('backend.services.consumption_service.get_catalog')
    @patch('backend.services.consumption_service.Gateway')
    def test_fetch_consumption_catalog_fallback(self, mock_gateway_class, mock_get_catalog):
        """Test fetch_consumption falls back to EUR if catalog fails."""
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        mock_gateway.ReadConsumptionAccount.return_value = {"ConsumptionEntries": []}
        mock_get_catalog.side_effect = Exception("Catalog error")
        
        result = fetch_consumption("key", "secret", "eu-west-2", "2024-01-01", "2024-01-31")
        
        assert result["currency"] == "EUR"
    
    @patch('backend.services.consumption_service.Gateway')
    def test_fetch_consumption_api_error(self, mock_gateway_class):
        """Test fetch_consumption handles API errors."""
        mock_gateway = Mock()
        mock_gateway_class.return_value = mock_gateway
        mock_gateway.ReadConsumptionAccount.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="Failed to fetch consumption"):
            fetch_consumption("key", "secret", "eu-west-2", "2024-01-01", "2024-01-31")


class TestGetConsumption:
    """Tests for get_consumption function."""
    
    @patch('backend.services.consumption_service.fetch_consumption')
    @patch('backend.services.consumption_service.consumption_cache')
    def test_get_consumption_from_cache(self, mock_cache, mock_fetch):
        """Test get_consumption returns cached data."""
        cached_data = {"entries": [], "from_date": "2024-01-01"}
        mock_cache.get.return_value = cached_data
        
        result = get_consumption("key", "secret", "eu-west-2", "account-123", "2024-01-01", "2024-01-31")
        
        assert result == cached_data
        mock_fetch.assert_not_called()
    
    @patch('backend.services.consumption_service.fetch_consumption')
    @patch('backend.services.consumption_service.consumption_cache')
    def test_get_consumption_fetches_when_not_cached(self, mock_cache, mock_fetch):
        """Test get_consumption fetches when not cached."""
        mock_cache.get.return_value = None
        fetched_data = {"entries": [], "from_date": "2024-01-01"}
        mock_fetch.return_value = fetched_data
        
        result = get_consumption("key", "secret", "eu-west-2", "account-123", "2024-01-01", "2024-01-31")
        
        assert result == fetched_data
        mock_fetch.assert_called_once()
        mock_cache.set.assert_called_once()
    
    @patch('backend.services.consumption_service.fetch_consumption')
    @patch('backend.services.consumption_service.consumption_cache')
    def test_get_consumption_force_refresh(self, mock_cache, mock_fetch):
        """Test get_consumption with force_refresh bypasses cache."""
        cached_data = {"entries": []}
        fetched_data = {"entries": [{"new": "data"}]}
        mock_cache.get.return_value = cached_data
        mock_fetch.return_value = fetched_data
        
        result = get_consumption("key", "secret", "eu-west-2", "account-123", "2024-01-01", "2024-01-31", force_refresh=True)
        
        assert result == fetched_data
        mock_cache.get.assert_not_called()
        mock_fetch.assert_called_once()


class TestAggregateByGranularity:
    """Tests for aggregate_by_granularity function."""
    
    def test_aggregate_by_day(self):
        """Test aggregation by day."""
        consumption_data = {
            "entries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-01T23:59:59Z", "Price": 100.0},
                {"FromDate": "2024-01-02T00:00:00Z", "ToDate": "2024-01-02T23:59:59Z", "Price": 200.0}
            ]
        }
        
        result = aggregate_by_granularity(consumption_data, "day")
        
        assert len(result) == 2
        assert result[0]["from_date"] == "2024-01-01"
        assert result[0]["price"] == 100.0
    
    def test_aggregate_by_week(self):
        """Test aggregation by week."""
        consumption_data = {
            "entries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-07T23:59:59Z", "Price": 700.0}
            ]
        }
        
        result = aggregate_by_granularity(consumption_data, "week")
        
        assert len(result) >= 1
        assert "from_date" in result[0]
        assert "price" in result[0]
    
    def test_aggregate_by_month(self):
        """Test aggregation by month."""
        consumption_data = {
            "entries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-31T23:59:59Z", "Price": 3100.0}
            ]
        }
        
        result = aggregate_by_granularity(consumption_data, "month")
        
        assert len(result) >= 1
        assert "from_date" in result[0]
        assert "price" in result[0]
    
    def test_aggregate_empty_entries(self):
        """Test aggregation with empty entries."""
        consumption_data = {"entries": []}
        
        result = aggregate_by_granularity(consumption_data, "day")
        
        assert result == []


class TestFilterConsumption:
    """Tests for filter_consumption function."""
    
    def test_filter_by_region(self):
        """Test filtering by region."""
        consumption_data = {
            "entries": [
                {"Zone": "eu-west-2a", "Price": 100.0, "Region": "eu-west-2"},
                {"Zone": "us-west-1a", "Price": 50.0, "Region": "us-west-1"}
            ],
            "region": "eu-west-2"
        }
        
        from backend.services.consumption_service import filter_consumption
        result = filter_consumption(consumption_data, region="eu-west-2")
        
        assert len(result["entries"]) == 1
        assert result["entries"][0]["Zone"].startswith("eu-west-2")
    
    def test_filter_by_service(self):
        """Test filtering by service."""
        consumption_data = {
            "entries": [
                {"Service": "TinaOS-FCU", "Price": 100.0, "Region": "eu-west-2"},
                {"Service": "TinaOS-OOS", "Price": 50.0, "Region": "eu-west-2"}
            ],
            "region": "eu-west-2"
        }
        
        from backend.services.consumption_service import filter_consumption
        result = filter_consumption(consumption_data, service="TinaOS-FCU")
        
        assert len(result["entries"]) == 1
        assert result["entries"][0]["Service"] == "TinaOS-FCU"
    
    def test_filter_by_resource_type(self):
        """Test filtering by resource type."""
        consumption_data = {
            "entries": [
                {"Type": "VM", "Price": 100.0, "Region": "eu-west-2"},
                {"Type": "Storage", "Price": 50.0, "Region": "eu-west-2"}
            ],
            "region": "eu-west-2"
        }
        
        from backend.services.consumption_service import filter_consumption
        result = filter_consumption(consumption_data, resource_type="VM")
        
        assert len(result["entries"]) == 1
        assert result["entries"][0]["Type"] == "VM"
    
    def test_filter_no_filters(self):
        """Test filtering with no filters returns all."""
        consumption_data = {
            "entries": [
                {"Price": 100.0, "Region": "eu-west-2"},
                {"Price": 50.0, "Region": "eu-west-2"}
            ],
            "region": "eu-west-2"
        }
        
        from backend.services.consumption_service import filter_consumption
        result = filter_consumption(consumption_data)
        
        assert len(result["entries"]) == 2


class TestAggregateByDimension:
    """Tests for aggregate_by_dimension function."""
    
    def test_aggregate_by_resource_type(self):
        """Test aggregation by resource_type."""
        consumption_data = {
            "entries": [
                {"Type": "VM1", "Price": 100.0},
                {"Type": "Storage", "Price": 50.0},
                {"Type": "VM1", "Price": 75.0}
            ],
            "region": "eu-west-2"
        }
        
        result = aggregate_by_dimension(consumption_data, "resource_type")
        
        assert len(result) == 2
        vm_total = next((item for item in result if item["resource_type"] == "VM1"), None)
        assert vm_total is not None
        assert vm_total["price"] == 175.0
    
    def test_aggregate_by_region(self):
        """Test aggregation by region."""
        consumption_data = {
            "entries": [
                {"Zone": "eu-west-2a", "Price": 100.0},
                {"Zone": "us-west-1a", "Price": 50.0},
                {"Zone": "eu-west-2b", "Price": 75.0}
            ],
            "region": "eu-west-2"
        }
        
        result = aggregate_by_dimension(consumption_data, "region")
        
        assert len(result) >= 1
        # Region aggregation extracts region from zone
        eu_total = next((item for item in result if "eu-west-2" in item.get("region", "")), None)
        if eu_total:
            assert eu_total["price"] > 0


class TestCalculateTotals:
    """Tests for calculate_totals function."""
    
    def test_calculate_totals(self):
        """Test calculating totals from consumption data."""
        consumption_data = {
            "entries": [
                {"Price": 100.0, "Value": 10.0},
                {"Price": 50.0, "Value": 5.0},
                {"Price": 25.0, "Value": 2.5}
            ]
        }
        
        result = calculate_totals(consumption_data)
        
        assert result["total_price"] == 175.0
        assert result["total_value"] == 17.5
        assert result["entry_count"] == 3
    
    def test_calculate_totals_empty(self):
        """Test calculating totals with empty entries."""
        consumption_data = {
            "entries": []
        }
        
        result = calculate_totals(consumption_data)
        
        assert result["total_price"] == 0.0
        assert result["total_value"] == 0.0
        assert result["entry_count"] == 0


class TestGetTopCostDrivers:
    """Tests for get_top_cost_drivers function."""
    
    def test_get_top_cost_drivers(self):
        """Test getting top cost drivers."""
        consumption_data = {
            "entries": [
                {"Service": "S1", "Type": "VM1", "Operation": "Op1", "Price": 500.0},
                {"Service": "S2", "Type": "VM2", "Operation": "Op2", "Price": 300.0},
                {"Service": "S3", "Type": "Storage", "Operation": "Op3", "Price": 200.0},
                {"Service": "S4", "Type": "VM3", "Operation": "Op4", "Price": 100.0}
            ]
        }
        
        result = get_top_cost_drivers(consumption_data, limit=3)
        
        assert len(result) == 3
        assert result[0]["total_price"] == 500.0
        assert "service" in result[0]
        assert "resource_type" in result[0]
    
    def test_get_top_cost_drivers_default_limit(self):
        """Test get_top_cost_drivers with default limit."""
        consumption_data = {
            "entries": [
                {"Service": f"S{i}", "Type": f"VM{i}", "Operation": f"Op{i}", "Price": float(100 - i)}
                for i in range(15)
            ]
        }
        
        result = get_top_cost_drivers(consumption_data)
        
        assert len(result) == 10  # Default limit
    
    def test_get_top_cost_drivers_empty(self):
        """Test get_top_cost_drivers with empty entries."""
        consumption_data = {"entries": []}
        
        result = get_top_cost_drivers(consumption_data)
        
        assert result == []

