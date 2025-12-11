"""Unit tests for backend.utils.date_validators."""
import pytest
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from backend.utils.date_validators import (
    validate_date_format,
    get_minimum_to_date,
    validate_date_range
)


class TestValidateDateFormat:
    """Tests for validate_date_format function."""
    
    def test_valid_date_format(self):
        """Test with valid YYYY-MM-DD format."""
        assert validate_date_format("2024-01-15") is True
        assert validate_date_format("2023-12-31") is True
        assert validate_date_format("2024-02-29") is True  # Leap year
        assert validate_date_format("2000-01-01") is True
    
    def test_invalid_date_format_wrong_separator(self):
        """Test with wrong date separator."""
        assert validate_date_format("2024/01/15") is False
        assert validate_date_format("2024.01.15") is False
        assert validate_date_format("2024 01 15") is False
    
    def test_invalid_date_format_wrong_order(self):
        """Test with wrong date order."""
        assert validate_date_format("01-15-2024") is False
        assert validate_date_format("15-01-2024") is False
    
    def test_invalid_date_format_short_year(self):
        """Test with 2-digit year."""
        assert validate_date_format("24-01-15") is False
    
    def test_invalid_date_format_missing_parts(self):
        """Test with missing date parts."""
        assert validate_date_format("2024-01") is False
        assert validate_date_format("2024") is False
        assert validate_date_format("01-15") is False
    
    def test_invalid_date_format_invalid_dates(self):
        """Test with invalid dates."""
        assert validate_date_format("2024-13-01") is False  # Invalid month
        assert validate_date_format("2024-02-30") is False  # Invalid day
        assert validate_date_format("2023-02-29") is False  # Not a leap year
    
    def test_invalid_date_format_empty_string(self):
        """Test with empty string."""
        assert validate_date_format("") is False
    
    def test_invalid_date_format_none(self):
        """Test with None value."""
        assert validate_date_format(None) is False
    
    def test_invalid_date_format_non_string(self):
        """Test with non-string value."""
        assert validate_date_format(20240115) is False
        assert validate_date_format([]) is False


class TestGetMinimumToDate:
    """Tests for get_minimum_to_date function."""
    
    def test_day_granularity(self):
        """Test minimum to_date for day granularity."""
        result = get_minimum_to_date("2024-01-15", "day")
        assert result == "2024-01-16"
        
        # Test month boundary
        result = get_minimum_to_date("2024-01-31", "day")
        assert result == "2024-02-01"
        
        # Test year boundary
        result = get_minimum_to_date("2023-12-31", "day")
        assert result == "2024-01-01"
    
    def test_week_granularity(self):
        """Test minimum to_date for week granularity."""
        result = get_minimum_to_date("2024-01-15", "week")
        assert result == "2024-01-22"
        
        # Test month boundary
        result = get_minimum_to_date("2024-01-25", "week")
        assert result == "2024-02-01"
    
    def test_month_granularity(self):
        """Test minimum to_date for month granularity."""
        result = get_minimum_to_date("2024-01-15", "month")
        assert result == "2024-02-15"
        
        # Test year boundary
        result = get_minimum_to_date("2023-12-15", "month")
        assert result == "2024-01-15"
        
        # Test month with different day counts
        result = get_minimum_to_date("2024-01-31", "month")
        assert result == "2024-02-29"  # February in leap year
    
    def test_invalid_granularity_defaults_to_day(self):
        """Test that invalid granularity defaults to 1 day."""
        result = get_minimum_to_date("2024-01-15", "invalid")
        assert result == "2024-01-16"
        
        result = get_minimum_to_date("2024-01-15", "")
        assert result == "2024-01-16"
        
        result = get_minimum_to_date("2024-01-15", None)
        # This will raise TypeError, but let's test with empty string
        result = get_minimum_to_date("2024-01-15", "unknown")
        assert result == "2024-01-16"


class TestValidateDateRange:
    """Tests for validate_date_range function."""
    
    def test_valid_date_range_no_granularity(self):
        """Test valid date range without granularity."""
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        two_days_ago = (datetime.utcnow().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(two_days_ago, yesterday)
        assert is_valid is True
        assert error is None
    
    def test_valid_date_range_with_day_granularity(self):
        """Test valid date range with day granularity."""
        three_days_ago = (datetime.utcnow().date() - timedelta(days=3)).strftime("%Y-%m-%d")
        two_days_ago = (datetime.utcnow().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(three_days_ago, two_days_ago, "day")
        assert is_valid is True
        assert error is None
    
    def test_valid_date_range_with_week_granularity(self):
        """Test valid date range with week granularity."""
        two_weeks_ago = (datetime.utcnow().date() - timedelta(weeks=2)).strftime("%Y-%m-%d")
        one_week_ago = (datetime.utcnow().date() - timedelta(weeks=1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(two_weeks_ago, one_week_ago, "week")
        assert is_valid is True
        assert error is None
    
    def test_valid_date_range_with_month_granularity(self):
        """Test valid date range with month granularity."""
        two_months_ago = (datetime.utcnow().date() - relativedelta(months=2)).strftime("%Y-%m-%d")
        one_month_ago = (datetime.utcnow().date() - relativedelta(months=1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(two_months_ago, one_month_ago, "month")
        assert is_valid is True
        assert error is None
    
    def test_invalid_from_date_format(self):
        """Test with invalid from_date format."""
        to_date = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range("invalid-date", to_date)
        assert is_valid is False
        assert "Invalid from_date format" in error
    
    def test_invalid_to_date_format(self):
        """Test with invalid to_date format."""
        from_date = (datetime.utcnow().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, "invalid-date")
        assert is_valid is False
        assert "Invalid to_date format" in error
    
    def test_from_date_in_future(self):
        """Test with from_date in the future."""
        tomorrow = (datetime.utcnow().date() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.utcnow().date() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(tomorrow, day_after)
        assert is_valid is False
        assert "from_date must be in the past" in error
    
    def test_from_date_is_today(self):
        """Test with from_date as today."""
        today = datetime.utcnow().date().strftime("%Y-%m-%d")
        tomorrow = (datetime.utcnow().date() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(today, tomorrow)
        assert is_valid is False
        assert "from_date must be in the past" in error
    
    def test_to_date_equal_to_from_date_no_granularity(self):
        """Test with to_date equal to from_date (no granularity)."""
        from_date = (datetime.utcnow().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, from_date)
        assert is_valid is False
        assert "to_date must be > from_date" in error
    
    def test_to_date_before_from_date_no_granularity(self):
        """Test with to_date before from_date (no granularity)."""
        from_date = (datetime.utcnow().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        to_date = (datetime.utcnow().date() - timedelta(days=3)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, to_date)
        assert is_valid is False
        assert "to_date must be > from_date" in error
    
    def test_to_date_less_than_minimum_with_day_granularity(self):
        """Test with to_date less than minimum for day granularity."""
        from_date = (datetime.utcnow().date() - timedelta(days=3)).strftime("%Y-%m-%d")
        # to_date is same as from_date (should be at least 1 day later)
        to_date = from_date
        
        is_valid, error = validate_date_range(from_date, to_date, "day")
        assert is_valid is False
        assert "to_date must be >=" in error
        assert "1 day period" in error
    
    def test_to_date_less_than_minimum_with_week_granularity(self):
        """Test with to_date less than minimum for week granularity."""
        from_date = (datetime.utcnow().date() - timedelta(weeks=2)).strftime("%Y-%m-%d")
        # to_date is only 3 days after from_date (should be at least 1 week later)
        to_date = (datetime.utcnow().date() - timedelta(weeks=2, days=-3)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, to_date, "week")
        assert is_valid is False
        assert "to_date must be >=" in error
        assert "1 week period" in error
    
    def test_to_date_less_than_minimum_with_month_granularity(self):
        """Test with to_date less than minimum for month granularity."""
        from_date = (datetime.utcnow().date() - relativedelta(months=2)).strftime("%Y-%m-%d")
        # to_date is only 1 week after from_date (should be at least 1 month later)
        to_date = (datetime.utcnow().date() - relativedelta(months=2, weeks=-1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, to_date, "month")
        assert is_valid is False
        assert "to_date must be >=" in error
        assert "1 month period" in error
    
    def test_to_date_exactly_minimum_with_granularity(self):
        """Test with to_date exactly at minimum for granularity."""
        from_date = (datetime.utcnow().date() - timedelta(days=3)).strftime("%Y-%m-%d")
        min_to_date = get_minimum_to_date(from_date, "day")
        
        is_valid, error = validate_date_range(from_date, min_to_date, "day")
        assert is_valid is True
        assert error is None
    
    def test_to_date_greater_than_minimum_with_granularity(self):
        """Test with to_date greater than minimum for granularity."""
        from_date = (datetime.utcnow().date() - timedelta(days=3)).strftime("%Y-%m-%d")
        to_date = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        is_valid, error = validate_date_range(from_date, to_date, "day")
        assert is_valid is True
        assert error is None

