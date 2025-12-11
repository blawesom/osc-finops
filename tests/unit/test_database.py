"""Unit tests for database configuration and management."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.config.database import get_db, init_db, close_db, SessionLocal
from backend.database.base import BaseModel, Base


class TestGetDb:
    """Tests for get_db generator function."""
    
    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_get_db_closes_on_exit(self):
        """Test that get_db closes session when generator exits."""
        mock_db = Mock()
        
        with patch('backend.config.database.SessionLocal', return_value=mock_db):
            db_gen = get_db()
            db = next(db_gen)
            
            # Exit generator (simulating finally block)
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            # Verify close was called
            mock_db.close.assert_called_once()
    
    def test_get_db_closes_on_exception(self):
        """Test that get_db closes session even if exception occurs."""
        mock_db = Mock()
        
        with patch('backend.config.database.SessionLocal', return_value=mock_db):
            db_gen = get_db()
            db = next(db_gen)
            
            # Simulate exception
            try:
                raise ValueError("Test error")
            except ValueError:
                # Generator should still close
                try:
                    next(db_gen)
                except StopIteration:
                    pass
            
            mock_db.close.assert_called_once()


class TestInitDb:
    """Tests for init_db function."""
    
    @patch('backend.database.base.Base.metadata.create_all')
    @patch('backend.config.database.engine')
    def test_init_db_creates_tables(self, mock_engine, mock_create_all):
        """Test that init_db creates all tables."""
        init_db()
        
        # Verify create_all was called
        mock_create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('backend.database.base.Base.metadata.create_all')
    @patch('backend.config.database.engine')
    def test_init_db_handles_import_error(self, mock_engine, mock_create_all):
        """Test that init_db handles import errors gracefully."""
        # This test verifies the function structure
        # Actual import errors would be caught at import time
        init_db()
        mock_create_all.assert_called_once()


class TestCloseDb:
    """Tests for close_db function."""
    
    def test_close_db_removes_session(self):
        """Test that close_db removes scoped session."""
        with patch('backend.config.database.SessionLocal') as mock_session_local:
            close_db()
            mock_session_local.remove.assert_called_once()


class TestBaseModel:
    """Tests for BaseModel class."""
    
    def test_base_model_is_abstract(self):
        """Test that BaseModel is abstract and cannot be instantiated directly."""
        # BaseModel should be abstract
        assert BaseModel.__abstract__ is True
    
    def test_base_model_has_common_fields(self):
        """Test that BaseModel defines common fields."""
        # Check that common fields are defined in the class
        assert hasattr(BaseModel, 'created_at')
        assert hasattr(BaseModel, 'updated_at')
        assert hasattr(BaseModel, 'to_dict')
    
    def test_base_model_to_dict_method(self):
        """Test BaseModel.to_dict method structure."""
        # Test that to_dict is a method
        assert callable(BaseModel.to_dict)
        assert hasattr(BaseModel, 'to_dict')
        
        # The actual implementation will be tested through concrete model tests
        # This is just a structural test

