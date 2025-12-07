"""Unit tests for backend.middleware.auth_middleware."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request

from backend.middleware.auth_middleware import require_auth


class TestRequireAuth:
    """Tests for require_auth decorator."""
    
    def test_require_auth_missing_session_id(self):
        """Test require_auth returns error when session_id is missing."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"status": "ok"}
        
        with app.test_client() as client:
            response = client.get('/test')
            
            assert response.status_code == 401
            data = response.get_json()
            # error_response returns {"error": {"code": ..., "message": ...}}
            assert "error" in data
            assert "code" in data["error"] or "message" in data["error"]
    
    def test_require_auth_invalid_session(self):
        """Test require_auth returns error when session is invalid."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"status": "ok"}
        
        with patch('backend.middleware.auth_middleware.session_manager') as mock_manager:
            mock_manager.get_session.return_value = None
            
            with app.test_client() as client:
                response = client.get('/test', headers={"X-Session-ID": "invalid-session"})
                
                assert response.status_code == 401
                data = response.get_json()
                # error_response returns {"error": {"code": ..., "message": ...}}
                assert "error" in data
                assert "code" in data["error"] or "message" in data["error"]
    
    def test_require_auth_valid_session_header(self):
        """Test require_auth allows access with valid session in header."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"status": "ok", "session_id": request.session.session_id}
        
        mock_session = Mock()
        mock_session.session_id = "valid-session-123"
        mock_session.region = "eu-west-2"
        
        with patch('backend.middleware.auth_middleware.session_manager') as mock_manager:
            mock_manager.get_session.return_value = mock_session
            
            with patch('backend.database.SessionLocal') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db_session = Mock()
                mock_db_session.user_id = "user-123"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_db_session
                
                with app.test_client() as client:
                    response = client.get('/test', headers={"X-Session-ID": "valid-session-123"})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data["status"] == "ok"
                    assert data["session_id"] == "valid-session-123"
    
    def test_require_auth_valid_session_query_param(self):
        """Test require_auth allows access with valid session in query param."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"status": "ok"}
        
        mock_session = Mock()
        mock_session.session_id = "valid-session-123"
        mock_session.region = "eu-west-2"
        
        with patch('backend.middleware.auth_middleware.session_manager') as mock_manager:
            mock_manager.get_session.return_value = mock_session
            
            with patch('backend.database.SessionLocal') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db_session = Mock()
                mock_db_session.user_id = "user-123"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_db_session
                
                with app.test_client() as client:
                    response = client.get('/test?session_id=valid-session-123')
                    
                    assert response.status_code == 200
    
    def test_require_auth_sets_user_id(self):
        """Test require_auth sets user_id from database session."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"user_id": getattr(request.session, 'user_id', None)}
        
        mock_session = Mock()
        mock_session.session_id = "valid-session-123"
        mock_session.region = "eu-west-2"
        
        with patch('backend.middleware.auth_middleware.session_manager') as mock_manager:
            mock_manager.get_session.return_value = mock_session
            
            with patch('backend.database.SessionLocal') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db_session = Mock()
                mock_db_session.user_id = "user-123"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_db_session
                
                with app.test_client() as client:
                    response = client.get('/test', headers={"X-Session-ID": "valid-session-123"})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data["user_id"] == "user-123"
    
    def test_require_auth_handles_db_error(self):
        """Test require_auth handles database errors gracefully."""
        app = Flask(__name__)
        
        @app.route('/test')
        @require_auth
        def test_route():
            return {"status": "ok"}
        
        mock_session = Mock()
        mock_session.session_id = "valid-session-123"
        mock_session.region = "eu-west-2"
        
        with patch('backend.middleware.auth_middleware.session_manager') as mock_manager:
            mock_manager.get_session.return_value = mock_session
            
            with patch('backend.database.SessionLocal') as mock_db_class:
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db.query.side_effect = Exception("Database error")
                
                with app.test_client() as client:
                    # Should still work even if DB query fails
                    response = client.get('/test', headers={"X-Session-ID": "valid-session-123"})
                    
                    assert response.status_code == 200

