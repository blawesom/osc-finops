"""Unit tests for backend.utils.validators."""
import pytest
import uuid
import json
import math
from backend.utils.validators import (
    validate_uuid,
    sanitize_string,
    sanitize_float,
    sanitize_json,
    validate_status,
    validate_discount_percent
)


class TestValidateUUID:
    """Tests for validate_uuid function."""
    
    def test_valid_uuid(self):
        """Test with valid UUID string."""
        valid_uuid = str(uuid.uuid4())
        assert validate_uuid(valid_uuid) is True
    
    def test_invalid_uuid_format(self):
        """Test with invalid UUID format."""
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("12345") is False
        assert validate_uuid("invalid-uuid-format") is False
    
    def test_none_uuid(self):
        """Test with None value."""
        assert validate_uuid(None) is False
    
    def test_empty_string(self):
        """Test with empty string."""
        assert validate_uuid("") is False
    
    def test_wrong_type(self):
        """Test with wrong type."""
        # For int, `not 12345` is False, so it tries uuid.UUID() which raises AttributeError
        with pytest.raises(AttributeError):
            validate_uuid(12345)
        # For empty list/dict, `not []` is True, so it returns False before conversion
        assert validate_uuid([]) is False
        assert validate_uuid({}) is False


class TestSanitizeString:
    """Tests for sanitize_string function."""
    
    def test_valid_string(self):
        """Test with valid string."""
        result = sanitize_string("hello world", 100)
        assert result == "hello world"
    
    def test_string_with_whitespace(self):
        """Test string trimming."""
        result = sanitize_string("  hello world  ", 100)
        assert result == "hello world"
    
    def test_string_truncation(self):
        """Test string truncation when too long."""
        long_string = "a" * 200
        result = sanitize_string(long_string, 50)
        assert len(result) == 50
        assert result == "a" * 50
    
    def test_none_value(self):
        """Test with None value."""
        result = sanitize_string(None, 100, default="default")
        assert result == "default"
    
    def test_empty_string(self):
        """Test with empty string."""
        result = sanitize_string("", 100, default="default")
        assert result == "default"
    
    def test_whitespace_only(self):
        """Test with whitespace-only string."""
        result = sanitize_string("   ", 100, default="default")
        assert result == "default"
    
    def test_non_string_conversion(self):
        """Test with non-string value that gets converted."""
        result = sanitize_string(12345, 100)
        assert result == "12345"
        assert isinstance(result, str)
    
    def test_custom_default(self):
        """Test with custom default value."""
        result = sanitize_string(None, 100, default="custom")
        assert result == "custom"


class TestSanitizeFloat:
    """Tests for sanitize_float function."""
    
    def test_valid_float(self):
        """Test with valid float."""
        assert sanitize_float(3.14) == 3.14
        assert sanitize_float(100.0) == 100.0
    
    def test_string_to_float(self):
        """Test string conversion to float."""
        assert sanitize_float("3.14") == 3.14
        assert sanitize_float("100") == 100.0
    
    def test_none_value(self):
        """Test with None value."""
        assert sanitize_float(None) == 0.0
        assert sanitize_float(None, default=5.0) == 5.0
    
    def test_invalid_string(self):
        """Test with invalid string."""
        assert sanitize_float("not-a-number") == 0.0
        assert sanitize_float("not-a-number", default=10.0) == 10.0
    
    def test_nan_value(self):
        """Test with NaN value."""
        result = sanitize_float(float('nan'))
        assert result == 0.0
        assert not math.isnan(result)
    
    def test_infinity_value(self):
        """Test with infinity value."""
        result = sanitize_float(float('inf'))
        assert result == 0.0
        assert not math.isinf(result)
    
    def test_negative_infinity(self):
        """Test with negative infinity."""
        result = sanitize_float(float('-inf'))
        assert result == 0.0
    
    def test_min_value_constraint(self):
        """Test minimum value constraint."""
        assert sanitize_float(5.0, min_value=10.0) == 10.0
        assert sanitize_float(15.0, min_value=10.0) == 15.0
        assert sanitize_float(5.0, min_value=10.0, default=20.0) == 20.0
    
    def test_max_value_constraint(self):
        """Test maximum value constraint."""
        # When value exceeds max, it returns default if default <= max_value, else max_value
        assert sanitize_float(15.0, max_value=10.0) == 0.0  # default is 0.0, which is <= 10.0
        assert sanitize_float(5.0, max_value=10.0) == 5.0
        assert sanitize_float(15.0, max_value=10.0, default=5.0) == 5.0
    
    def test_min_and_max_constraints(self):
        """Test both min and max constraints."""
        assert sanitize_float(5.0, min_value=10.0, max_value=20.0) == 10.0
        assert sanitize_float(15.0, min_value=10.0, max_value=20.0) == 15.0
        # When value exceeds max, returns default (0.0) if default <= max, else max
        assert sanitize_float(25.0, min_value=10.0, max_value=20.0) == 0.0  # default 0.0 <= 20.0
    
    def test_integer_input(self):
        """Test with integer input."""
        assert sanitize_float(42) == 42.0
        assert isinstance(sanitize_float(42), float)


class TestSanitizeJSON:
    """Tests for sanitize_json function."""
    
    def test_valid_dict(self):
        """Test with valid dictionary."""
        data = {"key": "value", "number": 123}
        result = sanitize_json(data)
        assert result == json.dumps(data)
        # Verify it's valid JSON
        assert json.loads(result) == data
    
    def test_valid_list(self):
        """Test with valid list."""
        data = [1, 2, 3, "test"]
        result = sanitize_json(data)
        assert result == json.dumps(data)
        assert json.loads(result) == data
    
    def test_none_value(self):
        """Test with None value."""
        result = sanitize_json(None)
        assert result == "{}"
        assert json.loads(result) == {}
    
    def test_custom_default(self):
        """Test with custom default."""
        result = sanitize_json(None, default='{"custom": true}')
        assert result == '{"custom": true}'
        assert json.loads(result) == {"custom": True}
    
    def test_non_serializable_object(self):
        """Test with non-serializable object."""
        class NonSerializable:
            pass
        
        result = sanitize_json(NonSerializable())
        assert result == "{}"
    
    def test_complex_nested_structure(self):
        """Test with complex nested structure."""
        data = {
            "level1": {
                "level2": {
                    "level3": [1, 2, 3]
                }
            },
            "array": [{"nested": "value"}]
        }
        result = sanitize_json(data)
        assert json.loads(result) == data
    
    def test_with_special_characters(self):
        """Test with special characters."""
        data = {"message": "Hello, \"world\"! \n New line"}
        result = sanitize_json(data)
        assert json.loads(result) == data


class TestValidateStatus:
    """Tests for validate_status function."""
    
    def test_valid_active_status(self):
        """Test with valid 'active' status."""
        assert validate_status("active") is True
    
    def test_valid_saved_status(self):
        """Test with valid 'saved' status."""
        assert validate_status("saved") is True
    
    def test_invalid_status(self):
        """Test with invalid status."""
        assert validate_status("invalid") is False
        assert validate_status("pending") is False
        assert validate_status("deleted") is False
        assert validate_status("") is False
    
    def test_case_sensitive(self):
        """Test that status is case-sensitive."""
        assert validate_status("Active") is False
        assert validate_status("ACTIVE") is False
        assert validate_status("Saved") is False


class TestValidateDiscountPercent:
    """Tests for validate_discount_percent function."""
    
    def test_valid_zero(self):
        """Test with zero discount."""
        assert validate_discount_percent(0.0) is True
    
    def test_valid_hundred(self):
        """Test with 100% discount."""
        assert validate_discount_percent(100.0) is True
    
    def test_valid_middle_value(self):
        """Test with middle value."""
        assert validate_discount_percent(50.0) is True
        assert validate_discount_percent(25.5) is True
    
    def test_negative_value(self):
        """Test with negative value."""
        assert validate_discount_percent(-1.0) is False
        assert validate_discount_percent(-0.1) is False
    
    def test_over_hundred(self):
        """Test with value over 100."""
        assert validate_discount_percent(100.1) is False
        assert validate_discount_percent(150.0) is False
    
    def test_integer_input(self):
        """Test with integer input."""
        assert validate_discount_percent(50) is True
        assert validate_discount_percent(0) is True
        assert validate_discount_percent(100) is True

