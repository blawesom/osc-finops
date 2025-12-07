"""Unit tests for backend.services.budget_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from backend.services.budget_service import (
    create_budget,
    get_budgets,
    get_budget,
    update_budget,
    delete_budget,
    get_budget_periods,
    calculate_budget_status
)
from backend.models.budget import Budget
from backend.models.user import User


class TestCreateBudget:
    """Tests for create_budget function."""
    
    @patch('backend.services.budget_service.SessionLocal')
    @patch('backend.services.budget_service.log_exception')
    def test_create_budget_success(self, mock_log, mock_session_local):
        """Test successful budget creation."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_budget = Mock(spec=Budget)
        mock_budget.budget_id = "budget-123"
        with patch('backend.services.budget_service.Budget') as mock_budget_class:
            mock_budget_class.return_value = mock_budget
            
            result = create_budget(
                user_id="user-123",
                name="Test Budget",
                amount=1000.0,
                period_type="monthly",
                start_date="2024-01-01"
            )
            
            assert result == mock_budget
            mock_budget_class.assert_called_once()
            mock_db.add.assert_called_once_with(mock_budget)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_budget)
    
    def test_create_budget_invalid_period_type(self):
        """Test create_budget with invalid period_type."""
        with pytest.raises(ValueError, match="period_type must be"):
            create_budget("user-123", "Test", 1000.0, "invalid", "2024-01-01")
    
    def test_create_budget_invalid_amount(self):
        """Test create_budget with invalid amount."""
        with pytest.raises(ValueError, match="amount must be greater than 0"):
            create_budget("user-123", "Test", -100.0, "monthly", "2024-01-01")
        
        with pytest.raises(ValueError, match="amount must be greater than 0"):
            create_budget("user-123", "Test", 0.0, "monthly", "2024-01-01")
    
    def test_create_budget_invalid_date_format(self):
        """Test create_budget with invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            create_budget("user-123", "Test", 1000.0, "monthly", "invalid-date")
    
    def test_create_budget_end_date_before_start(self):
        """Test create_budget with end_date before start_date."""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            create_budget(
                "user-123", "Test", 1000.0, "monthly",
                "2024-01-01", "2023-12-31"
            )
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_create_budget_user_not_found(self, mock_session_local):
        """Test create_budget when user doesn't exist."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            create_budget("user-123", "Test", 1000.0, "monthly", "2024-01-01")
    
    @patch('backend.services.budget_service.SessionLocal')
    @patch('backend.services.budget_service.log_exception')
    def test_create_budget_database_error(self, mock_log, mock_session_local):
        """Test create_budget handles database errors."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit.side_effect = Exception("DB Error")
        
        with pytest.raises(Exception):
            create_budget("user-123", "Test", 1000.0, "monthly", "2024-01-01")
        
        mock_db.rollback.assert_called_once()


class TestGetBudgets:
    """Tests for get_budgets function."""
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_get_budgets_success(self, mock_session_local):
        """Test successful get_budgets."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budgets = [Mock(spec=Budget), Mock(spec=Budget)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_budgets
        
        result = get_budgets("user-123")
        
        assert result == mock_budgets
        mock_db.query.assert_called_once_with(Budget)
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_get_budgets_empty(self, mock_session_local):
        """Test get_budgets with no budgets."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = get_budgets("user-123")
        
        assert result == []


class TestGetBudget:
    """Tests for get_budget function."""
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_get_budget_found(self, mock_session_local):
        """Test get_budget when budget exists."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budget = Mock(spec=Budget)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_budget
        
        result = get_budget("budget-123", "user-123")
        
        assert result == mock_budget
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_get_budget_not_found(self, mock_session_local):
        """Test get_budget when budget doesn't exist."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = get_budget("budget-123", "user-123")
        
        assert result is None


class TestUpdateBudget:
    """Tests for update_budget function."""
    
    @patch('backend.services.budget_service.SessionLocal')
    @patch('backend.services.budget_service.datetime')
    @patch('backend.services.budget_service.log_exception')
    def test_update_budget_success(self, mock_log, mock_datetime, mock_session_local):
        """Test successful budget update."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budget = Mock(spec=Budget)
        mock_budget.end_date = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_budget
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        result = update_budget("budget-123", "user-123", name="Updated Name")
        
        assert result == mock_budget
        assert mock_budget.name == "Updated Name"
        mock_db.commit.assert_called_once()
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_update_budget_not_found(self, mock_session_local):
        """Test update_budget when budget doesn't exist."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = update_budget("budget-123", "user-123", name="Updated")
        
        assert result is None
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_update_budget_invalid_amount(self, mock_session_local):
        """Test update_budget with invalid amount."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budget = Mock(spec=Budget)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_budget
        
        with pytest.raises(ValueError, match="amount must be greater than 0"):
            update_budget("budget-123", "user-123", amount=-100.0)
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_update_budget_invalid_period_type(self, mock_session_local):
        """Test update_budget with invalid period_type."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budget = Mock(spec=Budget)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_budget
        
        with pytest.raises(ValueError, match="period_type must be"):
            update_budget("budget-123", "user-123", period_type="invalid")


class TestDeleteBudget:
    """Tests for delete_budget function."""
    
    @patch('backend.services.budget_service.SessionLocal')
    @patch('backend.services.budget_service.log_exception')
    def test_delete_budget_success(self, mock_log, mock_session_local):
        """Test successful budget deletion."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_budget = Mock(spec=Budget)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_budget
        
        result = delete_budget("budget-123", "user-123")
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_budget)
        mock_db.commit.assert_called_once()
    
    @patch('backend.services.budget_service.SessionLocal')
    def test_delete_budget_not_found(self, mock_session_local):
        """Test delete_budget when budget doesn't exist."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = delete_budget("budget-123", "user-123")
        
        assert result is False
        mock_db.delete.assert_not_called()


class TestGetBudgetPeriods:
    """Tests for get_budget_periods function."""
    
    def test_get_budget_periods_monthly(self):
        """Test get_budget_periods for monthly budget."""
        budget = Mock(spec=Budget)
        budget.start_date = date(2024, 1, 1)
        budget.end_date = None
        budget.period_type = "monthly"
        budget.amount = 1000.0
        
        periods = get_budget_periods(budget, "2024-01-01", "2024-03-31")
        
        assert len(periods) == 3
        assert periods[0]["period"] == 0
        assert periods[0]["start_date"] == "2024-01-01"
        assert periods[0]["budget_amount"] == 1000.0
    
    def test_get_budget_periods_quarterly(self):
        """Test get_budget_periods for quarterly budget."""
        budget = Mock(spec=Budget)
        budget.start_date = date(2024, 1, 1)
        budget.end_date = None
        budget.period_type = "quarterly"
        budget.amount = 3000.0
        
        periods = get_budget_periods(budget, "2024-01-01", "2024-12-31")
        
        assert len(periods) == 4  # 4 quarters
        assert periods[0]["period"] == 0
        assert periods[0]["budget_amount"] == 3000.0
    
    def test_get_budget_periods_yearly(self):
        """Test get_budget_periods for yearly budget."""
        budget = Mock(spec=Budget)
        budget.start_date = date(2024, 1, 1)
        budget.end_date = None
        budget.period_type = "yearly"
        budget.amount = 12000.0
        
        periods = get_budget_periods(budget, "2024-01-01", "2025-12-31")
        
        assert len(periods) == 2  # 2 years
        assert periods[0]["budget_amount"] == 12000.0
    
    def test_get_budget_periods_with_end_date(self):
        """Test get_budget_periods respects budget end_date."""
        budget = Mock(spec=Budget)
        budget.start_date = date(2024, 1, 1)
        budget.end_date = date(2024, 6, 30)
        budget.period_type = "monthly"
        budget.amount = 1000.0
        
        periods = get_budget_periods(budget, "2024-01-01", "2024-12-31")
        
        assert len(periods) == 6  # Only 6 months until end_date
    
    def test_get_budget_periods_no_overlap(self):
        """Test get_budget_periods with date range before budget start."""
        budget = Mock(spec=Budget)
        budget.start_date = date(2026, 1, 1)  # Budget starts in 2026
        budget.end_date = None
        budget.period_type = "monthly"
        budget.amount = 1000.0
        
        # Request range is 2024-2025, before budget starts in 2026
        periods = get_budget_periods(budget, "2024-01-01", "2025-12-31")
        
        assert len(periods) == 0  # No overlap - budget hasn't started yet


class TestCalculateBudgetStatus:
    """Tests for calculate_budget_status function."""
    
    @patch('backend.services.budget_service.get_consumption')
    def test_calculate_budget_status_success(self, mock_get_consumption):
        """Test successful budget status calculation."""
        budget = Mock(spec=Budget)
        budget.budget_id = "budget-123"
        budget.name = "Test Budget"
        budget.start_date = date(2024, 1, 1)
        budget.end_date = None
        budget.period_type = "monthly"
        budget.amount = 1000.0
        
        mock_consumption = {
            "entries": [
                {
                    "FromDate": "2024-01-01",
                    "ToDate": "2024-01-31",
                    "Price": 500.0
                },
                {
                    "FromDate": "2024-02-01",
                    "ToDate": "2024-02-29",
                    "Price": 600.0
                }
            ],
            "currency": "EUR"
        }
        mock_get_consumption.return_value = mock_consumption
        
        with patch('backend.services.budget_service.get_budget_periods') as mock_periods:
            mock_periods.return_value = [
                {
                    "period": 0,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "budget_amount": 1000.0
                },
                {
                    "period": 1,
                    "start_date": "2024-02-01",
                    "end_date": "2024-02-29",
                    "budget_amount": 1000.0
                }
            ]
            
            result = calculate_budget_status(
                budget, "access_key", "secret_key", "eu-west-2",
                "account-123", "2024-01-01", "2024-02-29"
            )
            
            assert result["budget_id"] == "budget-123"
            assert result["budget_name"] == "Test Budget"
            assert len(result["periods"]) == 2
            assert result["total_budget"] == 2000.0
            assert result["total_spent"] == 1100.0
            assert result["currency"] == "EUR"
    
    @patch('backend.services.budget_service.get_budget_periods')
    def test_calculate_budget_status_no_periods(self, mock_periods):
        """Test calculate_budget_status with no periods."""
        budget = Mock(spec=Budget)
        budget.budget_id = "budget-123"
        budget.name = "Test Budget"
        mock_periods.return_value = []
        
        result = calculate_budget_status(
            budget, "access_key", "secret_key", "eu-west-2",
            "account-123", "2024-01-01", "2024-02-29"
        )
        
        assert result["periods"] == []
        assert result["total_budget"] == 0.0
        assert result["total_spent"] == 0.0

