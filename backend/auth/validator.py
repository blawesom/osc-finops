"""Credential and region validation."""
from typing import Tuple, Optional
from osc_sdk_python import Gateway

from backend.config.settings import SUPPORTED_REGIONS


def validate_region(region: str) -> Tuple[bool, Optional[str]]:
    """
    Validate region is in supported list.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not region:
        return False, "Region is required"
    
    if region not in SUPPORTED_REGIONS:
        return False, f"Invalid region. Supported regions: {', '.join(SUPPORTED_REGIONS)}"
    
    return True, None


def validate_credentials(access_key: str, secret_key: str, region: str) -> Tuple[bool, Optional[str]]:
    """
    Validate credentials by making a test API call.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not access_key or not secret_key:
        return False, "Access key and secret key are required"
    
    # Validate region first
    is_valid_region, region_error = validate_region(region)
    if not is_valid_region:
        return False, region_error
    
    try:
        # Create gateway with credentials
        gateway = Gateway(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        
        # Make a test API call to validate credentials
        # Using ReadAccounts as a lightweight test (no parameters needed)
        gateway.ReadAccounts()
        
        return True, None
    
    except Exception as e:
        # Don't expose detailed error messages that might leak information
        error_msg = str(e)
        if "InvalidAccessKeyId" in error_msg or "SignatureDoesNotMatch" in error_msg:
            return False, "Invalid credentials for the selected region"
        elif "RequestLimitExceeded" in error_msg:
            return False, "API rate limit exceeded. Please try again later"
        else:
            return False, f"Authentication failed: {error_msg}"

