"""User model for database."""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel


class User(BaseModel):
    """User model representing an Outscale account."""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(255), unique=True, nullable=False, index=True)
    access_key = Column(String(255), nullable=False, index=True)  # Non-unique, multiple keys per account
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, account_id={self.account_id})>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "is_active": self.is_active
        }

