"""Unit tests for cost API format functions."""
import pytest
from backend.api.cost import format_human_readable, format_csv


class TestFormatHumanReadable:
    """Tests for format_human_readable function."""
    
    def test_format_human_readable_basic(self):
        """Test basic human-readable formatting."""
        cost_data = {
            "totals": {
                "cost_per_hour": 0.5,
                "cost_per_month": 360.0,
                "cost_per_year": 4380.0,
                "resource_count": 5,
                "resource_type_count": 2
            },
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_human_readable(cost_data)
        
        assert "Current Cost Evaluation" in result
        assert "eu-west-2" in result
        assert "EUR" in result
        assert "0.5000" in result
        assert "360.00" in result
    
    def test_format_human_readable_with_breakdown(self):
        """Test human-readable formatting with breakdown."""
        cost_data = {
            "totals": {
                "cost_per_hour": 0.5,
                "cost_per_month": 360.0,
                "resource_count": 5
            },
            "breakdown": {
                "by_resource_type": {
                    "vm": {
                        "count": 3,
                        "cost_per_hour": 0.3,
                        "cost_per_month": 216.0
                    }
                },
                "by_category": {
                    "compute": {
                        "count": 3,
                        "cost_per_hour": 0.3,
                        "cost_per_month": 216.0
                    }
                }
            },
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_human_readable(cost_data)
        
        assert "BREAKDOWN BY RESOURCE TYPE" in result
        assert "BREAKDOWN BY CATEGORY" in result
        assert "vm" in result
    
    def test_format_human_readable_with_resources(self):
        """Test human-readable formatting with top resources."""
        cost_data = {
            "totals": {
                "cost_per_hour": 0.5,
                "cost_per_month": 360.0,
                "resource_count": 2
            },
            "resources": [
                {
                    "resource_id": "i-123",
                    "resource_type": "vm",
                    "cost_per_month": 216.0
                },
                {
                    "resource_id": "vol-456",
                    "resource_type": "volume",
                    "cost_per_month": 144.0
                }
            ],
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_human_readable(cost_data)
        
        assert "TOP 10 RESOURCES" in result
        assert "i-123" in result
        assert "vol-456" in result
    
    def test_format_human_readable_empty_data(self):
        """Test human-readable formatting with empty data."""
        cost_data = {
            "totals": {},
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_human_readable(cost_data)
        
        assert "Current Cost Evaluation" in result
        assert "eu-west-2" in result


class TestFormatCSV:
    """Tests for format_csv function."""
    
    def test_format_csv_basic(self):
        """Test basic CSV formatting."""
        cost_data = {
            "resources": [
                {
                    "resource_id": "i-123",
                    "resource_type": "vm",
                    "cost_per_hour": 0.1,
                    "cost_per_month": 72.0
                }
            ],
            "totals": {
                "cost_per_hour": 0.1,
                "cost_per_month": 72.0
            },
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_csv(cost_data)
        
        assert "Resource ID" in result
        assert "Resource Type" in result
        assert "Cost per Hour" in result
        assert "Cost per Month" in result
        assert "i-123" in result
    
    def test_format_csv_empty_resources(self):
        """Test CSV formatting with no resources."""
        cost_data = {
            "resources": [],
            "totals": {
                "cost_per_hour": 0.0,
                "cost_per_month": 0.0
            },
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_csv(cost_data)
        
        assert "Resource ID" in result  # Header should be present
    
    def test_format_csv_with_breakdown(self):
        """Test CSV formatting includes breakdown data."""
        cost_data = {
            "resources": [
                {
                    "resource_id": "i-123",
                    "resource_type": "vm",
                    "cost_per_hour": 0.1,
                    "cost_per_month": 72.0
                }
            ],
            "breakdown": {
                "by_resource_type": {
                    "vm": {
                        "count": 1,
                        "cost_per_hour": 0.1,
                        "cost_per_month": 72.0
                    }
                }
            },
            "totals": {
                "cost_per_hour": 0.1,
                "cost_per_month": 72.0
            },
            "currency": "EUR",
            "region": "eu-west-2"
        }
        
        result = format_csv(cost_data)
        
        assert "Resource ID" in result
        assert "i-123" in result
