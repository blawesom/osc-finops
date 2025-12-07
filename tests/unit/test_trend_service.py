"""Unit tests for backend.services.trend_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from backend.services.trend_service import (
    calculate_trends,
    calculate_growth_rate,
    calculate_historical_average,
    identify_cost_changes,
    project_trend_until_date
)


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
            "entries": [{"Price": 100.0, "Value": 10.0}],
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
            "entries": [{"Price": 100.0}],
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
            "entries": [{"Price": 100.0}],
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
                {"Type": "VM", "Price": 100.0},
                {"Type": "Storage", "Price": 50.0}
            ],
            "currency": "EUR"
        }
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", resource_type="VM"
        )
        
        # Should filter to only VM entries
        assert result["resource_type"] == "VM"
        # Each period should only count VM costs
        for period in result["periods"]:
            # Cost should be from VM entries only (100.0, not 150.0)
            assert period["cost"] == 100.0
    
    @patch('backend.services.trend_service.get_consumption')
    def test_calculate_trends_increasing_trend(self, mock_get_consumption):
        """Test calculate_trends identifies increasing trend."""
        # Simulate increasing costs
        costs = [100.0, 150.0, 200.0]
        mock_get_consumption.side_effect = [
            {"entries": [{"Price": cost}], "currency": "EUR"}
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
            {"entries": [{"Price": cost}], "currency": "EUR"}
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
            "entries": [{"Price": 100.0}],
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
            {"entries": [{"Price": 100.0}], "currency": "EUR"}
        ]
        
        result = calculate_trends(
            "access_key", "secret_key", "eu-west-2", "account-123",
            "2024-01-01", "2024-01-02", granularity="day"
        )
        
        # Should handle error gracefully, using 0.0 for failed period
        assert len(result["periods"]) == 2
        assert result["periods"][0]["cost"] == 0.0  # Failed fetch
        assert result["periods"][1]["cost"] == 100.0  # Successful fetch


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

