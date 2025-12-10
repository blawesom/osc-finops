"""Unit tests for backend.services.consumption_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, date

from backend.services.consumption_service import (
    ConsumptionCache,
    consumption_cache,
    fetch_consumption,
    get_consumption,
    aggregate_by_granularity,
    filter_consumption,
    aggregate_by_dimension,
    calculate_totals,
    round_to_period_start,
    round_to_period_end,
    get_consumption_granularity_from_budget,
    get_monthly_week_start,
    calculate_monthly_weeks,
    split_periods_at_budget_boundaries
)


class TestConsumptionCache:
    """Tests for ConsumptionCache class."""
    
    def test_init_default_ttl(self):
        """Test ConsumptionCache initialization with default TTL."""
        cache = ConsumptionCache()
        assert cache.ttl_seconds > 0
        assert cache._cache == {}
        assert cache._timestamps == {}
    
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
    @patch('backend.services.consumption_service.process_and_log_api_call')
    @patch('backend.services.consumption_service.create_logged_gateway')
    @patch('backend.services.consumption_service.datetime')
    def test_fetch_consumption_success(self, mock_datetime, mock_create_gateway, mock_process_api, mock_get_catalog):
        """Test successful consumption fetch."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_api.return_value = {
            "ConsumptionEntries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-02T00:00:00Z", "Value": 10.0, "UnitPrice": 10.0}
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
    
    def test_fetch_consumption_invalid_date_format(self):
        """Test fetch_consumption with invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            fetch_consumption("key", "secret", "eu-west-2", "invalid", "2024-01-31")
    
    def test_fetch_consumption_from_after_to(self):
        """Test fetch_consumption with from_date after to_date."""
        with pytest.raises(ValueError, match="to_date must be > from_date"):
            fetch_consumption("key", "secret", "eu-west-2", "2024-01-31", "2024-01-01")
    
    @patch('backend.services.consumption_service.get_catalog')
    @patch('backend.services.consumption_service.process_and_log_api_call')
    @patch('backend.services.consumption_service.create_logged_gateway')
    def test_fetch_consumption_adds_region(self, mock_create_gateway, mock_process_api, mock_get_catalog):
        """Test fetch_consumption adds region to entries."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_api.return_value = {
            "ConsumptionEntries": [
                {"FromDate": "2024-01-01T00:00:00Z", "ToDate": "2024-01-02T00:00:00Z", "Value": 10.0, "UnitPrice": 10.0}
            ]
        }
        mock_get_catalog.return_value = {"currency": "EUR"}
        
        result = fetch_consumption("key", "secret", "eu-west-2", "2024-01-01", "2024-01-31")
        
        assert result["entries"][0]["Region"] == "eu-west-2"
    
    @patch('backend.services.consumption_service.get_catalog')
    @patch('backend.services.consumption_service.process_and_log_api_call')
    @patch('backend.services.consumption_service.create_logged_gateway')
    def test_fetch_consumption_catalog_fallback(self, mock_create_gateway, mock_process_api, mock_get_catalog):
        """Test fetch_consumption falls back to EUR if catalog fails."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_api.return_value = {"ConsumptionEntries": []}
        mock_get_catalog.side_effect = Exception("Catalog error")
        
        result = fetch_consumption("key", "secret", "eu-west-2", "2024-01-01", "2024-01-31")
        
        assert result["currency"] == "EUR"
    
    @patch('backend.services.consumption_service.process_and_log_api_call')
    @patch('backend.services.consumption_service.create_logged_gateway')
    def test_fetch_consumption_api_error(self, mock_create_gateway, mock_process_api):
        """Test fetch_consumption handles API errors."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_api.side_effect = Exception("API Error")
        
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


class TestRoundToPeriodStart:
    """Tests for round_to_period_start function."""
    
    def test_round_to_period_start_day(self):
        """Test rounding to day period start."""
        result = round_to_period_start("2024-01-15", "day")
        assert result == "2024-01-15"
    
    def test_round_to_period_start_week(self):
        """Test rounding to week period start."""
        result = round_to_period_start("2024-01-15", "week")
        assert result == "2024-01-15"  # Should round to week start (15th is week 3 start)
    
    def test_round_to_period_start_week_mid_week(self):
        """Test rounding to week start from mid-week."""
        result = round_to_period_start("2024-01-10", "week")
        assert result == "2024-01-08"  # Week 2 starts on 8th
    
    def test_round_to_period_start_month(self):
        """Test rounding to month period start."""
        result = round_to_period_start("2024-01-15", "month")
        assert result == "2024-01-01"
    
    def test_round_to_period_start_invalid_granularity(self):
        """Test with invalid granularity returns original."""
        result = round_to_period_start("2024-01-15", "invalid")
        assert result == "2024-01-15"
    
    def test_round_to_period_start_invalid_date(self):
        """Test with invalid date format returns original."""
        result = round_to_period_start("invalid-date", "day")
        assert result == "invalid-date"


class TestRoundToPeriodEnd:
    """Tests for round_to_period_end function."""
    
    def test_round_to_period_end_day(self):
        """Test rounding to day period end (exclusive)."""
        result = round_to_period_end("2024-01-15", "day")
        assert result == "2024-01-16"  # Next day (exclusive)
    
    def test_round_to_period_end_week(self):
        """Test rounding to week period end."""
        result = round_to_period_end("2024-01-10", "week")
        assert result == "2024-01-15"  # Next week start (exclusive)
    
    def test_round_to_period_end_week_week_4(self):
        """Test rounding week 4 to next month."""
        result = round_to_period_end("2024-01-25", "week")
        assert result == "2024-02-01"  # Next month start
    
    def test_round_to_period_end_month(self):
        """Test rounding to month period end."""
        result = round_to_period_end("2024-01-15", "month")
        assert result == "2024-02-01"  # Next month start (exclusive)
    
    def test_round_to_period_end_month_december(self):
        """Test rounding December to next year."""
        result = round_to_period_end("2024-12-15", "month")
        assert result == "2025-01-01"
    
    def test_round_to_period_end_invalid_granularity(self):
        """Test with invalid granularity returns original."""
        result = round_to_period_end("2024-01-15", "invalid")
        assert result == "2024-01-15"
    
    def test_round_to_period_end_invalid_date(self):
        """Test with invalid date format returns original."""
        result = round_to_period_end("invalid-date", "day")
        assert result == "invalid-date"


class TestGetConsumptionGranularityFromBudget:
    """Tests for get_consumption_granularity_from_budget function."""
    
    def test_get_consumption_granularity_yearly(self):
        """Test yearly budget returns monthly granularity."""
        result = get_consumption_granularity_from_budget("yearly")
        assert result == "month"
    
    def test_get_consumption_granularity_quarterly(self):
        """Test quarterly budget returns monthly granularity."""
        result = get_consumption_granularity_from_budget("quarterly")
        assert result == "month"
    
    def test_get_consumption_granularity_monthly(self):
        """Test monthly budget returns weekly granularity."""
        result = get_consumption_granularity_from_budget("monthly")
        assert result == "week"
    
    def test_get_consumption_granularity_weekly(self):
        """Test weekly budget returns daily granularity."""
        result = get_consumption_granularity_from_budget("weekly")
        assert result == "day"
    
    def test_get_consumption_granularity_unknown(self):
        """Test unknown period type returns daily granularity."""
        result = get_consumption_granularity_from_budget("unknown")
        assert result == "day"


class TestGetMonthlyWeekStart:
    """Tests for get_monthly_week_start function."""
    
    def test_get_monthly_week_start_week_1(self):
        """Test week 1 start (days 1-7)."""
        result = get_monthly_week_start(date(2024, 1, 5))
        assert result == date(2024, 1, 1)
    
    def test_get_monthly_week_start_week_2(self):
        """Test week 2 start (days 8-14)."""
        result = get_monthly_week_start(date(2024, 1, 10))
        assert result == date(2024, 1, 8)
    
    def test_get_monthly_week_start_week_3(self):
        """Test week 3 start (days 15-21)."""
        result = get_monthly_week_start(date(2024, 1, 18))
        assert result == date(2024, 1, 15)
    
    def test_get_monthly_week_start_week_4(self):
        """Test week 4 start (days 22-end)."""
        result = get_monthly_week_start(date(2024, 1, 25))
        assert result == date(2024, 1, 22)
    
    def test_get_monthly_week_start_exact_boundaries(self):
        """Test exact week boundaries."""
        assert get_monthly_week_start(date(2024, 1, 1)) == date(2024, 1, 1)
        assert get_monthly_week_start(date(2024, 1, 7)) == date(2024, 1, 1)
        assert get_monthly_week_start(date(2024, 1, 8)) == date(2024, 1, 8)
        assert get_monthly_week_start(date(2024, 1, 14)) == date(2024, 1, 8)
        assert get_monthly_week_start(date(2024, 1, 15)) == date(2024, 1, 15)
        assert get_monthly_week_start(date(2024, 1, 21)) == date(2024, 1, 15)
        assert get_monthly_week_start(date(2024, 1, 22)) == date(2024, 1, 22)
        assert get_monthly_week_start(date(2024, 1, 31)) == date(2024, 1, 22)


class TestCalculateMonthlyWeeks:
    """Tests for calculate_monthly_weeks function."""
    
    def test_calculate_monthly_weeks_january(self):
        """Test calculating weeks for January (31 days)."""
        result = calculate_monthly_weeks(2024, 1)
        assert len(result) == 4
        assert result[0]["from_date"] == "2024-01-01"
        assert result[0]["to_date"] == "2024-01-08"  # Exclusive
        assert result[3]["from_date"] == "2024-01-22"
        assert result[3]["to_date"] == "2024-02-01"  # Exclusive
    
    def test_calculate_monthly_weeks_february_leap_year(self):
        """Test calculating weeks for February in leap year (29 days)."""
        result = calculate_monthly_weeks(2024, 2)
        assert len(result) == 4
        assert result[3]["from_date"] == "2024-02-22"
        assert result[3]["to_date"] == "2024-03-01"  # Exclusive
    
    def test_calculate_monthly_weeks_february_non_leap(self):
        """Test calculating weeks for February in non-leap year (28 days)."""
        result = calculate_monthly_weeks(2023, 2)
        assert len(result) == 4
        assert result[3]["from_date"] == "2023-02-22"
        assert result[3]["to_date"] == "2023-03-01"  # Exclusive
    
    def test_calculate_monthly_weeks_april(self):
        """Test calculating weeks for April (30 days)."""
        result = calculate_monthly_weeks(2024, 4)
        assert len(result) == 4
        assert result[3]["to_date"] == "2024-05-01"  # Exclusive
    
    def test_calculate_monthly_weeks_short_month(self):
        """Test calculating weeks for a very short month (if such existed)."""
        # All months have at least 28 days, so all should have 4 weeks
        result = calculate_monthly_weeks(2023, 2)  # 28 days
        assert len(result) == 4


class TestSplitPeriodsAtBudgetBoundaries:
    """Tests for split_periods_at_budget_boundaries function."""
    
    def test_split_periods_monthly_budget(self):
        """Test splitting periods with monthly budget."""
        periods = [
            {"from_date": "2024-01-15", "to_date": "2024-02-15", "cost": 100.0}
        ]
        budget = Mock()
        budget.period_type = "monthly"
        budget.start_date = date(2024, 1, 1)
        
        result = split_periods_at_budget_boundaries(periods, budget)
        
        # Should split at Feb 1 boundary
        assert len(result) > 1
        assert any(p["to_date"] == "2024-02-01" for p in result)
    
    def test_split_periods_quarterly_budget(self):
        """Test splitting periods with quarterly budget."""
        periods = [
            {"from_date": "2024-01-15", "to_date": "2024-04-15", "cost": 100.0}
        ]
        budget = Mock()
        budget.period_type = "quarterly"
        budget.start_date = date(2024, 1, 1)
        
        result = split_periods_at_budget_boundaries(periods, budget)
        
        # Should split at quarterly boundaries (Apr 1)
        assert len(result) > 1
    
    def test_split_periods_yearly_budget(self):
        """Test splitting periods with yearly budget."""
        periods = [
            {"from_date": "2024-06-15", "to_date": "2025-06-15", "cost": 100.0}
        ]
        budget = Mock()
        budget.period_type = "yearly"
        budget.start_date = date(2024, 1, 1)
        
        result = split_periods_at_budget_boundaries(periods, budget)
        
        # Should split at year boundary (2025-01-01)
        assert len(result) > 1
    
    def test_split_periods_no_boundaries(self):
        """Test periods that don't cross boundaries."""
        periods = [
            {"from_date": "2024-01-15", "to_date": "2024-01-20", "cost": 100.0}
        ]
        budget = Mock()
        budget.period_type = "monthly"
        budget.start_date = date(2024, 1, 1)
        
        result = split_periods_at_budget_boundaries(periods, budget)
        
        # Should remain unchanged
        assert len(result) == 1
        assert result[0] == periods[0]
    
    def test_split_periods_empty(self):
        """Test with empty periods."""
        result = split_periods_at_budget_boundaries([], Mock())
        assert result == []
    
    def test_split_periods_no_budget(self):
        """Test with no budget."""
        periods = [{"from_date": "2024-01-01", "to_date": "2024-01-31", "cost": 100.0}]
        result = split_periods_at_budget_boundaries(periods, None)
        assert result == periods



class TestConsumptionServiceWithFixtures:
    """Tests for consumption service using fixture data."""
    
    def test_get_consumption_with_fixture_data(self, formatted_consumption_data):
        """Test get_consumption using fixture data."""
        if not formatted_consumption_data:
            pytest.skip("Consumption fixture not available")
        
        with patch('backend.services.consumption_service.consumption_cache') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            with patch('backend.services.consumption_service.fetch_consumption') as mock_fetch:
                mock_fetch.return_value = formatted_consumption_data
                
                result = get_consumption(
                    "access_key",
                    "secret_key",
                    "eu-west-2",
                    "account-123",
                    "2025-12-01",
                    "2025-12-02",
                    granularity="day"
                )
                
                assert result is not None
                assert "entries" in result
                assert len(result["entries"]) > 0
    
    def test_consumption_fixture_structure(self, consumption_fixture_data):
        """Test that consumption fixture has expected structure."""
        if not consumption_fixture_data:
            pytest.skip("Consumption fixture not available")
        
        assert "ConsumptionEntries" in consumption_fixture_data
        entries = consumption_fixture_data["ConsumptionEntries"]
        assert len(entries) > 0
        
        # Verify entry structure
        first_entry = entries[0]
        assert "Type" in first_entry
        assert "Value" in first_entry
        assert "FromDate" in first_entry
        assert "ToDate" in first_entry
        assert "AccountId" in first_entry
    
    def test_aggregate_consumption_with_fixture(self, formatted_consumption_data):
        """Test aggregating consumption data from fixture."""
        if not formatted_consumption_data:
            pytest.skip("Consumption fixture not available")
        
        # Aggregate by resource type
        aggregated = aggregate_by_dimension(
            formatted_consumption_data["entries"],
            "resource_type"
        )
        
        assert len(aggregated) > 0
        # Each aggregated entry should have a resource_type
        for entry in aggregated:
            assert "resource_type" in entry or "Type" in entry
    
    def test_filter_consumption_with_fixture(self, formatted_consumption_data):
        """Test filtering consumption data from fixture."""
        if not formatted_consumption_data:
            pytest.skip("Consumption fixture not available")
        
        # Filter by service
        filtered = filter_consumption(
            formatted_consumption_data["entries"],
            service="TinaOS-FCU"
        )
        
        # All entries should match the filter
        for entry in filtered:
            assert entry.get("Service", "") == "TinaOS-FCU"
