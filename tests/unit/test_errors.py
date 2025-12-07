"""Unit tests for backend.utils.errors."""
import pytest
from flask import Flask, jsonify
from backend.utils.errors import APIError, error_response, success_response


class TestAPIError:
    """Tests for APIError exception class."""
    
    def test_init_with_message(self):
        """Test APIError initialization with message only."""
        error = APIError("Test error")
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.code == "API_ERROR"
        assert str(error) == "Test error"
    
    def test_init_with_status_code(self):
        """Test APIError initialization with custom status code."""
        error = APIError("Not found", status_code=404)
        assert error.message == "Not found"
        assert error.status_code == 404
        assert error.code == "API_ERROR"
    
    def test_init_with_custom_code(self):
        """Test APIError initialization with custom code."""
        error = APIError("Invalid input", code="INVALID_INPUT")
        assert error.message == "Invalid input"
        assert error.code == "INVALID_INPUT"
    
    def test_init_with_all_params(self):
        """Test APIError initialization with all parameters."""
        error = APIError("Unauthorized", status_code=401, code="UNAUTHORIZED")
        assert error.message == "Unauthorized"
        assert error.status_code == 401
        assert error.code == "UNAUTHORIZED"
    
    def test_to_dict(self):
        """Test converting error to dictionary."""
        error = APIError("Test error", status_code=400, code="TEST_ERROR")
        error_dict = error.to_dict()
        
        assert "error" in error_dict
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Test error"
    
    def test_inheritance(self):
        """Test that APIError inherits from Exception."""
        error = APIError("Test")
        assert isinstance(error, Exception)


class TestErrorResponse:
    """Tests for error_response function."""
    
    def test_basic_error_response(self):
        """Test basic error response creation."""
        app = Flask(__name__)
        with app.app_context():
            response, status_code = error_response("TEST_ERROR", "Test error message")
            
            assert status_code == 400
            # Flask jsonify always returns 200, status_code is in the tuple
            data = response.get_json()
            assert "error" in data
            assert data["error"]["code"] == "TEST_ERROR"
            assert data["error"]["message"] == "Test error message"
    
    def test_error_response_with_custom_status(self):
        """Test error response with custom status code."""
        app = Flask(__name__)
        with app.app_context():
            response, status_code = error_response("NOT_FOUND", "Resource not found", 404)
            
            assert status_code == 404
            # Flask jsonify always returns 200, status_code is in the tuple
            data = response.get_json()
            assert data["error"]["code"] == "NOT_FOUND"
            assert data["error"]["message"] == "Resource not found"
    
    def test_error_response_with_details(self):
        """Test error response with additional details."""
        app = Flask(__name__)
        with app.app_context():
            details = {"field": "email", "reason": "invalid format"}
            response, status_code = error_response(
                "VALIDATION_ERROR",
                "Validation failed",
                400,
                details=details
            )
            
            data = response.get_json()
            assert data["error"]["code"] == "VALIDATION_ERROR"
            assert "details" in data["error"]
            assert data["error"]["details"] == details
    
    def test_error_response_with_empty_details(self):
        """Test error response with empty details dict (not added if empty)."""
        app = Flask(__name__)
        with app.app_context():
            response, status_code = error_response("ERROR", "Message", details={})
            data = response.get_json()
            # Empty dict is falsy, so details won't be added
            assert "details" not in data["error"]
    
    def test_error_response_different_status_codes(self):
        """Test error response with various status codes."""
        app = Flask(__name__)
        with app.app_context():
            # 401 Unauthorized
            response, status = error_response("UNAUTHORIZED", "Unauthorized", 401)
            assert status == 401
            data = response.get_json()
            assert data["error"]["code"] == "UNAUTHORIZED"
            
            # 403 Forbidden
            response, status = error_response("FORBIDDEN", "Forbidden", 403)
            assert status == 403
            
            # 500 Internal Server Error
            response, status = error_response("INTERNAL_ERROR", "Internal error", 500)
            assert status == 500


class TestSuccessResponse:
    """Tests for success_response function."""
    
    def test_basic_success_response(self):
        """Test basic success response creation."""
        app = Flask(__name__)
        with app.app_context():
            data = {"id": 1, "name": "Test"}
            response, status_code = success_response(data)
            
            assert status_code == 200
            assert response.status_code == 200
            response_data = response.get_json()
            assert "data" in response_data
            assert response_data["data"] == data
    
    def test_success_response_with_custom_status(self):
        """Test success response with custom status code."""
        app = Flask(__name__)
        with app.app_context():
            data = {"id": 2}
            response, status_code = success_response(data, status_code=201)
            
            assert status_code == 201
            # Flask jsonify always returns 200, status_code is in the tuple
            response_data = response.get_json()
            assert response_data["data"] == data
    
    def test_success_response_with_metadata(self):
        """Test success response with metadata."""
        app = Flask(__name__)
        with app.app_context():
            data = {"items": [1, 2, 3]}
            metadata = {"total": 3, "page": 1}
            response, status_code = success_response(data, metadata=metadata)
            
            response_data = response.get_json()
            assert response_data["data"] == data
            assert "metadata" in response_data
            assert response_data["metadata"] == metadata
    
    def test_success_response_with_empty_metadata(self):
        """Test success response with empty metadata (not added if empty)."""
        app = Flask(__name__)
        with app.app_context():
            data = {"result": "ok"}
            response, status_code = success_response(data, metadata={})
            
            response_data = response.get_json()
            assert response_data["data"] == data
            # Empty dict is falsy, so metadata won't be added
            assert "metadata" not in response_data
    
    def test_success_response_with_none_data(self):
        """Test success response with None data."""
        app = Flask(__name__)
        with app.app_context():
            response, status_code = success_response(None)
            
            response_data = response.get_json()
            assert response_data["data"] is None
    
    def test_success_response_with_list_data(self):
        """Test success response with list data."""
        app = Flask(__name__)
        with app.app_context():
            data = [1, 2, 3, 4, 5]
            response, status_code = success_response(data)
            
            response_data = response.get_json()
            assert response_data["data"] == data
    
    def test_success_response_with_complex_data(self):
        """Test success response with complex nested data."""
        app = Flask(__name__)
        with app.app_context():
            data = {
                "user": {
                    "id": 1,
                    "name": "Test User",
                    "roles": ["admin", "user"]
                },
                "settings": {
                    "theme": "dark",
                    "notifications": True
                }
            }
            response, status_code = success_response(data)
            
            response_data = response.get_json()
            assert response_data["data"] == data
    
    def test_success_response_different_status_codes(self):
        """Test success response with various status codes."""
        app = Flask(__name__)
        with app.app_context():
            # 201 Created
            response, status = success_response({"id": 1}, status_code=201)
            assert status == 201
            data = response.get_json()
            assert data["data"]["id"] == 1
            
            # 202 Accepted
            response, status = success_response({"job_id": "123"}, status_code=202)
            assert status == 202
            
            # 204 No Content (though data would typically be None)
            response, status = success_response(None, status_code=204)
            assert status == 204

