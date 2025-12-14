"""Quote model for database."""
from sqlalchemy import Column, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel


class Quote(BaseModel):
    """Quote model for cost estimates."""
    __tablename__ = "quotes"
    
    quote_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="active", index=True)
    duration = Column(Float, nullable=False, default=1.0)
    duration_unit = Column(String(20), nullable=False, default="months")
    commitment_period = Column(String(20), nullable=True)
    global_discount_percent = Column(Float, nullable=False, default=0.0)
    
    # Relationships
    user = relationship("User", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.display_order")
    groups = relationship("QuoteGroup", back_populates="quote", cascade="all, delete-orphan", order_by="QuoteGroup.display_order")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'saved')", name="check_status"),
        CheckConstraint("global_discount_percent >= 0 AND global_discount_percent <= 100", name="check_discount"),
        {"sqlite_autoincrement": True}
    )
    
    def __repr__(self):
        return f"<Quote(quote_id={self.quote_id}, name={self.name}, status={self.status})>"
    
    def to_dict(self):
        """Convert quote to dictionary with calculation."""
        from backend.services.cost_calculator import calculate_quote_total
        
        # Convert items to dict format for calculation
        items_dict = [item.to_dict() for item in self.items]
        
        # Convert groups to dict format
        groups_dict = [group.to_dict() for group in self.groups]
        
        # Calculate totals
        calculation = calculate_quote_total(
            items_dict,
            self.duration,
            self.duration_unit,
            self.commitment_period,
            self.global_discount_percent
        )
        
        return {
            "quote_id": self.quote_id,
            "name": self.name,
            "status": self.status,
            "user_id": self.user_id,
            "items": items_dict,
            "groups": groups_dict,
            "duration": self.duration,
            "duration_unit": self.duration_unit,
            "commitment_period": self.commitment_period,
            "global_discount_percent": self.global_discount_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "calculation": calculation
        }

