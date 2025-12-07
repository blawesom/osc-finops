"""Unit tests for backend.services.discount_rules."""
import pytest
from backend.services.discount_rules import (
    get_resource_type,
    get_commitment_discount,
    COMMITMENT_DISCOUNTS
)


class TestGetResourceType:
    """Tests for get_resource_type function."""
    
    def test_compute_category(self):
        """Test with compute category."""
        catalog_item = {"Category": "compute"}
        assert get_resource_type(catalog_item) == "compute"
    
    def test_storage_category(self):
        """Test with storage category."""
        catalog_item = {"Category": "storage"}
        assert get_resource_type(catalog_item) == "storage"
    
    def test_network_category(self):
        """Test with network category."""
        catalog_item = {"Category": "network"}
        assert get_resource_type(catalog_item) == "network"
    
    def test_licence_category(self):
        """Test with licence category."""
        catalog_item = {"Category": "licence"}
        assert get_resource_type(catalog_item) == "licence"
    
    def test_case_insensitive(self):
        """Test that category is case-insensitive."""
        assert get_resource_type({"Category": "COMPUTE"}) == "compute"
        assert get_resource_type({"Category": "Storage"}) == "storage"
        assert get_resource_type({"Category": "NETWORK"}) == "network"
    
    def test_unknown_category(self):
        """Test with unknown category returns default."""
        catalog_item = {"Category": "unknown"}
        assert get_resource_type(catalog_item) == "default"
    
    def test_missing_category(self):
        """Test with missing Category field."""
        catalog_item = {}
        assert get_resource_type(catalog_item) == "default"
    
    def test_empty_category(self):
        """Test with empty category string."""
        catalog_item = {"Category": ""}
        assert get_resource_type(catalog_item) == "default"
    
    def test_none_category(self):
        """Test with None category raises AttributeError."""
        catalog_item = {"Category": None}
        with pytest.raises(AttributeError):
            get_resource_type(catalog_item)
    
    def test_other_categories(self):
        """Test with other categories that should default."""
        assert get_resource_type({"Category": "database"}) == "default"
        assert get_resource_type({"Category": "monitoring"}) == "default"
        assert get_resource_type({"Category": "security"}) == "default"


class TestGetCommitmentDiscount:
    """Tests for get_commitment_discount function."""
    
    def test_compute_1month(self):
        """Test compute resource with 1month commitment."""
        assert get_commitment_discount("compute", "1month") == 30
    
    def test_compute_1year(self):
        """Test compute resource with 1year commitment."""
        assert get_commitment_discount("compute", "1year") == 40
    
    def test_compute_3years(self):
        """Test compute resource with 3years commitment."""
        assert get_commitment_discount("compute", "3years") == 50
    
    def test_storage_no_discount(self):
        """Test storage resource has no commitment discounts."""
        assert get_commitment_discount("storage", "1month") == 0
        assert get_commitment_discount("storage", "1year") == 0
        assert get_commitment_discount("storage", "3years") == 0
    
    def test_network_no_discount(self):
        """Test network resource has no commitment discounts."""
        assert get_commitment_discount("network", "1month") == 0
        assert get_commitment_discount("network", "1year") == 0
        assert get_commitment_discount("network", "3years") == 0
    
    def test_licence_no_discount(self):
        """Test licence resource has no commitment discounts."""
        assert get_commitment_discount("licence", "1month") == 0
        assert get_commitment_discount("licence", "1year") == 0
        assert get_commitment_discount("licence", "3years") == 0
    
    def test_default_resource_type(self):
        """Test default resource type has no discounts."""
        assert get_commitment_discount("default", "1month") == 0
        assert get_commitment_discount("default", "1year") == 0
        assert get_commitment_discount("default", "3years") == 0
    
    def test_none_commitment_period(self):
        """Test with None commitment period."""
        assert get_commitment_discount("compute", None) == 0
        assert get_commitment_discount("storage", None) == 0
    
    def test_none_string_commitment(self):
        """Test with 'none' string commitment period."""
        assert get_commitment_discount("compute", "none") == 0
        assert get_commitment_discount("compute", "None") == 0
        assert get_commitment_discount("compute", "NONE") == 0
    
    def test_case_insensitive_commitment(self):
        """Test that commitment period is case-insensitive."""
        assert get_commitment_discount("compute", "1MONTH") == 30
        assert get_commitment_discount("compute", "1Year") == 40
        assert get_commitment_discount("compute", "3YEARS") == 50
    
    def test_invalid_commitment_period(self):
        """Test with invalid commitment period."""
        assert get_commitment_discount("compute", "invalid") == 0
        assert get_commitment_discount("compute", "2years") == 0
        assert get_commitment_discount("compute", "6months") == 0
    
    def test_unknown_resource_type(self):
        """Test with unknown resource type falls back to default."""
        assert get_commitment_discount("unknown", "1year") == 0
        assert get_commitment_discount("", "1year") == 0
    
    def test_empty_commitment_period(self):
        """Test with empty string commitment period."""
        assert get_commitment_discount("compute", "") == 0
    
    def test_all_resource_types_no_commitment(self):
        """Test all resource types return 0 with no commitment."""
        resource_types = ["compute", "storage", "network", "licence", "default"]
        for resource_type in resource_types:
            assert get_commitment_discount(resource_type, None) == 0
            assert get_commitment_discount(resource_type, "none") == 0
    
    def test_compute_discount_progression(self):
        """Test that compute discounts increase with commitment length."""
        assert get_commitment_discount("compute", "1month") == 30
        assert get_commitment_discount("compute", "1year") == 40
        assert get_commitment_discount("compute", "3years") == 50
        # Verify progression
        assert 30 < 40 < 50

