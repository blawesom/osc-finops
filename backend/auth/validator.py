"""Credential and region validation."""
from typing import Tuple, Optional

from backend.config.settings import SUPPORTED_REGIONS
from backend.utils.api_call_logger import create_logged_gateway, process_and_log_api_call


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


def validate_credentials(access_key: str, secret_key: str, region: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate credentials by making a test API call and retrieve account_id.
    
    Returns:
        Tuple of (is_valid, error_message, account_id)
        account_id is None if validation fails
    """
    if not access_key or not secret_key:
        return False, "Access key and secret key are required", None
    
    # Validate region first
    is_valid_region, region_error = validate_region(region)
    if not is_valid_region:
        return False, region_error, None
    
    try:
        # Create gateway with credentials and logging enabled
        gateway = create_logged_gateway(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        
        # Make ReadAccounts API call to validate credentials and get account_id
        response = process_and_log_api_call(
            gateway=gateway,
            api_method="ReadAccounts",
            call_func=lambda: gateway.ReadAccounts()
        )
        
        # Extract account_id from response
        account_id = None
        if response and response.get('Accounts'):
            accounts = response.get('Accounts')
            if accounts and len(accounts) > 0:
                account = accounts[0]
                if account.get('AccountId'):
                    account_id = account.get('AccountId')
        
        if not account_id:
            return False, "Could not retrieve account information", None
        
        return True, None, account_id
    
    except Exception as e:
        # Don't expose detailed error messages that might leak information
        error_msg = str(e)
        if "InvalidAccessKeyId" in error_msg or "SignatureDoesNotMatch" in error_msg:
            return False, "Invalid credentials for the selected region", None
        elif "RequestLimitExceeded" in error_msg:
            return False, "API rate limit exceeded. Please try again later", None
        else:
            return False, f"Authentication failed: {error_msg}", None

