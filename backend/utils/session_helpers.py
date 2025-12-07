"""Session helper utilities for extracting user information from request context."""
from flask import request
from backend.database import SessionLocal
from backend.models.user import User


def get_user_id_from_session():
    """
    Get user_id from session.
    
    Returns:
        str: User ID (UUID) or None if not found
    """
    session = getattr(request, 'session', None)
    if not session:
        return None
    
    # Get user_id from session
    if hasattr(session, 'user_id') and session.user_id:
        return session.user_id
    
    return None


def get_account_id_from_session():
    """
    Get account_id from session by looking up user.
    
    Returns:
        str: Account ID or None if not found
    """
    session = getattr(request, 'session', None)
    if not session:
        return None
    
    # Get account_id from user_id in session
    db = SessionLocal()
    try:
        if hasattr(session, 'user_id') and session.user_id:
            user = db.query(User).filter(User.user_id == session.user_id).first()
            if user:
                return user.account_id
    except Exception:
        pass
    finally:
        db.close()
    
    return None

