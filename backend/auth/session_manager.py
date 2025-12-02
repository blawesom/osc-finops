"""In-memory session management."""
import uuid
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from backend.config.settings import SESSION_TIMEOUT


class Session:
    """Session data structure."""
    
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.session_id: str = str(uuid.uuid4())
        self.access_key: str = access_key
        self.secret_key: str = secret_key
        self.region: str = region
        self.created_at: datetime = datetime.utcnow()
        self.last_activity: datetime = datetime.utcnow()
        self.expires_at: datetime = self.created_at + timedelta(seconds=SESSION_TIMEOUT)
    
    def update_activity(self) -> None:
        """Update last activity time and extend expiration."""
        self.last_activity = datetime.utcnow()
        self.expires_at = self.last_activity + timedelta(seconds=SESSION_TIMEOUT)
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary (excluding sensitive data)."""
        return {
            "session_id": self.session_id,
            "region": self.region,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class SessionManager:
    """In-memory session manager."""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def create_session(self, access_key: str, secret_key: str, region: str) -> Session:
        """Create a new session."""
        session = Session(access_key, secret_key, region)
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, checking expiration."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        
        if session.is_expired():
            self.delete_session(session_id)
            return None
        
        session.update_activity()
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned."""
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired()
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
        return len(expired_ids)
    
    def get_session_count(self) -> int:
        """Get current number of active sessions."""
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()

