"""Unit tests for backend.auth.validator."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.auth.validator import validate_region, validate_credentials
from backend.config.settings import SUPPORTED_REGIONS


class TestValidateRegion:
    """Tests for validate_region function."""
    
    def test_valid_regions(self):
        """Test with all supported regions."""
        for region in SUPPORTED_REGIONS:
            is_valid, error = validate_region(region)
            assert is_valid is True
            assert error is None
    
    def test_invalid_region(self):
        """Test with invalid region."""
        is_valid, error = validate_region("invalid-region")
        assert is_valid is False
        assert "Invalid region" in error
        assert all(region in error for region in SUPPORTED_REGIONS)
    
    def test_none_region(self):
        """Test with None region."""
        is_valid, error = validate_region(None)
        assert is_valid is False
        assert error == "Region is required"
    
    def test_empty_region(self):
        """Test with empty string region."""
        is_valid, error = validate_region("")
        assert is_valid is False
        assert error == "Region is required"
    
    def test_whitespace_region(self):
        """Test with whitespace-only region (not stripped, treated as invalid)."""
        is_valid, error = validate_region("   ")
        assert is_valid is False
        # Whitespace is not stripped, so it's treated as invalid region
        assert "Invalid region" in error
    
    def test_case_sensitive(self):
        """Test that region validation is case-sensitive."""
        # Lowercase versions of valid regions should fail if case matters
        # But let's test with actual case variations
        is_valid, error = validate_region("EU-WEST-2")  # Uppercase
        assert is_valid is False  # Should be lowercase
    
    def test_partial_match(self):
        """Test that partial region names don't match."""
        is_valid, error = validate_region("eu-west")
        assert is_valid is False
    
    def test_region_with_extra_chars(self):
        """Test region with extra characters."""
        is_valid, error = validate_region("eu-west-2-extra")
        assert is_valid is False


class TestValidateCredentials:
    """Tests for validate_credentials function."""
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_valid_credentials(self, mock_create_gateway, mock_process_call):
        """Test with valid credentials."""
        # Setup mock
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {
            'Accounts': [{'AccountId': '123456789012'}]
        }
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is True
        assert error is None
        assert account_id == "123456789012"
        mock_create_gateway.assert_called_once_with(
            access_key="access_key",
            secret_key="secret_key",
            region="eu-west-2"
        )
        mock_process_call.assert_called_once()
    
    def test_missing_access_key(self):
        """Test with missing access key."""
        is_valid, error, account_id = validate_credentials(
            "",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Access key and secret key are required" in error
        assert account_id is None
    
    def test_missing_secret_key(self):
        """Test with missing secret key."""
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Access key and secret key are required" in error
        assert account_id is None
    
    def test_missing_both_keys(self):
        """Test with both keys missing."""
        is_valid, error, account_id = validate_credentials(
            None,
            None,
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Access key and secret key are required" in error
        assert account_id is None
    
    def test_invalid_region(self):
        """Test with invalid region."""
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "invalid-region"
        )
        
        assert is_valid is False
        assert "Invalid region" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_invalid_credentials_invalid_access_key(self, mock_create_gateway, mock_process_call):
        """Test with invalid access key."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.side_effect = Exception("InvalidAccessKeyId")
        
        is_valid, error, account_id = validate_credentials(
            "invalid_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Invalid credentials" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_invalid_credentials_signature_mismatch(self, mock_create_gateway, mock_process_call):
        """Test with signature mismatch."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.side_effect = Exception("SignatureDoesNotMatch")
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "wrong_secret",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Invalid credentials" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_rate_limit_exceeded(self, mock_create_gateway, mock_process_call):
        """Test with rate limit exceeded."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.side_effect = Exception("RequestLimitExceeded")
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "API rate limit exceeded" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_generic_exception(self, mock_create_gateway, mock_process_call):
        """Test with generic exception."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.side_effect = Exception("Network error")
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Authentication failed" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_empty_accounts_response(self, mock_create_gateway, mock_process_call):
        """Test with empty accounts in response."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {'Accounts': []}
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Could not retrieve account information" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_no_accounts_key_in_response(self, mock_create_gateway, mock_process_call):
        """Test with response missing Accounts key."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {}
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Could not retrieve account information" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_account_without_account_id(self, mock_create_gateway, mock_process_call):
        """Test with account missing AccountId."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {
            'Accounts': [{'SomeOtherField': 'value'}]
        }
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Could not retrieve account information" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_none_response(self, mock_create_gateway, mock_process_call):
        """Test with None response."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = None
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is False
        assert "Could not retrieve account information" in error
        assert account_id is None
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_multiple_accounts_uses_first(self, mock_create_gateway, mock_process_call):
        """Test with multiple accounts uses first one."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {
            'Accounts': [
                {'AccountId': '111111111111'},
                {'AccountId': '222222222222'}
            ]
        }
        
        is_valid, error, account_id = validate_credentials(
            "access_key",
            "secret_key",
            "eu-west-2"
        )
        
        assert is_valid is True
        assert account_id == "111111111111"
    
    @patch('backend.auth.validator.process_and_log_api_call')
    @patch('backend.auth.validator.create_logged_gateway')
    def test_all_supported_regions(self, mock_create_gateway, mock_process_call):
        """Test credential validation with all supported regions."""
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        mock_process_call.return_value = {
            'Accounts': [{'AccountId': '123456789012'}]
        }
        
        for region in SUPPORTED_REGIONS:
            is_valid, error, account_id = validate_credentials(
                "access_key",
                "secret_key",
                region
            )
            assert is_valid is True
            assert account_id == "123456789012"
            # Verify create_logged_gateway was called with correct region
            call_args = mock_create_gateway.call_args
            assert call_args[1]['region'] == region

