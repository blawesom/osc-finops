"""Session management with database support."""
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta

from backend.config.settings import SESSION_TIMEOUT
from backend.database import SessionLocal
from backend.models.session import Session as SessionModel


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
    """Session manager with database backend."""
    
    def __init__(self):
        # Keep in-memory fallback for backward compatibility
        self._sessions: Dict[str, Session] = {}
        self._use_database = True  # Can be configured
    
    def create_session(self, user_id: str, access_key: str, secret_key: str, region: str) -> Session:
        """
        Create a new session in database.
        
        Args:
            user_id: User ID from database
            access_key: Outscale access key
            secret_key: Outscale secret key (will be stored encrypted)
            region: Selected region
        
        Returns:
            Session object (database-backed)
        """
        if self._use_database:
            db = SessionLocal()
            try:
                db_session = SessionModel(
                    user_id=user_id,
                    access_key=access_key,
                    secret_key=secret_key,  # TODO: Encrypt secret_key
                    region=region
                )
                db.add(db_session)
                db.commit()
                db.refresh(db_session)
                
                # Create Session wrapper for backward compatibility
                session = Session(access_key, secret_key, region)
                session.session_id = db_session.session_id
                session.created_at = db_session.created_at
                session.last_activity = db_session.last_activity
                session.expires_at = db_session.expires_at
                return session
            except Exception as e:
                db.rollback()
                # Fallback to in-memory
                session = Session(access_key, secret_key, region)
                self._sessions[session.session_id] = session
                return session
            finally:
                db.close()
        else:
            # In-memory fallback
            session = Session(access_key, secret_key, region)
            self._sessions[session.session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, checking expiration."""
        if self._use_database:
            db = SessionLocal()
            try:
                db_session = db.query(SessionModel).filter(
                    SessionModel.session_id == session_id
                ).first()
                
                if db_session is None:
                    return None
                
                if db_session.is_expired():
                    self.delete_session(session_id)
                    return None
                
                # Update activity
                db_session.update_activity()
                db.commit()
                
                # Create Session wrapper
                session = Session(
                    db_session.access_key,
                    db_session.secret_key,
                    db_session.region
                )
                session.session_id = db_session.session_id
                session.created_at = db_session.created_at
                session.last_activity = db_session.last_activity
                session.expires_at = db_session.expires_at
                return session
            except Exception:
                # Fallback to in-memory
                pass
            finally:
                db.close()
        
        # In-memory fallback
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
        if self._use_database:
            db = SessionLocal()
            try:
                db_session = db.query(SessionModel).filter(
                    SessionModel.session_id == session_id
                ).first()
                if db_session:
                    db.delete(db_session)
                    db.commit()
                    return True
                return False
            except Exception:
                db.rollback()
                return False
            finally:
                db.close()
        
        # In-memory fallback
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned."""
        if self._use_database:
            db = SessionLocal()
            try:
                expired_sessions = db.query(SessionModel).filter(
                    SessionModel.expires_at < datetime.utcnow()
                ).all()
                count = len(expired_sessions)
                for session in expired_sessions:
                    db.delete(session)
                db.commit()
                return count
            except Exception:
                db.rollback()
                return 0
            finally:
                db.close()
        
        # In-memory fallback
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
        if self._use_database:
            db = SessionLocal()
            try:
                return db.query(SessionModel).filter(
                    SessionModel.expires_at > datetime.utcnow()
                ).count()
            except Exception:
                return len(self._sessions)
            finally:
                db.close()
        
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()

