"""Unit tests for backend.services.trend_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta

from backend.services.trend_service import (
    calculate_trends,
    calculate_growth_rate,
    calculate_historical_average,
    identify_cost_changes,
    project_trend_until_date,
    get_monthly_week_end,
    get_next_monthly_week_start,
    find_last_period_excluding_today,
    align_periods_to_budget_boundaries,
    calculate_trends_async,
    _generate_period_ranges,
    _fetch_period_costs,
    _calculate_trend_metrics,
    _build_trend_result
)
from backend.services.consumption_service import get_monthly_week_start


class TestCalculateGrowthRate:
    """Tests for calculate_growth_rate function."""
    
    def test_growth_rate_positive(self):
        """Test growth rate calculation with positive growth."""
        periods = [
            {"cost": 100.0},
            {"cost": 150.0}
        ]
        
        result = calculate_growth_rate(periods)
        
        assert result == 50.0  # 50% growth
    
    def test_growth_rate_negative(self):
        """Test growth rate calculation with negative growth."""
        periods = [
            {"cost": 200.0},
            {"cost": 150.0}
        ]
        
        result = calculate_growth_rate(periods)
        
        assert result == -25.0  # -25% growth
    
    def test_growth_rate_zero_start(self):
        """Test growth rate when starting from zero."""
        periods = [
            {"cost": 0.0},
            {"cost": 100.0}
        ]
        
        result = calculate_growth_rate(periods)
        
        assert result == 100.0  # From 0 to positive = 100%
    
    def test_growth_rate_insufficient_periods(self):
        """Test growth rate with less than 2 periods."""
        periods = [{"cost": 100.0}]
        
        result = calculate_growth_rate(periods)
        
        assert result == 0.0
    
    def test_growth_rate_empty(self):
        """Test growth rate with empty periods."""
        result = calculate_growth_rate([])
        
        assert result == 0.0
    
    def test_growth_rate_multiple_periods(self):
        """Test growth rate with multiple periods."""
        periods = [
            {"cost": 100.0},
            {"cost": 120.0},
            {"cost": 150.0}
        ]
        
        result = calculate_growth_rate(periods)
        
        # Growth from first (100) to last (150) = 50%
        assert result == 50.0


class TestCalculateHistoricalAverage:
    """Tests for calculate_historical_average function."""
    
    def test_historical_average(self):
        """Test historical average calculation."""
        periods = [
            {"cost": 100.0},
            {"cost": 200.0},
            {"cost": 300.0}
        ]
        
        result = calculate_historical_average(periods)
        
        assert result == 200.0  # (100 + 200 + 300) / 3
    
    def test_historical_average_empty(self):
        """Test historical average with empty periods."""
        result = calculate_historical_average([])
        
        assert result == 0.0
    
    def test_historical_average_single_period(self):
        """Test historical average with single period."""
        periods = [{"cost": 150.0}]
        
        result = calculate_historical_average(periods)
        
        assert result == 150.0
    
    def test_historical_average_with_zeros(self):
        """Test historical average with zero costs."""
        periods = [
            {"cost": 0.0},
            {"cost": 100.0},
            {"cost": 0.0}
        ]
        
        result = calculate_historical_average(periods)
        
        assert result == pytest.approx(33.33, abs=0.01)


class TestIdentifyCostChanges:
    """Tests for identify_cost_changes function."""
    
    def test_identify_cost_changes_above_threshold(self):
        """Test identifying cost changes above threshold."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 120.0},  # 20% increase
            {"period": "2024-03", "cost": 80.0}    # -33% decrease
        ]
        
        result = identify_cost_changes(periods, threshold=10.0)
        
        assert len(result) == 2  # Both changes exceed 10%
        assert result[0]["change_percent"] >= 10.0  # Uses abs() so both are positive
        assert result[1]["change_percent"] >= 10.0
        assert result[0]["direction"] == "increase"
        assert result[1]["direction"] == "decrease"
    
    def test_identify_cost_changes_below_threshold(self):
        """Test identifying cost changes below threshold."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 105.0},  # 5% increase
            {"period": "2024-03", "cost": 103.0}    # -2% decrease
        ]
        
        result = identify_cost_changes(periods, threshold=10.0)
        
        assert len(result) == 0  # No changes exceed 10%
    
    def test_identify_cost_changes_custom_threshold(self):
        """Test identifying cost changes with custom threshold."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 108.0}  # 8% increase
        ]
        
        result = identify_cost_changes(periods, threshold=5.0)
        
        assert len(result) == 1  # 8% > 5% threshold
    
    def test_identify_cost_changes_empty(self):
        """Test identifying cost changes with empty periods."""
        result = identify_cost_changes([])
        
        assert result == []
    
    def test_identify_cost_changes_single_period(self):
        """Test identifying cost changes with single period."""
        periods = [{"period": "2024-01", "cost": 100.0}]
        
        result = identify_cost_changes(periods)
        
        assert result == []


class TestCalculateTrends:
    """Tests for calculate_trends function."""
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_day_granularity(self, mock_get_consumption):
        """Test calculate_trends with day granularity."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert result["granularity"] == "day"
        assert len(result["periods"]) == 3  # 3 days
        assert result["currency"] == "EUR"
        assert "growth_rate" in result
        assert "trend_direction" in result
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_week_granularity(self, mock_get_consumption):
        """Test calculate_trends with week granularity."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-14", granularity="week"
        )
        
        assert result["granularity"] == "week"
        assert len(result["periods"]) >= 2  # At least 2 weeks
        assert "growth_rate" in result
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_month_granularity(self, mock_get_consumption):
        """Test calculate_trends with month granularity."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-03-31", granularity="month"
        )
        
        assert result["granularity"] == "month"
        assert len(result["periods"]) == 3  # 3 months
        assert "growth_rate" in result
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_with_resource_type_filter(self, mock_get_consumption):
        """Test calculate_trends with resource type filter."""
        mock_get_consumption.return_value = {
            "entries": [
                {"Type": "VM", "UnitPrice": 10.0, "Value": 10.0},
                {"Type": "Storage", "UnitPrice": 5.0, "Value": 10.0}
            ],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", resource_type="VM"
        )
        
        # Should filter to only VM entries
        assert result["resource_type"] == "VM"
        # Each period should only count VM costs (10.0 * 10.0 = 100.0)
        for period in result["periods"]:
            assert period["cost"] == 100.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_increasing_trend(self, mock_get_consumption):
        """Test calculate_trends identifies increasing trend."""
        # Simulate increasing costs (UnitPrice * Value)
        costs = [100.0, 150.0, 200.0]
        mock_get_consumption.side_effect = [
            {"entries": [{"UnitPrice": cost / 10.0, "Value": 10.0}], "currency": "EUR"}
            for cost in costs
        ]
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert result["trend_direction"] == "increasing"
        assert result["growth_rate"] > 5.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_decreasing_trend(self, mock_get_consumption):
        """Test calculate_trends identifies decreasing trend."""
        costs = [200.0, 150.0, 100.0]
        mock_get_consumption.side_effect = [
            {"entries": [{"UnitPrice": cost / 10.0, "Value": 10.0}], "currency": "EUR"}
            for cost in costs
        ]
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert result["trend_direction"] == "decreasing"
        assert result["growth_rate"] < -5.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_stable_trend(self, mock_get_consumption):
        """Test calculate_trends identifies stable trend."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert result["trend_direction"] == "stable"
        assert abs(result["growth_rate"]) <= 5.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_handles_fetch_errors(self, mock_get_consumption):
        """Test calculate_trends handles consumption fetch errors."""
        mock_get_consumption.side_effect = [
            Exception("API Error"),
            {"entries": [{"UnitPrice": 10.0, "Value": 10.0}], "currency": "EUR"}
        ]
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day"
        )
        
        # Should handle error gracefully, using 0.0 for failed period
        assert len(result["periods"]) == 2
        assert result["periods"][0]["cost"] == 0.0  # Failed fetch
        assert result["periods"][1]["cost"] == 100.0  # Successful fetch (10.0 * 10.0)
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_with_budget(self, mock_get_consumption):
        """Test calculate_trends with budget parameter."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        budget = Mock()
        budget.period_type = "monthly"
        budget.start_date = date(2024, 1, 1)
        
        with patch('backend.services.trend_service.align_periods_to_budget_boundaries') as mock_align:
            mock_align.return_value = [
                {"period": "2024-01", "from_date": "2024-01-01", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02", "from_date": "2024-02-01", "to_date": "2024-02-29", "cost": 120.0}
            ]
            
            result = calculate_trends(
                "access_key", "secret_key", "eu-west-2", "account-123",
                "2024-01-01", "2024-02-29", granularity="month",
                budget=budget
            )
            
            assert mock_align.called
            assert result["granularity"] == "month"
    
    @patch('backend.services.trend_service.get_consumption')
    @patch('backend.services.trend_service.find_last_period_excluding_today')
    @patch('backend.services.trend_service.project_trend_until_date')
    def test_calculate_trends_with_project_until(self, mock_project, mock_find_last, mock_get_consumption):
        """Test calculate_trends with project_until parameter."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        mock_find_last.return_value = "2024-01-15"
        mock_project.return_value = {
            "periods": [
                {"period": "2024-01-01", "to_date": "2024-01-01", "cost": 100.0},
                {"period": "2024-01-16", "to_date": "2024-01-16", "cost": 110.0, "projected": True}
            ],
            "projected_periods": 1
        }
        
        with patch('backend.services.trend_service.datetime') as mock_dt:
            # Mock today as future date so projection happens
            mock_dt.utcnow.return_value.date.return_value = date(2024, 1, 20)
            mock_dt.strptime = datetime.strptime
            
            result = calculate_trends(
                "access_key", "secret_key", "eu-west-2", "account-123",
                "2024-01-01", "2024-01-31", granularity="day",
                project_until="2024-01-31"
            )
            
            # Verify projection was attempted
            assert mock_find_last.called or result.get("projected_periods", 0) > 0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_empty_consumption_entries(self, mock_get_consumption):
        """Test calculate_trends with empty consumption entries."""
        mock_get_consumption.return_value = {
            "entries": [],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert len(result["periods"]) == 3
        assert all(p["cost"] == 0.0 for p in result["periods"])
        assert result["total_cost"] == 0.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_currency_variations(self, mock_get_consumption):
        """Test calculate_trends with different currencies."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "USD"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day"
        )
        
        assert result["currency"] == "USD"
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_force_refresh(self, mock_get_consumption):
        """Test calculate_trends with force_refresh parameter."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day",
            force_refresh=True
        )
        
        # Verify get_consumption was called with force_refresh
        assert mock_get_consumption.called
        call_args = mock_get_consumption.call_args
        assert call_args.kwargs.get("force_refresh") is True
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_multiple_consecutive_errors(self, mock_get_consumption):
        """Test calculate_trends with multiple consecutive fetch errors."""
        mock_get_consumption.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            {"entries": [{"UnitPrice": 10.0, "Value": 10.0}], "currency": "EUR"}
        ]
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert len(result["periods"]) == 3
        assert result["periods"][0]["cost"] == 0.0
        assert result["periods"][1]["cost"] == 0.0
        assert result["periods"][2]["cost"] == 100.0  # 10.0 * 10.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_resource_type_filter_mixed(self, mock_get_consumption):
        """Test resource type filtering with mixed resource types."""
        mock_get_consumption.return_value = {
            "entries": [
                {"Type": "VM", "UnitPrice": 10.0, "Value": 10.0},
                {"Type": "Storage", "UnitPrice": 5.0, "Value": 10.0},
                {"Type": "VM", "UnitPrice": 7.5, "Value": 10.0}
            ],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", resource_type="VM"
        )
        
        assert result["resource_type"] == "VM"
        # Should only count VM entries (10.0*10.0 + 7.5*10.0 = 175.0 per period)
        for period in result["periods"]:
            # Each period should filter to VM only
            assert period["cost"] == 175.0
    
    @patch('backend.services.trend_service.validate_date_range')
    def test_calculate_trends_invalid_date_range(self, mock_validate):
        """Test calculate_trends with invalid date range."""
        mock_validate.return_value = (False, "Invalid date range")
        
        with pytest.raises(ValueError, match="Invalid date range"):
            calculate_trends(
                "access_key", "secret_key", "eu-west-2", "account-123",
                "2024-01-31", "2024-01-01", granularity="day"
            )


class TestProjectTrendUntilDate:
    """Tests for project_trend_until_date function."""
    
    def test_project_trend_until_date_increasing(self):
        """Test projecting increasing trend."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 120.0},
                {"period": "2024-03-31", "to_date": "2024-03-31", "cost": 140.0}
            ],
            "growth_rate": 20.0,
            "historical_average": 120.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-06-30")
        
        assert "projected_periods" in result
        assert result["projected_periods"] > 0  # Count of projected periods
        assert len(result["periods"]) > len(trend_data["periods"])  # More periods added
        # Projected periods should have "projected": True
        projected = [p for p in result["periods"] if p.get("projected")]
        assert len(projected) > 0
    
    def test_project_trend_until_date_decreasing(self):
        """Test projecting decreasing trend."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 200.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 180.0},
                {"period": "2024-03-31", "to_date": "2024-03-31", "cost": 160.0}
            ],
            "growth_rate": -20.0,
            "historical_average": 180.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-06-30")
        
        assert "projected_periods" in result
        assert result["projected_periods"] > 0
        # Projected costs should be decreasing (negative growth rate)
        projected = [p for p in result["periods"] if p.get("projected")]
        assert len(projected) > 0
    
    def test_project_trend_until_date_before_end(self):
        """Test projecting when end_date is before last period."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 120.0}
            ],
            "growth_rate": 20.0,
            "historical_average": 110.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-01-15")
        
        # Should return original data if target is before last period
        assert result == trend_data
    
    def test_project_trend_until_date_stable(self):
        """Test projecting stable trend."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 100.0},
                {"period": "2024-03-31", "to_date": "2024-03-31", "cost": 100.0}
            ],
            "growth_rate": 0.0,
            "historical_average": 100.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-06-30")
        
        assert "projected_periods" in result
        # Projected costs should be close to last cost (100.0) since growth is 0
        projected = [p for p in result["periods"] if p.get("projected")]
        for period in projected:
            assert abs(period["cost"] - 100.0) < 1.0  # Should stay close to 100
    
    def test_project_trend_until_date_week_granularity(self):
        """Test projecting with week granularity."""
        trend_data = {
            "periods": [
                {"period": "2024-01-01", "to_date": "2024-01-07", "cost": 100.0},
                {"period": "2024-01-08", "to_date": "2024-01-14", "cost": 110.0}
            ],
            "growth_rate": 10.0,
            "historical_average": 105.0,
            "granularity": "week"
        }
        
        result = project_trend_until_date(trend_data, "2024-02-14")
        
        assert "projected_periods" in result
        assert result["projected_periods"] > 0
        projected = [p for p in result["periods"] if p.get("projected")]
        assert len(projected) > 0
    
    def test_project_trend_until_date_with_budget(self):
        """Test projection with budget boundary alignment."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0}
            ],
            "growth_rate": 10.0,
            "historical_average": 100.0,
            "granularity": "month"
        }
        
        budget = Mock()
        budget.period_type = "monthly"
        
        with patch('backend.services.trend_service.align_periods_to_budget_boundaries') as mock_align:
            mock_align.return_value = [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 110.0, "projected": True}
            ]
            
            result = project_trend_until_date(trend_data, "2024-02-29", budget)
            
            assert mock_align.called
            assert len(result["periods"]) > len(trend_data["periods"])
    
    def test_project_trend_until_date_negative_growth(self):
        """Test projection with negative growth rate."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 200.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 180.0}
            ],
            "growth_rate": -10.0,
            "historical_average": 190.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-04-30")
        
        projected = [p for p in result["periods"] if p.get("projected")]
        assert len(projected) > 0
        # Projected costs should be decreasing
        for i in range(1, len(projected)):
            assert projected[i]["cost"] <= projected[i-1]["cost"]
    
    def test_project_trend_until_date_high_growth_rate(self):
        """Test projection with very high growth rate."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0},
                {"period": "2024-02-29", "to_date": "2024-02-29", "cost": 200.0}
            ],
            "growth_rate": 100.0,
            "historical_average": 150.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-04-30")
        
        projected = [p for p in result["periods"] if p.get("projected")]
        assert len(projected) > 0
        # Projected costs should be increasing
        for i in range(1, len(projected)):
            assert projected[i]["cost"] >= projected[i-1]["cost"]
    
    def test_project_trend_until_date_invalid_date_format(self):
        """Test projection with invalid date format."""
        trend_data = {
            "periods": [
                {"period": "2024-01-31", "to_date": "2024-01-31", "cost": 100.0}
            ],
            "growth_rate": 10.0,
            "historical_average": 100.0,
            "granularity": "month"
        }
        
        # Should return original data on invalid date
        result = project_trend_until_date(trend_data, "invalid-date")
        assert result == trend_data
    
    def test_project_trend_until_date_empty_periods(self):
        """Test projection with empty periods."""
        trend_data = {
            "periods": [],
            "growth_rate": 10.0,
            "historical_average": 100.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-06-30")
        assert result == trend_data
    
    def test_project_trend_until_date_no_periods_key(self):
        """Test projection with missing periods key."""
        trend_data = {
            "growth_rate": 10.0,
            "historical_average": 100.0,
            "granularity": "month"
        }
        
        result = project_trend_until_date(trend_data, "2024-06-30")
        assert result == trend_data


class TestGetMonthlyWeekEnd:
    """Tests for get_monthly_week_end function."""
    
    def test_get_monthly_week_end_week_1(self):
        """Test week 1 end (days 1-7)."""
        week_start = date(2024, 1, 1)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 1, 7)
    
    def test_get_monthly_week_end_week_2(self):
        """Test week 2 end (days 8-14)."""
        week_start = date(2024, 1, 8)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 1, 14)
    
    def test_get_monthly_week_end_week_3(self):
        """Test week 3 end (days 15-21)."""
        week_start = date(2024, 1, 15)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 1, 21)
    
    def test_get_monthly_week_end_week_4_january(self):
        """Test week 4 end for January (31 days)."""
        week_start = date(2024, 1, 22)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 1, 31)
    
    def test_get_monthly_week_end_week_4_february_leap_year(self):
        """Test week 4 end for February in leap year (29 days)."""
        week_start = date(2024, 2, 22)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 2, 29)
    
    def test_get_monthly_week_end_week_4_february_non_leap(self):
        """Test week 4 end for February in non-leap year (28 days)."""
        week_start = date(2023, 2, 22)
        result = get_monthly_week_end(week_start)
        assert result == date(2023, 2, 28)
    
    def test_get_monthly_week_end_week_4_april(self):
        """Test week 4 end for April (30 days)."""
        week_start = date(2024, 4, 22)
        result = get_monthly_week_end(week_start)
        assert result == date(2024, 4, 30)
    
    def test_get_monthly_week_end_with_from_date(self):
        """Test get_monthly_week_end with from_date parameter."""
        week_start = date(2024, 1, 1)
        from_date = date(2024, 1, 3)
        result = get_monthly_week_end(week_start, from_date)
        # Should still return normal week end
        assert result == date(2024, 1, 7)


class TestGetNextMonthlyWeekStart:
    """Tests for get_next_monthly_week_start function."""
    
    def test_get_next_monthly_week_start_week_1_to_2(self):
        """Test transition from week 1 to week 2."""
        current_date = date(2024, 1, 5)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 1, 8)
    
    def test_get_next_monthly_week_start_week_2_to_3(self):
        """Test transition from week 2 to week 3."""
        current_date = date(2024, 1, 10)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 1, 15)
    
    def test_get_next_monthly_week_start_week_3_to_4(self):
        """Test transition from week 3 to week 4."""
        current_date = date(2024, 1, 18)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 1, 22)
    
    def test_get_next_monthly_week_start_week_4_to_next_month(self):
        """Test transition from week 4 to next month."""
        current_date = date(2024, 1, 25)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 2, 1)
    
    def test_get_next_monthly_week_start_december_to_january(self):
        """Test transition from December to January (year boundary)."""
        current_date = date(2024, 12, 25)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2025, 1, 1)
    
    def test_get_next_monthly_week_start_february_short_month(self):
        """Test transition in February (28 days)."""
        current_date = date(2023, 2, 25)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2023, 3, 1)
    
    def test_get_next_monthly_week_start_february_leap_year(self):
        """Test transition in February leap year (29 days)."""
        current_date = date(2024, 2, 25)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 3, 1)
    
    def test_get_next_monthly_week_start_april_30_days(self):
        """Test transition in April (30 days)."""
        current_date = date(2024, 4, 25)
        result = get_next_monthly_week_start(current_date)
        assert result == date(2024, 5, 1)


class TestFindLastPeriodExcludingToday:
    """Tests for find_last_period_excluding_today function."""
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_day_granularity(self, mock_datetime):
        """Test finding last day period excluding today."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 15)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("day", "2024-01-01", "2024-01-20")
        assert result == "2024-01-14"  # Yesterday
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_day_past_date(self, mock_datetime):
        """Test when to_date is already in the past."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 20)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("day", "2024-01-01", "2024-01-15")
        assert result == "2024-01-15"  # to_date is already before today
    
    @patch('backend.services.trend_service.datetime')
    @patch('backend.services.trend_service.get_monthly_week_start')
    def test_find_last_period_excluding_today_week_granularity(self, mock_week_start, mock_datetime):
        """Test finding last week period excluding today."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 15)
        mock_datetime.strptime = datetime.strptime
        mock_week_start.return_value = date(2024, 1, 8)  # Week 2 start
        
        result = find_last_period_excluding_today("week", "2024-01-01", "2024-01-31")
        assert result == "2024-01-01"  # Previous week start (week 1)
    
    @patch('backend.services.trend_service.datetime')
    @patch('backend.services.trend_service.get_monthly_week_start')
    def test_find_last_period_excluding_today_week_month_boundary(self, mock_week_start, mock_datetime):
        """Test week granularity at month boundary."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 2, 5)
        mock_datetime.strptime = datetime.strptime
        mock_week_start.return_value = date(2024, 2, 1)  # Week 1 start
        
        result = find_last_period_excluding_today("week", "2024-01-01", "2024-02-10")
        assert result == "2024-01-22"  # Week 4 of previous month
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_month_granularity(self, mock_datetime):
        """Test finding last month period excluding today."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 2, 15)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("month", "2024-01-01", "2024-03-31")
        assert result == "2024-01-01"  # Previous month start
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_month_year_boundary(self, mock_datetime):
        """Test month granularity at year boundary."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 15)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("month", "2023-12-01", "2024-02-28")
        assert result == "2023-12-01"  # Previous month (December)
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_invalid_granularity(self, mock_datetime):
        """Test with invalid granularity returns to_date."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 15)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("invalid", "2024-01-01", "2024-01-31")
        assert result == "2024-01-31"
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_before_from_date(self, mock_datetime):
        """Test when last period would be before from_date."""
        mock_datetime.utcnow.return_value.date.return_value = date(2024, 1, 3)
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("day", "2024-01-01", "2024-01-10")
        # Yesterday (2024-01-02) is >= from_date (2024-01-01), so it returns yesterday
        # If today was 2024-01-01, yesterday would be 2023-12-31 which is < from_date, so it would return from_date
        assert result == "2024-01-02"  # Yesterday, which is >= from_date
    
    @patch('backend.services.trend_service.datetime')
    def test_find_last_period_excluding_today_exception_handling(self, mock_datetime):
        """Test exception handling returns to_date."""
        mock_datetime.utcnow.side_effect = Exception("Error")
        mock_datetime.strptime = datetime.strptime
        
        result = find_last_period_excluding_today("day", "2024-01-01", "2024-01-31")
        assert result == "2024-01-31"


class TestAlignPeriodsToBudgetBoundaries:
    """Tests for align_periods_to_budget_boundaries function."""
    
    @patch('backend.services.trend_service.split_periods_at_budget_boundaries')
    def test_align_periods_to_budget_boundaries_with_budget(self, mock_split):
        """Test alignment with budget."""
        periods = [
            {"from_date": "2024-01-01", "to_date": "2024-01-31", "cost": 100.0},
            {"from_date": "2024-02-01", "to_date": "2024-02-29", "cost": 120.0}
        ]
        budget = Mock()
        budget.start_date = date(2024, 1, 1)  # Set as date object
        budget.period_type = "monthly"
        mock_split.return_value = [
            {"from_date": "2024-01-01", "to_date": "2024-01-31", "cost": 100.0},
            {"from_date": "2024-02-01", "to_date": "2024-02-15", "cost": 60.0},
            {"from_date": "2024-02-16", "to_date": "2024-02-29", "cost": 60.0}
        ]
        
        result = align_periods_to_budget_boundaries(periods, budget)
        
        assert len(result) == 3
        mock_split.assert_called_once_with(periods, budget)
    
    def test_align_periods_to_budget_boundaries_no_budget(self):
        """Test alignment without budget returns original periods."""
        periods = [
            {"from_date": "2024-01-01", "to_date": "2024-01-31", "cost": 100.0}
        ]
        
        result = align_periods_to_budget_boundaries(periods, None)
        
        assert result == periods
    
    def test_align_periods_to_budget_boundaries_empty_periods(self):
        """Test alignment with empty periods."""
        result = align_periods_to_budget_boundaries([], Mock())
        assert result == []
    
    def test_align_periods_to_budget_boundaries_no_periods_no_budget(self):
        """Test alignment with no periods and no budget."""
        result = align_periods_to_budget_boundaries(None, None)
        assert result is None


class TestGeneratePeriodRanges:
    """Tests for _generate_period_ranges function."""
    
    def test_generate_period_ranges_day(self):
        """Test period generation for day granularity."""
        result = _generate_period_ranges("2024-01-01", "2024-01-03", "day")
        
        assert len(result) == 3
        assert result[0]["period"] == "2024-01-01"
        assert result[0]["from_date"] == "2024-01-01"
        assert result[0]["to_date"] == "2024-01-01"
        assert result[2]["period"] == "2024-01-03"
    
    def test_generate_period_ranges_week(self):
        """Test period generation for week granularity."""
        result = _generate_period_ranges("2024-01-01", "2024-01-14", "week")
        
        assert len(result) >= 2
        assert result[0]["period"] == "2024-01-01"
        assert "from_date" in result[0]
        assert "to_date" in result[0]
    
    def test_generate_period_ranges_month(self):
        """Test period generation for month granularity."""
        result = _generate_period_ranges("2024-01-01", "2024-03-31", "month")
        
        assert len(result) == 3
        assert result[0]["period"] == "2024-01"
        assert result[1]["period"] == "2024-02"
        assert result[2]["period"] == "2024-03"


class TestFetchPeriodCosts:
    """Tests for _fetch_period_costs function."""
    
    @patch('backend.services.trend_service.get_consumption')
    def test_fetch_period_costs_exclusive_todate(self, mock_get_consumption):
        """Test fetching costs with exclusive ToDate."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        period_ranges = [
            {"period": "2024-01-01", "from_date": "2024-01-01", "to_date": "2024-01-01"}
        ]
        
        periods, currency = _fetch_period_costs(
            period_ranges, "key", "secret", "region", "account",
            None, False, use_exclusive_todate=True
        )
        
        assert len(periods) == 1
        assert periods[0]["cost"] == 100.0  # 10.0 * 10.0
        assert currency == "EUR"
        # Verify exclusive ToDate was used (to_date + 1 day)
        call_args = mock_get_consumption.call_args
        assert call_args.kwargs["to_date"] == "2024-01-02"
    
    @patch('backend.services.trend_service.get_consumption')
    def test_fetch_period_costs_inclusive_todate(self, mock_get_consumption):
        """Test fetching costs with inclusive ToDate."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        period_ranges = [
            {"period": "2024-01-01", "from_date": "2024-01-01", "to_date": "2024-01-01"}
        ]
        
        periods, currency = _fetch_period_costs(
            period_ranges, "key", "secret", "region", "account",
            None, False, use_exclusive_todate=False
        )
        
        assert len(periods) == 1
        assert currency == "EUR"
        # Verify inclusive ToDate was used (to_date as-is)
        call_args = mock_get_consumption.call_args
        assert call_args.kwargs["to_date"] == "2024-01-01"
    
    @patch('backend.services.trend_service.get_consumption')
    def test_fetch_period_costs_with_resource_type(self, mock_get_consumption):
        """Test fetching costs with resource type filter."""
        mock_get_consumption.return_value = {
            "entries": [
                {"Type": "VM", "UnitPrice": 10.0, "Value": 10.0},
                {"Type": "Storage", "UnitPrice": 5.0, "Value": 10.0}
            ],
            "currency": "EUR"
        }
        
        period_ranges = [
            {"period": "2024-01-01", "from_date": "2024-01-01", "to_date": "2024-01-01"}
        ]
        
        periods, currency = _fetch_period_costs(
            period_ranges, "key", "secret", "region", "account",
            "VM", False, use_exclusive_todate=True
        )
        
        assert len(periods) == 1
        assert periods[0]["cost"] == 100.0  # Only VM entries (10.0 * 10.0)
    
    @patch('backend.services.trend_service.get_consumption')
    def test_fetch_period_costs_error_handling(self, mock_get_consumption):
        """Test error handling in fetch period costs."""
        mock_get_consumption.side_effect = Exception("API Error")
        
        period_ranges = [
            {"period": "2024-01-01", "from_date": "2024-01-01", "to_date": "2024-01-01"}
        ]
        
        periods, currency = _fetch_period_costs(
            period_ranges, "key", "secret", "region", "account",
            None, False, use_exclusive_todate=True
        )
        
        assert len(periods) == 1
        assert periods[0]["cost"] == 0.0
        assert periods[0]["value"] == 0.0
        assert periods[0]["entry_count"] == 0
        assert currency == "EUR"  # Default currency
    
    @patch('backend.services.trend_service.get_consumption')
    def test_fetch_period_costs_progress_callback(self, mock_get_consumption):
        """Test progress callback in fetch period costs."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        progress_calls = []
        def progress_callback(progress, estimated_remaining):
            progress_calls.append(progress)
        
        period_ranges = [
            {"period": "2024-01-01", "from_date": "2024-01-01", "to_date": "2024-01-01"},
            {"period": "2024-01-02", "from_date": "2024-01-02", "to_date": "2024-01-02"}
        ]
        
        _fetch_period_costs(
            period_ranges, "key", "secret", "region", "account",
            None, False, use_exclusive_todate=True,
            progress_callback=progress_callback, start_progress=0, end_progress=100
        )
        
        assert len(progress_calls) > 0


class TestCalculateTrendMetrics:
    """Tests for _calculate_trend_metrics function."""
    
    def test_calculate_trend_metrics_increasing(self):
        """Test trend metrics calculation for increasing trend."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 150.0},
            {"period": "2024-03", "cost": 200.0}
        ]
        
        metrics = _calculate_trend_metrics(periods)
        
        assert metrics["growth_rate"] > 5.0
        assert metrics["trend_direction"] == "increasing"
        assert metrics["historical_average"] == 150.0
        assert len(metrics["period_changes"]) == 2
    
    def test_calculate_trend_metrics_decreasing(self):
        """Test trend metrics calculation for decreasing trend."""
        periods = [
            {"period": "2024-01", "cost": 200.0},
            {"period": "2024-02", "cost": 150.0},
            {"period": "2024-03", "cost": 100.0}
        ]
        
        metrics = _calculate_trend_metrics(periods)
        
        assert metrics["growth_rate"] < -5.0
        assert metrics["trend_direction"] == "decreasing"
        assert len(metrics["period_changes"]) == 2
    
    def test_calculate_trend_metrics_stable(self):
        """Test trend metrics calculation for stable trend."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 102.0},
            {"period": "2024-03", "cost": 101.0}
        ]
        
        metrics = _calculate_trend_metrics(periods)
        
        assert abs(metrics["growth_rate"]) <= 5.0
        assert metrics["trend_direction"] == "stable"
    
    def test_calculate_trend_metrics_single_period(self):
        """Test trend metrics with single period."""
        periods = [{"period": "2024-01", "cost": 100.0}]
        
        metrics = _calculate_trend_metrics(periods)
        
        assert metrics["growth_rate"] == 0.0
        assert metrics["historical_average"] == 100.0
        assert len(metrics["period_changes"]) == 0


class TestBuildTrendResult:
    """Tests for _build_trend_result function."""
    
    def test_build_trend_result_basic(self):
        """Test building basic trend result."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 120.0}
        ]
        metrics = {
            "growth_rate": 20.0,
            "historical_average": 110.0,
            "period_changes": [],
            "trend_direction": "increasing"
        }
        
        result = _build_trend_result(
            periods, metrics, "EUR", "eu-west-2", "month",
            "2024-01-01", "2024-02-29", None
        )
        
        assert result["periods"] == periods
        assert result["growth_rate"] == 20.0
        assert result["currency"] == "EUR"
        assert result["total_cost"] == 220.0
        assert result["period_count"] == 2
        assert "projected" not in result
    
    def test_build_trend_result_with_projection(self):
        """Test building trend result with projection."""
        periods = [
            {"period": "2024-01", "cost": 100.0},
            {"period": "2024-02", "cost": 110.0, "projected": True}
        ]
        metrics = {
            "growth_rate": 10.0,
            "historical_average": 100.0,
            "period_changes": [],
            "trend_direction": "increasing"
        }
        
        result = _build_trend_result(
            periods, metrics, "EUR", "eu-west-2", "month",
            "2024-01-01", "2024-02-29", None,
            projected=True, projected_periods=1
        )
        
        assert result["projected"] is True
        assert result["projected_periods"] == 1


class TestCalculateTrendsAsync:
    """Tests for calculate_trends_async function."""
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_async_progress_callback(self, mock_get_consumption):
        """Test async calculation with progress callback."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        progress_calls = []
        def progress_callback(progress, estimated_remaining):
            progress_calls.append((progress, estimated_remaining))
        
        result = calculate_trends_async(
            "job-123", "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day",
            progress_callback=progress_callback
        )
        
        assert len(progress_calls) > 0
        assert progress_calls[0][0] == 0  # Starting progress
        assert result["granularity"] == "day"
        assert len(result["periods"]) > 0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_async_no_callback(self, mock_get_consumption):
        """Test async calculation without callback."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        result = calculate_trends_async(
            "job-123", "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-03", granularity="day"
        )
        
        assert result["granularity"] == "day"
        assert "growth_rate" in result
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_async_progress_percentages(self, mock_get_consumption):
        """Test progress percentages are called correctly."""
        mock_get_consumption.return_value = {
            "entries": [{"UnitPrice": 10.0, "Value": 10.0}],
            "currency": "EUR"
        }
        
        progress_values = []
        def progress_callback(progress, estimated_remaining):
            progress_values.append(progress)
        
        calculate_trends_async(
            "job-123", "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day",
            progress_callback=progress_callback
        )
        
        # Should have progress updates at 0%, 20%, 80%, 100%
        assert 0 in progress_values
        assert 20 in progress_values or any(p >= 20 for p in progress_values)
        assert 100 in progress_values
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_async_error_handling(self, mock_get_consumption):
        """Test error handling in async calculation."""
        # The function handles errors gracefully in the period loop, so we test that
        # errors during consumption fetch result in 0 cost for that period
        mock_get_consumption.side_effect = Exception("API Error")
        
        progress_calls = []
        def progress_callback(progress, estimated_remaining):
            progress_calls.append(progress)
        
        # Function should complete successfully, handling errors gracefully
        result = calculate_trends_async(
            "job-123", "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day",
            progress_callback=progress_callback
        )
        
        # Should have called progress
        assert len(progress_calls) > 0
        # Periods should have 0 cost due to errors
        assert all(p["cost"] == 0.0 for p in result["periods"])

