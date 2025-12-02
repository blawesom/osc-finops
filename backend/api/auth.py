"""Authentication API endpoints."""
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError, validate

from backend.auth.session_manager import session_manager
from backend.auth.validator import validate_credentials, validate_region
from backend.utils.errors import error_response, success_response


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


class LoginSchema(Schema):
    """Schema for login request."""
    access_key = fields.Str(required=True, validate=validate.Length(min=1))
    secret_key = fields.Str(required=True, validate=validate.Length(min=1))
    region = fields.Str(required=True, validate=validate.Length(min=1))


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login endpoint - validate credentials and create session."""
    try:
        # Validate request schema
        schema = LoginSchema()
        data = schema.load(request.json)
        
        access_key = data["access_key"]
        secret_key = data["secret_key"]
        region = data["region"]
        
        # Validate region
        is_valid_region, region_error = validate_region(region)
        if not is_valid_region:
            return error_response("INVALID_REGION", region_error, 400)
        
        # Validate credentials
        is_valid, error_msg = validate_credentials(access_key, secret_key, region)
        if not is_valid:
            return error_response("INVALID_CREDENTIALS", error_msg, 401)
        
        # Create session
        session = session_manager.create_session(access_key, secret_key, region)
        
        # Return session info (without sensitive data)
        return success_response({
            "session_id": session.session_id,
            "region": session.region,
            "expires_at": session.expires_at.isoformat()
        }, 200)
    
    except ValidationError as e:
        return error_response("VALIDATION_ERROR", "Invalid request data", 400, {"fields": e.messages})
    except Exception as e:
        # Log error (without sensitive data)
        return error_response("INTERNAL_ERROR", "An error occurred during login", 500)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout endpoint - delete session."""
    session_id = request.headers.get("X-Session-ID") or request.json.get("session_id") if request.json else None
    
    if not session_id:
        return error_response("MISSING_SESSION", "Session ID is required", 400)
    
    deleted = session_manager.delete_session(session_id)
    
    if deleted:
        return success_response({"message": "Logged out successfully"}, 200)
    else:
        return error_response("INVALID_SESSION", "Session not found", 404)


@auth_bp.route("/session", methods=["GET"])
def get_session():
    """Get session status."""
    session_id = request.headers.get("X-Session-ID") or request.args.get("session_id")
    
    if not session_id:
        return error_response("MISSING_SESSION", "Session ID is required", 400)
    
    session = session_manager.get_session(session_id)
    
    if session:
        return success_response(session.to_dict(), 200)
    else:
        return error_response("INVALID_SESSION", "Session not found or expired", 401)

