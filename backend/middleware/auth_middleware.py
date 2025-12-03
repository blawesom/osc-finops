"""Authentication middleware for protecting routes."""
from functools import wraps
from flask import request
from backend.auth.session_manager import session_manager
from backend.utils.errors import error_response


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from backend.database import SessionLocal
        from backend.models.session import Session as SessionModel
        
        session_id = request.headers.get("X-Session-ID") or request.args.get("session_id")
        
        if not session_id:
            return error_response("MISSING_SESSION", "Authentication required", 401)
        
        session = session_manager.get_session(session_id)
        if not session:
            return error_response("INVALID_SESSION", "Session not found or expired", 401)
        
        # Get user_id from database session if available
        db = SessionLocal()
        try:
            db_session = db.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()
            if db_session:
                session.user_id = db_session.user_id
        except Exception:
            pass
        finally:
            db.close()
        
        # Add session to request context for use in route handlers
        request.session = session
        
        return f(*args, **kwargs)
    
    return decorated_function

