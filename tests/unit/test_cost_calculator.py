"""Unit tests for backend.services.cost_calculator."""
import pytest
from backend.services.cost_calculator import (
    convert_duration_to_hours,
    convert_duration_to_months,
    calculate_item_cost,
    calculate_quote_total
)


class TestConvertDurationToHours:
    """Tests for convert_duration_to_hours function."""
    
    def test_hours_unit(self):
        """Test conversion with hours unit."""
        assert convert_duration_to_hours(5.0, "hours") == 5.0
        assert convert_duration_to_hours(10.5, "hours") == 10.5
        assert convert_duration_to_hours(0, "hours") == 0.0
    
    def test_days_unit(self):
        """Test conversion with days unit."""
        assert convert_duration_to_hours(1.0, "days") == 24.0
        assert convert_duration_to_hours(2.5, "days") == 60.0
        assert convert_duration_to_hours(0, "days") == 0.0
    
    def test_weeks_unit(self):
        """Test conversion with weeks unit."""
        assert convert_duration_to_hours(1.0, "weeks") == 168.0  # 24 * 7
        assert convert_duration_to_hours(2.0, "weeks") == 336.0
        assert convert_duration_to_hours(0.5, "weeks") == 84.0
    
    def test_months_unit(self):
        """Test conversion with months unit."""
        assert convert_duration_to_hours(1.0, "months") == 720.0  # 24 * 30
        assert convert_duration_to_hours(2.0, "months") == 1440.0
        assert convert_duration_to_hours(0.5, "months") == 360.0
    
    def test_years_unit(self):
        """Test conversion with years unit."""
        assert convert_duration_to_hours(1.0, "years") == 8760.0  # 24 * 365
        assert convert_duration_to_hours(2.0, "years") == 17520.0
        assert convert_duration_to_hours(0.5, "years") == 4380.0
    
    def test_case_insensitive(self):
        """Test that unit is case-insensitive."""
        assert convert_duration_to_hours(1.0, "HOURS") == 1.0
        assert convert_duration_to_hours(1.0, "Days") == 24.0
        assert convert_duration_to_hours(1.0, "WEEKS") == 168.0
    
    def test_invalid_unit(self):
        """Test with invalid unit (should return duration as-is)."""
        assert convert_duration_to_hours(5.0, "invalid") == 5.0
        assert convert_duration_to_hours(10.0, "unknown") == 10.0
    
    def test_zero_duration(self):
        """Test with zero duration."""
        assert convert_duration_to_hours(0, "hours") == 0.0
        assert convert_duration_to_hours(0, "days") == 0.0
        assert convert_duration_to_hours(0, "years") == 0.0
    
    def test_none_duration(self):
        """Test with None duration raises TypeError."""
        with pytest.raises(TypeError):
            convert_duration_to_hours(None, "hours")


class TestConvertDurationToMonths:
    """Tests for convert_duration_to_months function."""
    
    def test_hours_unit(self):
        """Test conversion from hours to months."""
        # 1 hour = 1 / (24 * 30) months ≈ 0.001389
        result = convert_duration_to_months(24.0 * 30.0, "hours")
        assert abs(result - 1.0) < 0.01
    
    def test_days_unit(self):
        """Test conversion from days to months."""
        assert convert_duration_to_months(30.0, "days") == 1.0
        assert convert_duration_to_months(60.0, "days") == 2.0
        assert convert_duration_to_months(15.0, "days") == 0.5
    
    def test_weeks_unit(self):
        """Test conversion from weeks to months."""
        # 1 week ≈ 0.2308 months (1 / 4.33)
        result = convert_duration_to_months(4.33, "weeks")
        assert abs(result - 1.0) < 0.1
    
    def test_months_unit(self):
        """Test conversion with months unit."""
        assert convert_duration_to_months(1.0, "months") == 1.0
        assert convert_duration_to_months(2.5, "months") == 2.5
        assert convert_duration_to_months(0, "months") == 0.0
    
    def test_years_unit(self):
        """Test conversion from years to months."""
        assert convert_duration_to_months(1.0, "years") == 12.0
        assert convert_duration_to_months(2.0, "years") == 24.0
        assert convert_duration_to_months(0.5, "years") == 6.0
    
    def test_case_insensitive(self):
        """Test that unit is case-insensitive (lowercased in function)."""
        assert convert_duration_to_months(1.0, "MONTHS") == 1.0
        assert convert_duration_to_months(1.0, "months") == 1.0
        # 12 years = 144 months (12 * 12)
        assert convert_duration_to_months(12.0, "years") == 144.0
        assert convert_duration_to_months(12.0, "YEARS") == 144.0
    
    def test_invalid_unit(self):
        """Test with invalid unit (should return duration as-is)."""
        assert convert_duration_to_months(5.0, "invalid") == 5.0
    
    def test_zero_duration(self):
        """Test with zero duration."""
        assert convert_duration_to_months(0, "months") == 0.0
        assert convert_duration_to_months(0, "years") == 0.0


class TestCalculateItemCost:
    """Tests for calculate_item_cost function."""
    
    def test_basic_item_cost_hourly(self):
        """Test basic item cost calculation for hourly billing."""
        item = {
            "quantity": 2.0,
            "unit_price": 0.10,
            "resource_data": {"Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", None, 0.0)
        
        assert result["base_cost"] == 20.0  # 2 * 0.10 * 100
        assert result["quantity"] == 2.0
        assert result["unit_price"] == 0.10
        assert result["is_monthly"] is False
        assert result["commitment_discount_percent"] == 0
        assert result["global_discount_percent"] == 0.0
        assert result["final_cost"] == 20.0
    
    def test_basic_item_cost_monthly(self):
        """Test basic item cost calculation for monthly billing."""
        item = {
            "quantity": 1.0,
            "unit_price": 10.0,
            "resource_data": {"Flags": "PER_MONTH"}
        }
        result = calculate_item_cost(item, 2.0, "months", None, 0.0)
        
        assert result["base_cost"] == 20.0  # 1 * 10 * 2
        assert result["is_monthly"] is True
        assert result["duration_in_billing_unit"] == 2.0
    
    def test_item_cost_with_iops(self):
        """Test item cost with IOPS for io1 storage."""
        item = {
            "quantity": 1.0,
            "unit_price": 0.10,
            "iops_unit_price": 0.05,
            "resource_data": {"Flags": ""},
            "parameters": {"iops": 3000}
        }
        result = calculate_item_cost(item, 100.0, "hours", None, 0.0)
        
        # Base cost: 1 * 0.10 * 100 = 10.0
        # IOPS cost: 3000 * 0.05 * 100 = 15000.0
        # Total: 15010.0
        assert result["iops_cost"] == 15000.0
        assert result["base_cost"] == 15010.0
    
    def test_item_cost_with_commitment_discount_compute(self):
        """Test item cost with commitment discount for compute."""
        item = {
            "quantity": 1.0,
            "unit_price": 100.0,
            "resource_data": {"Category": "compute", "Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", "1year", 0.0)
        
        # Base: 1 * 100 * 100 = 10000
        # Commitment discount (40% for 1year compute): 4000
        # After commitment: 6000
        assert result["base_cost"] == 10000.0
        assert result["commitment_discount_percent"] == 40
        assert result["commitment_discount_amount"] == 4000.0
        assert result["cost_after_commitment_discount"] == 6000.0
        assert result["final_cost"] == 6000.0
    
    def test_item_cost_with_global_discount(self):
        """Test item cost with global discount."""
        item = {
            "quantity": 1.0,
            "unit_price": 100.0,
            "resource_data": {"Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", None, 10.0)
        
        # Base: 1 * 100 * 100 = 10000
        # Global discount (10%): 1000
        # Final: 9000
        assert result["base_cost"] == 10000.0
        assert result["global_discount_percent"] == 10.0
        assert result["global_discount_amount"] == 1000.0
        assert result["final_cost"] == 9000.0
    
    def test_item_cost_with_both_discounts(self):
        """Test item cost with both commitment and global discounts."""
        item = {
            "quantity": 1.0,
            "unit_price": 100.0,
            "resource_data": {"Category": "compute", "Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", "1year", 10.0)
        
        # Base: 10000
        # Commitment discount (40%): 4000, after: 6000
        # Global discount (10% on 6000): 600, final: 5400
        assert result["base_cost"] == 10000.0
        assert result["commitment_discount_amount"] == 4000.0
        assert result["cost_after_commitment_discount"] == 6000.0
        assert result["global_discount_amount"] == 600.0
        assert result["final_cost"] == 5400.0
    
    def test_item_cost_with_zero_quantity(self):
        """Test item cost with zero quantity."""
        item = {
            "quantity": 0.0,
            "unit_price": 100.0,
            "resource_data": {"Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", None, 0.0)
        
        assert result["base_cost"] == 0.0
        assert result["final_cost"] == 0.0
    
    def test_item_cost_with_zero_unit_price(self):
        """Test item cost with zero unit price."""
        item = {
            "quantity": 10.0,
            "unit_price": 0.0,
            "resource_data": {"Flags": ""}
        }
        result = calculate_item_cost(item, 100.0, "hours", None, 0.0)
        
        assert result["base_cost"] == 0.0
        assert result["final_cost"] == 0.0
    
    def test_item_cost_rounding(self):
        """Test that costs are properly rounded."""
        item = {
            "quantity": 1.0,
            "unit_price": 0.333333,
            "resource_data": {"Flags": ""}
        }
        result = calculate_item_cost(item, 3.0, "hours", None, 0.0)
        
        # Should round to 2 decimal places
        assert isinstance(result["base_cost"], float)
        assert len(str(result["base_cost"]).split('.')[-1]) <= 2


class TestCalculateQuoteTotal:
    """Tests for calculate_quote_total function."""
    
    def test_single_item_quote(self):
        """Test quote total with single item."""
        items = [{
            "quantity": 1.0,
            "unit_price": 10.0,
            "resource_data": {"Flags": ""}
        }]
        result = calculate_quote_total(items, 100.0, "hours", None, 0.0)
        
        assert result["item_count"] == 1
        assert result["base_total"] == 1000.0
        assert result["subtotal"] == 1000.0
        assert result["total"] == 1000.0
        assert len(result["items"]) == 1
    
    def test_multiple_items_quote(self):
        """Test quote total with multiple items."""
        items = [
            {"quantity": 1.0, "unit_price": 10.0, "resource_data": {"Flags": ""}},
            {"quantity": 2.0, "unit_price": 5.0, "resource_data": {"Flags": ""}}
        ]
        result = calculate_quote_total(items, 100.0, "hours", None, 0.0)
        
        # Item 1: 1 * 10 * 100 = 1000
        # Item 2: 2 * 5 * 100 = 1000
        # Total: 2000
        assert result["item_count"] == 2
        assert result["base_total"] == 2000.0
        assert result["total"] == 2000.0
    
    def test_quote_with_commitment_discounts(self):
        """Test quote total with commitment discounts."""
        items = [
            {
                "quantity": 1.0,
                "unit_price": 100.0,
                "resource_data": {"Category": "compute", "Flags": ""}
            }
        ]
        result = calculate_quote_total(items, 100.0, "hours", "1year", 0.0)
        
        # Base: 10000, commitment discount (40%): 4000
        assert result["base_total"] == 10000.0
        assert result["total_commitment_discounts"] == 4000.0
        assert result["subtotal"] == 6000.0
        assert result["total"] == 6000.0
    
    def test_quote_with_global_discount(self):
        """Test quote total with global discount."""
        items = [
            {"quantity": 1.0, "unit_price": 100.0, "resource_data": {"Flags": ""}}
        ]
        result = calculate_quote_total(items, 100.0, "hours", None, 20.0)
        
        # Base: 10000, global discount (20%): 2000
        assert result["base_total"] == 10000.0
        assert result["subtotal"] == 10000.0
        assert result["global_discount_amount"] == 2000.0
        assert result["total"] == 8000.0
    
    def test_quote_with_both_discounts(self):
        """Test quote total with both commitment and global discounts."""
        items = [
            {
                "quantity": 1.0,
                "unit_price": 100.0,
                "resource_data": {"Category": "compute", "Flags": ""}
            }
        ]
        result = calculate_quote_total(items, 100.0, "hours", "1year", 10.0)
        
        # Base: 10000
        # Commitment discount (40%): 4000, subtotal: 6000
        # Global discount (10% on 6000): 600, total: 5400
        assert result["base_total"] == 10000.0
        assert result["total_commitment_discounts"] == 4000.0
        assert result["subtotal"] == 6000.0
        assert result["global_discount_amount"] == 600.0
        assert result["total"] == 5400.0
    
    def test_quote_summary_structure(self):
        """Test that quote summary has correct structure."""
        items = [
            {"quantity": 1.0, "unit_price": 10.0, "resource_data": {"Flags": ""}}
        ]
        result = calculate_quote_total(items, 100.0, "hours", None, 0.0)
        
        assert "summary" in result
        assert "base_total" in result["summary"]
        assert "commitment_discounts" in result["summary"]
        assert "subtotal" in result["summary"]
        assert "global_discount" in result["summary"]
        assert "total" in result["summary"]
    
    def test_empty_items_list(self):
        """Test quote total with empty items list."""
        result = calculate_quote_total([], 100.0, "hours", None, 0.0)
        
        assert result["item_count"] == 0
        assert result["base_total"] == 0.0
        assert result["total"] == 0.0
        assert len(result["items"]) == 0

