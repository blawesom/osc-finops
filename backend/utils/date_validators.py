"""Centralized date validation utilities for the application."""
from typing import Optional, Tuple
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


def validate_date_format(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to validate
    
    Returns:
        True if date is in valid format, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def get_minimum_to_date(from_date: str, granularity: str) -> str:
    """
    Calculate the minimum valid to_date based on from_date and granularity.
    to_date must be at least 1 granularity period after from_date.
    
    Args:
        from_date: Start date (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month"
    
    Returns:
        Minimum valid to_date string (ISO format: YYYY-MM-DD)
    """
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    
    if granularity == "day":
        min_to_date = from_dt + timedelta(days=1)
    elif granularity == "week":
        min_to_date = from_dt + timedelta(weeks=1)
    elif granularity == "month":
        min_to_date = from_dt + relativedelta(months=1)
    else:
        # Default to 1 day if granularity is invalid
        min_to_date = from_dt + timedelta(days=1)
    
    return min_to_date.strftime("%Y-%m-%d")


def validate_date_range(from_date: str, to_date: str, granularity: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate date range according to application rules.
    
    Validation rules:
    - from_date and to_date must be in YYYY-MM-DD format
    - from_date must be in the past
    - to_date must be >= from_date + 1 granularity period (if granularity provided)
    - to_date must be > from_date (if granularity not provided)
    
    Args:
        from_date: Start date (ISO format: YYYY-MM-DD)
        to_date: End date (ISO format: YYYY-MM-DD)
        granularity: "day", "week", or "month" (optional)
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes, False otherwise
        - error_message: Error message if validation fails, None if valid
    """
    # Validate date format
    if not validate_date_format(from_date):
        return False, f"Invalid from_date format. Use YYYY-MM-DD"
    
    if not validate_date_format(to_date):
        return False, f"Invalid to_date format. Use YYYY-MM-DD"
    
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        from_date_obj = from_dt.date()
        to_date_obj = to_dt.date()
        today = datetime.utcnow().date()
        
        # Validate from_date is in the past
        if from_date_obj >= today:
            return False, "from_date must be in the past"
        
        # Validate to_date based on granularity
        if granularity:
            # Validate to_date >= from_date + 1 granularity period
            min_to_date_str = get_minimum_to_date(from_date, granularity)
            min_to_date_obj = datetime.strptime(min_to_date_str, "%Y-%m-%d").date()
            
            if to_date_obj < min_to_date_obj:
                return False, f"to_date must be >= {min_to_date_str} (from_date + 1 {granularity} period)"
        else:
            # Basic validation: to_date must be > from_date
            if to_date_obj <= from_date_obj:
                return False, "to_date must be > from_date (ToDate is exclusive)"
        
        return True, None
        
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"

