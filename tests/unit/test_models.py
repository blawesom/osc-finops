"""Unit tests for backend models."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from backend.models.session import Session as SessionModel
from backend.models.user import User
from backend.models.quote import Quote
from backend.models.quote_item import QuoteItem
from backend.models.budget import Budget
from backend.config.settings import SESSION_TIMEOUT


class TestSessionModel:
    """Tests for Session model."""
    
    @patch('backend.models.session.datetime')
    def test_session_init_sets_expires_at(self, mock_datetime):
        """Test Session initialization sets expires_at."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session = SessionModel(
            user_id="user-123",
            access_key="access_key",
            secret_key="secret_key",
            region="eu-west-2"
        )
        
        assert session.expires_at == now + timedelta(seconds=SESSION_TIMEOUT)
    
    @patch('backend.models.session.datetime')
    def test_update_activity(self, mock_datetime):
        """Test update_activity updates last_activity and extends expiration."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        later = now + timedelta(minutes=10)
        mock_datetime.utcnow.side_effect = [now, later]
        
        session = SessionModel(
            user_id="user-123",
            access_key="key",
            secret_key="secret",
            region="eu-west-2",
            expires_at=now + timedelta(seconds=SESSION_TIMEOUT)
        )
        original_expires = session.expires_at
        
        session.update_activity()
        
        assert session.last_activity == later
        assert session.expires_at > original_expires
        assert session.updated_at == later
    
    @patch('backend.models.session.datetime')
    def test_is_expired_false(self, mock_datetime):
        """Test is_expired returns False for active session."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        session = SessionModel(
            user_id="user-123",
            access_key="key",
            secret_key="secret",
            region="eu-west-2",
            expires_at=now + timedelta(seconds=SESSION_TIMEOUT)
        )
        
        assert session.is_expired() is False
    
    @patch('backend.models.session.datetime')
    def test_is_expired_true(self, mock_datetime):
        """Test is_expired returns True for expired session."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        later = now + timedelta(seconds=SESSION_TIMEOUT + 1)
        mock_datetime.utcnow.return_value = later
        
        session = SessionModel(
            user_id="user-123",
            access_key="key",
            secret_key="secret",
            region="eu-west-2",
            expires_at=now + timedelta(seconds=SESSION_TIMEOUT)
        )
        
        assert session.is_expired() is True
    
    def test_to_dict(self):
        """Test to_dict excludes sensitive data."""
        session = SessionModel(
            user_id="user-123",
            access_key="access_key",
            secret_key="secret_key",
            region="eu-west-2"
        )
        
        result = session.to_dict()
        
        assert "session_id" in result
        assert "user_id" in result
        assert "region" in result
        assert "access_key" not in result
        assert "secret_key" not in result


class TestUserModel:
    """Tests for User model."""
    
    def test_user_init(self):
        """Test User initialization."""
        user = User(
            account_id="account-123",
            access_key="access_key"
        )
        
        assert user.account_id == "account-123"
        assert user.access_key == "access_key"
        assert user.user_id is not None
        assert user.is_active is True
    
    def test_user_to_dict(self):
        """Test User to_dict method."""
        user = User(
            account_id="account-123",
            access_key="access_key"
        )
        
        result = user.to_dict()
        
        assert "user_id" in result
        assert "account_id" in result
        assert "is_active" in result


class TestQuoteModel:
    """Tests for Quote model."""
    
    def test_quote_init(self):
        """Test Quote initialization."""
        quote = Quote(
            name="Test Quote",
            user_id="user-123",
            status="active",
            duration=1.0,
            duration_unit="months",
            global_discount_percent=0.0
        )
        
        assert quote.name == "Test Quote"
        assert quote.user_id == "user-123"
        assert quote.status == "active"
        assert quote.duration == 1.0
        assert quote.duration_unit == "months"
        assert quote.global_discount_percent == 0.0
    
    @patch('backend.services.cost_calculator.calculate_quote_total')
    def test_quote_to_dict(self, mock_calc):
        """Test Quote to_dict includes calculation."""
        quote = Quote(
            name="Test Quote",
            user_id="user-123",
            status="active",
            duration=1.0
        )
        quote.items = []
        
        mock_calc.return_value = {"total": 100.0}
        
        result = quote.to_dict()
        
        assert "quote_id" in result
        assert "name" in result
        assert "status" in result
        assert "calculation" in result
        assert result["calculation"]["total"] == 100.0


class TestQuoteItemModel:
    """Tests for QuoteItem model."""
    
    def test_quote_item_init(self):
        """Test QuoteItem initialization."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data='{"Category": "compute"}',
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        assert item.quote_id == "quote-123"
        assert item.resource_name == "VM"
        assert item.resource_type == "compute"
        assert item.quantity == 1.0
        assert item.unit_price == 0.1
        assert item.region == "eu-west-2"
    
    def test_get_resource_data(self):
        """Test get_resource_data parses JSON."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data='{"Category": "compute", "Type": "VM"}',
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        result = item.get_resource_data()
        
        assert isinstance(result, dict)
        assert result["Category"] == "compute"
        assert result["Type"] == "VM"
    
    def test_get_resource_data_invalid_json(self):
        """Test get_resource_data handles invalid JSON."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data="invalid json",
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        result = item.get_resource_data()
        
        assert result == {}
    
    def test_set_resource_data(self):
        """Test set_resource_data stores JSON."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data="{}",
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        item.set_resource_data({"Category": "compute"})
        
        assert "Category" in item.get_resource_data()
    
    def test_get_parameters(self):
        """Test get_parameters parses JSON."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data="{}",
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2",
            parameters='{"key": "value"}'
        )
        
        result = item.get_parameters()
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
    
    def test_set_parameters_none(self):
        """Test set_parameters with None."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data="{}",
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        item.set_parameters(None)
        
        assert item.parameters is None
    
    def test_to_dict(self):
        """Test QuoteItem to_dict."""
        item = QuoteItem(
            quote_id="quote-123",
            resource_name="VM",
            resource_type="compute",
            resource_data='{"Category": "compute"}',
            quantity=1.0,
            unit_price=0.1,
            region="eu-west-2"
        )
        
        result = item.to_dict()
        
        assert "id" in result
        assert result["resource_name"] == "VM"
        assert result["resource_type"] == "compute"
        assert result["quantity"] == 1.0
        assert result["unit_price"] == 0.1


class TestBudgetModel:
    """Tests for Budget model."""
    
    def test_budget_init(self):
        """Test Budget initialization."""
        budget = Budget(
            user_id="user-123",
            name="Monthly Budget",
            amount=1000.0,
            period_type="monthly",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 1, 31).date()
        )
        
        assert budget.user_id == "user-123"
        assert budget.name == "Monthly Budget"
        assert budget.amount == 1000.0
        assert budget.period_type == "monthly"
        assert budget.start_date == datetime(2024, 1, 1).date()
        assert budget.end_date == datetime(2024, 1, 31).date()
    
    def test_budget_to_dict(self):
        """Test Budget to_dict."""
        budget = Budget(
            user_id="user-123",
            name="Monthly Budget",
            amount=1000.0,
            period_type="monthly",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 1, 31).date()
        )
        
        result = budget.to_dict()
        
        assert "budget_id" in result
        assert result["name"] == "Monthly Budget"
        assert result["amount"] == 1000.0
        assert result["period_type"] == "monthly"
        assert "start_date" in result
        assert "end_date" in result

