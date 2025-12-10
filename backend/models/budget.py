"""Budget model for database."""
from sqlalchemy import Column, String, Float, ForeignKey, Date, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel


class Budget(BaseModel):
    """Budget model for cost management."""
    __tablename__ = "budgets"
    
    budget_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Optional, for fixed duration budgets
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("period_type IN ('monthly', 'quarterly', 'yearly')", name="check_period_type"),
        CheckConstraint("amount > 0", name="check_amount_positive"),
        {"sqlite_autoincrement": True}
    )
    
    def __repr__(self):
        return f"<Budget(budget_id={self.budget_id}, name={self.name}, amount={self.amount}, period_type={self.period_type})>"
    
    def to_dict(self):
        """Convert budget to dictionary."""
        return {
            "budget_id": self.budget_id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

