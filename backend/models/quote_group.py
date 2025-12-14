"""QuoteGroup model for database."""
from sqlalchemy import Column, String, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel
from backend.utils.validators import sanitize_string, validate_uuid


class QuoteGroup(BaseModel):
    """QuoteGroup model for organizing quote items."""
    __tablename__ = "quote_groups"
    
    group_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(UUID(as_uuid=False), ForeignKey("quotes.quote_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    quote = relationship("Quote", back_populates="groups")
    items = relationship("QuoteItem", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(name) > 0", name="check_name_not_empty"),
        {"sqlite_autoincrement": True}
    )
    
    def __repr__(self):
        return f"<QuoteGroup(group_id={self.group_id}, name={self.name}, quote_id={self.quote_id})>"
    
    def to_dict(self):
        """Convert quote group to dictionary."""
        return {
            "group_id": self.group_id,
            "quote_id": self.quote_id,
            "name": self.name,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, group_dict, quote_id):
        """
        Create QuoteGroup from dictionary with validation and sanitization.
        
        Args:
            group_dict: Dictionary with group data
            quote_id: Parent quote ID
        
        Returns:
            QuoteGroup instance
        """
        # Validate and sanitize group_id
        group_id = group_dict.get("group_id")
        if not group_id or not validate_uuid(group_id):
            group_id = str(uuid.uuid4())
        
        # Validate quote_id
        if not validate_uuid(quote_id):
            raise ValueError(f"Invalid quote_id format: {quote_id}")
        
        # Sanitize name
        name = sanitize_string(
            group_dict.get("name"),
            max_length=255,
            default="New Group"
        )
        
        # Sanitize display_order
        display_order = int(group_dict.get("display_order", 0))
        if display_order < 0:
            display_order = 0
        
        # Create group
        group = cls(
            group_id=group_id,
            quote_id=quote_id,
            name=name,
            display_order=display_order
        )
        
        return group

