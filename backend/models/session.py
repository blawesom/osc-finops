"""Session model for database."""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel
from backend.config.settings import SESSION_TIMEOUT


class Session(BaseModel):
    """Session model for user authentication."""
    __tablename__ = "sessions"
    
    session_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False, index=True)
    access_key = Column(String(255), nullable=False)  # Cached for quick lookups
    secret_key = Column(String(500), nullable=False)  # Encrypted secret key
    region = Column(String(50), nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    def __init__(self, *args, **kwargs):
        """Initialize session with expiration time."""
        super().__init__(*args, **kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT)
    
    def update_activity(self):
        """Update last activity time and extend expiration."""
        self.last_activity = datetime.utcnow()
        self.expires_at = self.last_activity + timedelta(seconds=SESSION_TIMEOUT)
        self.updated_at = datetime.utcnow()
    
    def is_expired(self):
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """Convert session to dictionary (excluding sensitive data)."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "region": self.region,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id})>"

