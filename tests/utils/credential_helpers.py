"""Credential validation utilities for tests."""
import os
from typing import Optional, Dict, Tuple
from backend.config.settings import SUPPORTED_REGIONS


def get_test_credentials() -> Optional[Dict[str, str]]:
    """
    Get test credentials from environment variables.
    
    Returns:
        Dictionary with 'access_key', 'secret_key', and 'region' if all are present,
        None otherwise.
    """
    access_key = os.getenv("OSC_ACCESS_KEY")
    secret_key = os.getenv("OSC_SECRET_KEY")
    region = os.getenv("OSC_REGION")
    
    if not access_key or not secret_key or not region:
        return None
    
    return {
        "access_key": access_key,
        "secret_key": secret_key,
        "region": region
    }


def validate_credential_format(credentials: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate credential format (basic checks).
    
    Args:
        credentials: Dictionary with 'access_key', 'secret_key', and 'region'
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not credentials:
        return False, "Credentials dictionary is empty"
    
    access_key = credentials.get("access_key", "").strip()
    secret_key = credentials.get("secret_key", "").strip()
    region = credentials.get("region", "").strip()
    
    if not access_key:
        return False, "OSC_ACCESS_KEY is empty or not set"
    
    if not secret_key:
        return False, "OSC_SECRET_KEY is empty or not set"
    
    if not region:
        return False, "OSC_REGION is empty or not set"
    
    if region not in SUPPORTED_REGIONS:
        return False, f"Invalid region '{region}'. Supported regions: {', '.join(SUPPORTED_REGIONS)}"
    
    return True, None


def has_test_credentials() -> bool:
    """
    Check if all required test credentials are present in environment.
    
    Returns:
        True if all credentials are present, False otherwise.
    """
    credentials = get_test_credentials()
    if not credentials:
        return False
    
    is_valid, _ = validate_credential_format(credentials)
    return is_valid

