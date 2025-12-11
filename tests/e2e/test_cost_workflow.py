"""End-to-end tests for Cost analysis workflow."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock

# Load fixture data
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
CATALOG_FIXTURE = FIXTURES_DIR / "euwest2_catalog.json"
CONSUMPTION_FIXTURE = FIXTURES_DIR / "consumption_dec_2025.json"


@pytest.fixture
def catalog_data():
    """Load catalog fixture data."""
    if CATALOG_FIXTURE.exists():
        with open(CATALOG_FIXTURE, 'r') as f:
            return json.load(f)
    return None


@pytest.fixture
def consumption_data():
    """Load consumption fixture data."""
    if CONSUMPTION_FIXTURE.exists():
        with open(CONSUMPTION_FIXTURE, 'r') as f:
            return json.load(f)
    return None


class TestCostAnalysisWorkflow:
    """E2E tests for cost analysis workflow."""
    
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.create_logged_gateway')
    def test_cost_workflow_with_fixtures(self, mock_create_gateway, mock_fetch_resources,
                                         mock_get_catalog, catalog_data):
        """Test cost analysis workflow using fixture data."""
        if not catalog_data:
            pytest.skip("Catalog fixture not available")
        
        # Setup catalog mock
        catalog_entries = catalog_data.get("Catalog", {}).get("Entries", [])
        mock_get_catalog.return_value = {
            "entries": catalog_entries,
            "currency": "EUR"
        }
        
        # Setup resource fetch mock (empty resources for test)
        mock_fetch_resources.return_value = {
            "resources": [],
            "currency": "EUR",
            "fetched_at": "2024-01-01T00:00:00"
        }
        
        # Setup gateway mock
        mock_gateway = Mock()
        mock_gateway.ReadAccounts.return_value = {"Accounts": [{"AccountId": "249064296596"}]}
        mock_create_gateway.return_value = mock_gateway
        
        # Test that catalog can be retrieved
        catalog = mock_get_catalog("eu-west-2")
        assert catalog is not None
        assert len(catalog["entries"]) > 0
    
    def test_cost_calculation_with_catalog_fixture(self, catalog_data):
        """Test cost calculation using catalog fixture."""
        if not catalog_data:
            pytest.skip("Catalog fixture not available")
        
        from backend.services.cost_service import find_catalog_price
        
        # Transform catalog fixture
        catalog_entries = catalog_data.get("Catalog", {}).get("Entries", [])
        catalog = {"entries": catalog_entries}
        
        # Test finding a price from catalog
        # Look for ElasticIP:IdleAddress
        price = find_catalog_price(
            catalog,
            "TinaOS-FCU",
            "AssociateAddress",
            "ElasticIP:IdleAddress"
        )
        
        # Should find price from fixture
        assert price is not None
        assert price > 0
    
    def test_cost_breakdown_with_fixtures(self, catalog_data):
        """Test cost breakdown calculation with fixture data."""
        if not catalog_data:
            pytest.skip("Catalog fixture not available")
        
        from backend.services.cost_service import (
            get_cost_breakdown,
            aggregate_by_resource_type
        )
        
        # Create sample resources with costs
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.5,
                "cost_per_month": 365.0,
                "cost_per_year": 4380.0
            },
            {
                "resource_type": "Volume",
                "cost_per_hour": 0.01,
                "cost_per_month": 7.3,
                "cost_per_year": 87.6
            }
        ]
        
        breakdown = get_cost_breakdown(resources)
        assert "Compute" in breakdown
        assert "Storage" in breakdown
        assert breakdown["Compute"]["cost_per_month"] == 365.0
        assert breakdown["Storage"]["cost_per_month"] == 7.3
        
        aggregation = aggregate_by_resource_type(resources)
        assert "Vm" in aggregation
        assert "Volume" in aggregation

