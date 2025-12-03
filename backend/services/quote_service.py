"""Quote service for managing quotes (database-backed)."""
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from backend.services.cost_calculator import calculate_quote_total
from backend.services.quote_service_db import QuoteServiceDB
from backend.database import SessionLocal


class Quote:
    """Quote data structure."""
    
    def __init__(self, name: str = "Untitled Quote", owner: Optional[str] = None):
        self.quote_id: str = str(uuid.uuid4())
        self.name: str = name
        self.status: str = "active"  # "active" or "saved"
        self.owner: str = owner or ""  # User identifier (access_key or session_id)
        self.items: List[Dict] = []
        self.duration: float = 1.0
        self.duration_unit: str = "months"
        self.commitment_period: Optional[str] = None
        self.global_discount_percent: float = 0.0
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
    
    def add_item(self, item: Dict) -> None:
        """Add item to quote."""
        self.items.append(item)
        self.updated_at = datetime.utcnow()
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from quote by ID."""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.get("id") != item_id]
        if len(self.items) < original_count:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def update_config(self, duration: Optional[float] = None, duration_unit: Optional[str] = None,
                     commitment_period: Optional[str] = None, global_discount_percent: Optional[float] = None) -> None:
        """Update quote configuration."""
        if duration is not None:
            self.duration = duration
        if duration_unit is not None:
            self.duration_unit = duration_unit
        if commitment_period is not None:
            self.commitment_period = commitment_period
        if global_discount_percent is not None:
            self.global_discount_percent = global_discount_percent
        self.updated_at = datetime.utcnow()
    
    def calculate(self) -> Dict:
        """Calculate quote totals."""
        return calculate_quote_total(
            self.items,
            self.duration,
            self.duration_unit,
            self.commitment_period,
            self.global_discount_percent
        )
    
    def to_dict(self) -> Dict:
        """Convert quote to dictionary."""
        calculation = self.calculate()
        return {
            "quote_id": self.quote_id,
            "name": self.name,
            "status": self.status,
            "owner": self.owner,
            "items": self.items,
            "duration": self.duration,
            "duration_unit": self.duration_unit,
            "commitment_period": self.commitment_period,
            "global_discount_percent": self.global_discount_percent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "calculation": calculation
        }


class QuoteManager:
    """Database-backed quote manager with user-scoped quotes and lifecycle management."""
    
    def __init__(self):
        # Keep for backward compatibility, but use database
        pass
    
    def create_quote(self, name: str = "Untitled Quote", owner: Optional[str] = None) -> 'Quote':
        """
        Create a new quote.
        If user has an active quote, it will be saved automatically.
        New quote becomes active.
        """
        if not owner:
            raise ValueError("Owner (user_id) is required")
        
        db = SessionLocal()
        try:
            db_quote = QuoteServiceDB.create_quote(db, name, owner)
            # Convert to Quote object for backward compatibility
            quote = Quote(name, owner=owner)
            quote.quote_id = db_quote.quote_id
            quote.status = db_quote.status
            quote.created_at = db_quote.created_at
            quote.updated_at = db_quote.updated_at
            quote.duration = db_quote.duration
            quote.duration_unit = db_quote.duration_unit
            quote.commitment_period = db_quote.commitment_period
            quote.global_discount_percent = db_quote.global_discount_percent
            # Load items
            quote.items = [item.to_dict() for item in db_quote.items]
            return quote
        except ValueError as e:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create quote: {str(e)}")
        finally:
            db.close()
    
    def get_quote(self, quote_id: str, owner: Optional[str] = None) -> Optional['Quote']:
        """
        Get quote by ID.
        If owner is provided, verify ownership.
        """
        db = SessionLocal()
        try:
            db_quote = QuoteServiceDB.get_quote(db, quote_id, owner)
            if not db_quote:
                return None
            
            # Convert to Quote object
            quote = Quote(db_quote.name, owner=db_quote.user_id)
            quote.quote_id = db_quote.quote_id
            quote.status = db_quote.status
            quote.created_at = db_quote.created_at
            quote.updated_at = db_quote.updated_at
            quote.duration = db_quote.duration
            quote.duration_unit = db_quote.duration_unit
            quote.commitment_period = db_quote.commitment_period
            quote.global_discount_percent = db_quote.global_discount_percent
            quote.items = [item.to_dict() for item in db_quote.items]
            return quote
        finally:
            db.close()
    
    def get_active_quote(self, owner: str) -> Optional['Quote']:
        """Get active quote for a user."""
        db = SessionLocal()
        try:
            db_quote = QuoteServiceDB.get_active_quote(db, owner)
            if not db_quote:
                return None
            
            quote = Quote(db_quote.name, owner=db_quote.user_id)
            quote.quote_id = db_quote.quote_id
            quote.status = db_quote.status
            quote.created_at = db_quote.created_at
            quote.updated_at = db_quote.updated_at
            quote.duration = db_quote.duration
            quote.duration_unit = db_quote.duration_unit
            quote.commitment_period = db_quote.commitment_period
            quote.global_discount_percent = db_quote.global_discount_percent
            quote.items = [item.to_dict() for item in db_quote.items]
            return quote
        finally:
            db.close()
    
    def _save_active_quote_for_owner(self, owner: str) -> None:
        """Save the active quote for an owner (if exists)."""
        db = SessionLocal()
        try:
            QuoteServiceDB._save_active_quote_for_user(db, owner)
        finally:
            db.close()
    
    def update_quote(self, quote_id: str, owner: Optional[str] = None, **kwargs) -> Optional['Quote']:
        """
        Update quote.
        If owner is provided, verify ownership.
        Handles status transitions (active/saved).
        """
        db = SessionLocal()
        try:
            db_quote = QuoteServiceDB.update_quote(db, quote_id, owner, **kwargs)
            if not db_quote:
                return None
            
            quote = Quote(db_quote.name, owner=db_quote.user_id)
            quote.quote_id = db_quote.quote_id
            quote.status = db_quote.status
            quote.created_at = db_quote.created_at
            quote.updated_at = db_quote.updated_at
            quote.duration = db_quote.duration
            quote.duration_unit = db_quote.duration_unit
            quote.commitment_period = db_quote.commitment_period
            quote.global_discount_percent = db_quote.global_discount_percent
            quote.items = [item.to_dict() for item in db_quote.items]
            return quote
        finally:
            db.close()
    
    def load_quote(self, quote_id: str, owner: str) -> Optional['Quote']:
        """
        Load a saved quote (makes it active).
        Previous active quote becomes saved.
        """
        db = SessionLocal()
        try:
            db_quote = QuoteServiceDB.load_quote(db, quote_id, owner)
            if not db_quote:
                return None
            
            quote = Quote(db_quote.name, owner=db_quote.user_id)
            quote.quote_id = db_quote.quote_id
            quote.status = db_quote.status
            quote.created_at = db_quote.created_at
            quote.updated_at = db_quote.updated_at
            quote.duration = db_quote.duration
            quote.duration_unit = db_quote.duration_unit
            quote.commitment_period = db_quote.commitment_period
            quote.global_discount_percent = db_quote.global_discount_percent
            quote.items = [item.to_dict() for item in db_quote.items]
            return quote
        finally:
            db.close()
    
    def delete_quote(self, quote_id: str, owner: Optional[str] = None) -> bool:
        """
        Delete quote.
        Only allows deletion of saved quotes (not active).
        If owner is provided, verify ownership.
        """
        db = SessionLocal()
        try:
            return QuoteServiceDB.delete_quote(db, quote_id, owner)
        finally:
            db.close()
    
    def list_quotes(self, owner: Optional[str] = None) -> List[Dict]:
        """
        List quotes (summary only).
        If owner is provided, filter by owner.
        """
        db = SessionLocal()
        try:
            return QuoteServiceDB.list_quotes(db, owner)
        finally:
            db.close()


# Global quote manager instance
quote_manager = QuoteManager()

