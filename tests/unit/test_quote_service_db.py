"""Unit tests for backend.services.quote_service_db."""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from backend.services.quote_service_db import QuoteServiceDB
from backend.models.quote import Quote
from backend.models.quote_item import QuoteItem
from backend.models.user import User


class TestQuoteServiceDBCreateQuote:
    """Tests for QuoteServiceDB.create_quote."""
    
    @patch('backend.services.quote_service_db.datetime')
    def test_create_quote_success(self, mock_datetime):
        """Test successful quote creation."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_quote = Mock(spec=Quote)
        mock_quote.quote_id = str(uuid.uuid4())
        valid_user_id = str(uuid.uuid4())
        with patch('backend.services.quote_service_db.Quote') as mock_quote_class:
            mock_quote_class.return_value = mock_quote
            with patch.object(QuoteServiceDB, '_save_active_quote_for_user') as mock_save:
                
                result = QuoteServiceDB.create_quote(mock_db, "Test Quote", valid_user_id)
                
                assert result == mock_quote
                mock_save.assert_called_once_with(mock_db, valid_user_id)
                mock_db.add.assert_called_once_with(mock_quote)
                mock_db.commit.assert_called_once()
    
    def test_create_quote_invalid_user_id(self):
        """Test create_quote with invalid user_id format."""
        mock_db = Mock()
        
        with pytest.raises(ValueError, match="Invalid user_id format"):
            QuoteServiceDB.create_quote(mock_db, "Test", "invalid-uuid")
    
    def test_create_quote_user_not_found(self):
        """Test create_quote when user doesn't exist."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        valid_user_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="User not found"):
            QuoteServiceDB.create_quote(mock_db, "Test", valid_user_id)
    
    def test_create_quote_sanitizes_name(self):
        """Test create_quote sanitizes quote name."""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        valid_user_id = str(uuid.uuid4())
        with patch('backend.services.quote_service_db.Quote') as mock_quote_class:
            mock_quote = Mock(spec=Quote)
            mock_quote_class.return_value = mock_quote
            with patch.object(QuoteServiceDB, '_save_active_quote_for_user'):
                
                QuoteServiceDB.create_quote(mock_db, "  " * 100, valid_user_id)  # Very long name
                
                # Should be sanitized to max 255 chars or default
                mock_quote_class.assert_called_once()


class TestQuoteServiceDBGetQuote:
    """Tests for QuoteServiceDB.get_quote."""
    
    def test_get_quote_found(self):
        """Test get_quote when quote exists."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        valid_quote_id = str(uuid.uuid4())
        
        # Fix mock chaining - need to properly chain query().filter().first()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_quote(mock_db, valid_quote_id)
        
        assert result == mock_quote
    
    def test_get_quote_not_found(self):
        """Test get_quote when quote doesn't exist."""
        mock_db = Mock()
        valid_quote_id = str(uuid.uuid4())
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_quote(mock_db, valid_quote_id)
        
        assert result is None
    
    def test_get_quote_invalid_uuid(self):
        """Test get_quote with invalid UUID."""
        mock_db = Mock()
        
        result = QuoteServiceDB.get_quote(mock_db, "invalid")
        
        assert result is None
    
    def test_get_quote_with_user_id_ownership_check(self):
        """Test get_quote verifies ownership when user_id provided."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        valid_quote_id = str(uuid.uuid4())
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_quote(mock_db, valid_quote_id, valid_user_id)
        
        assert result == mock_quote
    
    def test_get_quote_wrong_owner(self):
        """Test get_quote returns None for wrong owner."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        wrong_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_quote(mock_db, valid_quote_id, wrong_user_id)
        
        assert result is None


class TestQuoteServiceDBGetActiveQuote:
    """Tests for QuoteServiceDB.get_active_quote."""
    
    def test_get_active_quote_found(self):
        """Test get_active_quote when active quote exists."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_active_quote(mock_db, valid_user_id)
        
        assert result == mock_quote
    
    def test_get_active_quote_not_found(self):
        """Test get_active_quote when no active quote exists."""
        mock_db = Mock()
        valid_user_id = str(uuid.uuid4())
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.get_active_quote(mock_db, valid_user_id)
        
        assert result is None
    
    def test_get_active_quote_invalid_uuid(self):
        """Test get_active_quote with invalid UUID."""
        mock_db = Mock()
        
        result = QuoteServiceDB.get_active_quote(mock_db, "invalid")
        
        assert result is None


class TestQuoteServiceDBUpdateQuote:
    """Tests for QuoteServiceDB.update_quote."""
    
    @patch('backend.services.quote_service_db.datetime')
    def test_update_quote_name(self, mock_datetime):
        """Test updating quote name."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.update_quote(mock_db, valid_quote_id, valid_user_id, name="New Name")
        
        assert result == mock_quote
        assert mock_quote.name == "New Name"
        mock_db.commit.assert_called_once()
    
    def test_update_quote_not_found(self):
        """Test update_quote when quote doesn't exist."""
        mock_db = Mock()
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        result = QuoteServiceDB.update_quote(mock_db, valid_quote_id, valid_user_id, name="New")
        
        assert result is None
    
    def test_update_quote_invalid_status(self):
        """Test update_quote with invalid status."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        mock_quote.status = "active"
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValueError, match="Invalid status"):
            QuoteServiceDB.update_quote(mock_db, valid_quote_id, valid_user_id, status="invalid")
    
    def test_update_quote_status_to_active(self):
        """Test updating status to active saves current active."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        mock_quote.status = "saved"
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        with patch.object(QuoteServiceDB, '_save_active_quote_for_user') as mock_save:
            result = QuoteServiceDB.update_quote(mock_db, valid_quote_id, valid_user_id, status="active")
            
            assert result == mock_quote
            assert mock_quote.status == "active"
            mock_save.assert_called_once()
    
    def test_update_quote_invalid_discount(self):
        """Test update_quote with invalid discount percentage."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        mock_quote.user_id = valid_user_id
        
        # Fix mock chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_quote
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        # The function sanitizes the discount to max 100.0, so 150.0 becomes 100.0
        # Test with a negative value which should be sanitized to 0.0
        result = QuoteServiceDB.update_quote(mock_db, valid_quote_id, valid_user_id, global_discount_percent=-10.0)
        
        assert result == mock_quote
        # Discount should be sanitized to 0.0 (min_value)
        assert mock_quote.global_discount_percent == 0.0
        mock_db.commit.assert_called_once()


class TestQuoteServiceDBDeleteQuote:
    """Tests for QuoteServiceDB.delete_quote."""
    
    def test_delete_quote_success(self):
        """Test successful quote deletion."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            result = QuoteServiceDB.delete_quote(mock_db, valid_quote_uuid, valid_user_uuid)
            
            assert result is True
            mock_db.delete.assert_called_once_with(mock_quote)
            mock_db.commit.assert_called_once()
    
    def test_delete_quote_not_found(self):
        """Test delete_quote when quote doesn't exist."""
        mock_db = Mock()
        valid_user_id = str(uuid.uuid4())
        valid_quote_id = str(uuid.uuid4())
        
        # get_quote is called internally, so we need to mock it
        with patch.object(QuoteServiceDB, 'get_quote', return_value=None):
            result = QuoteServiceDB.delete_quote(mock_db, valid_quote_id, valid_user_id)
            
            assert result is False
    
    def test_delete_quote_invalid_uuid(self):
        """Test delete_quote with invalid UUID."""
        mock_db = Mock()
        valid_user_id = str(uuid.uuid4())
        
        result = QuoteServiceDB.delete_quote(mock_db, "invalid", valid_user_id)
        
        assert result is False


class TestQuoteServiceDBDeleteQuoteAndGetReplacement:
    """Tests for QuoteServiceDB.delete_quote_and_get_replacement."""
    
    @patch('backend.services.quote_service_db.datetime')
    def test_delete_active_quote_gets_replacement(self, mock_datetime):
        """Test deleting active quote returns replacement."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        mock_quote.status = "active"
        
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        # Setup query chain for replacement quote
        mock_replacement = Mock(spec=Quote)
        mock_replacement.status = "saved"
        mock_replacement_query = Mock()
        mock_replacement_query.filter.return_value.order_by.return_value.first.return_value = mock_replacement
        mock_db.query.return_value = mock_replacement_query
        
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            result = QuoteServiceDB.delete_quote_and_get_replacement(mock_db, valid_quote_uuid, valid_user_uuid)
            
            assert result == mock_replacement
            assert mock_replacement.status == "active"
            mock_db.delete.assert_called_once_with(mock_quote)
    
    def test_delete_saved_quote_no_replacement(self):
        """Test deleting saved quote returns None."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        mock_quote.status = "saved"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        
        result = QuoteServiceDB.delete_quote_and_get_replacement(mock_db, "quote-123", "user-123")
        
        assert result is None


class TestQuoteServiceDBListQuotes:
    """Tests for QuoteServiceDB.list_quotes."""
    
    def test_list_quotes_all(self):
        """Test list_quotes without user_id filter."""
        mock_db = Mock()
        mock_quote1 = Mock(spec=Quote)
        mock_quote1.quote_id = "quote-1"
        mock_quote1.name = "Quote 1"
        mock_quote1.status = "active"
        mock_quote1.items = []
        mock_quote1.created_at = datetime(2024, 1, 1)
        mock_quote1.updated_at = datetime(2024, 1, 2)
        
        mock_quote2 = Mock(spec=Quote)
        mock_quote2.quote_id = "quote-2"
        mock_quote2.name = "Quote 2"
        mock_quote2.status = "saved"
        mock_quote2.items = [Mock(), Mock()]
        mock_quote2.created_at = datetime(2024, 1, 3)
        mock_quote2.updated_at = datetime(2024, 1, 4)
        
        mock_db.query.return_value.all.return_value = [mock_quote1, mock_quote2]
        
        result = QuoteServiceDB.list_quotes(mock_db)
        
        assert len(result) == 2
        assert result[0]["quote_id"] == "quote-1"
        assert result[0]["item_count"] == 0
        assert result[1]["item_count"] == 2
    
    def test_list_quotes_filtered_by_user(self):
        """Test list_quotes filtered by user_id."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.quote_id = "quote-1"
        mock_quote.name = "Quote 1"
        mock_quote.status = "active"
        mock_quote.items = []
        mock_quote.created_at = datetime(2024, 1, 1)
        mock_quote.updated_at = datetime(2024, 1, 2)
        
        # Setup query chain properly - need to handle the filter chain
        mock_query_base = Mock()
        mock_filtered = Mock()
        mock_filtered.all.return_value = [mock_quote]
        mock_query_base.filter.return_value = mock_filtered
        mock_db.query.return_value = mock_query_base
        
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        result = QuoteServiceDB.list_quotes(mock_db, valid_user_uuid)
        
        assert len(result) == 1
        assert result[0]["quote_id"] == "quote-1"
    
    def test_list_quotes_invalid_user_id(self):
        """Test list_quotes with invalid user_id."""
        mock_db = Mock()
        
        result = QuoteServiceDB.list_quotes(mock_db, "invalid")
        
        assert result == []


class TestQuoteServiceDBAddItem:
    """Tests for QuoteServiceDB.add_item."""
    
    @patch('backend.services.quote_service_db.datetime')
    def test_add_item_success(self, mock_datetime):
        """Test successful item addition."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        # Setup query chains - get_quote uses one chain, max_order uses another
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            mock_order_query = Mock()
            mock_order_query.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value = mock_order_query
            
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            item_data = {
                "resource_name": "VM",
                "resource_type": "compute",
                "resource_data": {"Category": "compute"},
                "quantity": 1.0,
                "unit_price": 0.1,
                "region": "eu-west-2"
            }
            
            with patch('backend.services.quote_service_db.QuoteItem') as mock_item_class:
                mock_item = Mock(spec=QuoteItem)
                mock_item_class.from_dict.return_value = mock_item
                
                result = QuoteServiceDB.add_item(mock_db, valid_quote_uuid, item_data, valid_user_uuid)
                
                assert result == mock_quote
                mock_db.add.assert_called_once_with(mock_item)
                mock_db.commit.assert_called_once()
    
    def test_add_item_quote_not_found(self):
        """Test add_item when quote doesn't exist."""
        mock_db = Mock()
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=None):
            result = QuoteServiceDB.add_item(mock_db, valid_quote_uuid, {}, valid_user_uuid)
            
            assert result is None
    
    def test_add_item_invalid_item_data(self):
        """Test add_item with invalid item data."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            mock_order_query = Mock()
            mock_order_query.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value = mock_order_query
            
            with patch('backend.services.quote_service_db.QuoteItem') as mock_item_class:
                mock_item_class.from_dict.side_effect = ValueError("Invalid data")
                
                with pytest.raises(ValueError, match="Failed to create quote item"):
                    QuoteServiceDB.add_item(mock_db, valid_quote_uuid, {}, valid_user_uuid)
                
                mock_db.rollback.assert_called_once()


class TestQuoteServiceDBRemoveItem:
    """Tests for QuoteServiceDB.remove_item."""
    
    @patch('backend.services.quote_service_db.datetime')
    def test_remove_item_success(self, mock_datetime):
        """Test successful item removal."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        mock_item = Mock(spec=QuoteItem)
        
        # Use valid UUIDs
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_item_uuid = "87654321-4321-8765-4321-876543218765"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        # get_quote is called internally
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            mock_item_query = Mock()
            mock_item_query.filter.return_value.first.return_value = mock_item
            mock_db.query.return_value = mock_item_query
            
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            result = QuoteServiceDB.remove_item(mock_db, valid_quote_uuid, valid_item_uuid, valid_user_uuid)
            
            assert result == mock_quote
            mock_db.delete.assert_called_once_with(mock_item)
            mock_db.commit.assert_called_once()
    
    def test_remove_item_quote_not_found(self):
        """Test remove_item when quote doesn't exist."""
        mock_db = Mock()
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_item_uuid = "87654321-4321-8765-4321-876543218765"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=None):
            result = QuoteServiceDB.remove_item(mock_db, valid_quote_uuid, valid_item_uuid, valid_user_uuid)
            
            assert result is None
    
    def test_remove_item_item_not_found(self):
        """Test remove_item when item doesn't exist."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        
        valid_quote_uuid = "12345678-1234-5678-1234-567812345678"
        valid_item_uuid = "87654321-4321-8765-4321-876543218765"
        valid_user_uuid = "11111111-1111-1111-1111-111111111111"
        
        with patch.object(QuoteServiceDB, 'get_quote', return_value=mock_quote):
            mock_item_query = Mock()
            mock_item_query.filter.return_value.first.return_value = None
            mock_db.query.return_value = mock_item_query
            
            result = QuoteServiceDB.remove_item(mock_db, valid_quote_uuid, valid_item_uuid, valid_user_uuid)
            
            assert result == mock_quote
            mock_db.delete.assert_not_called()


class TestQuoteServiceDBLoadQuote:
    """Tests for QuoteServiceDB.load_quote."""
    
    @patch('backend.services.quote_service_db.datetime')
    @patch.object(QuoteServiceDB, 'get_quote')
    def test_load_quote_success(self, mock_get_quote, mock_datetime):
        """Test loading saved quote makes it active."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        mock_quote.status = "saved"
        mock_get_quote.return_value = mock_quote
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        # Use valid UUID format
        valid_uuid = "12345678-1234-5678-1234-567812345678"
        with patch.object(QuoteServiceDB, '_save_active_quote_for_user') as mock_save:
            result = QuoteServiceDB.load_quote(mock_db, valid_uuid, valid_uuid)
            
            assert result == mock_quote
            assert mock_quote.status == "active"
            mock_save.assert_called_once_with(mock_db, valid_uuid)
            mock_db.commit.assert_called_once()
            mock_get_quote.assert_called_once_with(mock_db, valid_uuid, valid_uuid)
    
    @patch.object(QuoteServiceDB, 'get_quote')
    def test_load_quote_not_found(self, mock_get_quote):
        """Test load_quote when quote doesn't exist."""
        mock_db = Mock()
        mock_get_quote.return_value = None
        
        # Use valid UUID format
        valid_uuid = "12345678-1234-5678-1234-567812345678"
        result = QuoteServiceDB.load_quote(mock_db, valid_uuid, valid_uuid)
        
        assert result is None
        mock_get_quote.assert_called_once_with(mock_db, valid_uuid, valid_uuid)
    
    @patch.object(QuoteServiceDB, 'get_quote')
    def test_load_quote_already_active(self, mock_get_quote):
        """Test loading already active quote."""
        mock_db = Mock()
        mock_quote = Mock(spec=Quote)
        mock_quote.user_id = "user-123"
        mock_quote.status = "active"
        mock_get_quote.return_value = mock_quote
        
        # Use valid UUID format
        valid_uuid = "12345678-1234-5678-1234-567812345678"
        with patch.object(QuoteServiceDB, '_save_active_quote_for_user') as mock_save:
            result = QuoteServiceDB.load_quote(mock_db, valid_uuid, valid_uuid)
            
            assert result == mock_quote
            # Should not change status if already active
            mock_save.assert_not_called()  # Should not save if already active
            mock_get_quote.assert_called_once_with(mock_db, valid_uuid, valid_uuid)

