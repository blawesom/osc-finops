"""Database-backed quote service."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.quote import Quote
from backend.models.quote_item import QuoteItem
from backend.models.quote_group import QuoteGroup
from backend.models.user import User
from backend.services.cost_calculator import calculate_quote_total
from backend.database import SessionLocal
from backend.utils.validators import (
    validate_uuid,
    sanitize_string,
    sanitize_float,
    validate_status,
    validate_discount_percent
)


class QuoteServiceDB:
    """Database-backed quote service."""
    
    @staticmethod
    def create_quote(db: Session, name: str, user_id: str) -> Quote:
        """
        Create a new quote.
        If user has an active quote, it will be saved automatically.
        New quote becomes active.
        """
        # Validate user_id format
        if not validate_uuid(user_id):
            raise ValueError(f"Invalid user_id format: {user_id}")
        
        # Verify user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Sanitize quote name
        name = sanitize_string(name, max_length=255, default="Untitled Quote")
        
        # Save any existing active quote for this user
        QuoteServiceDB._save_active_quote_for_user(db, user_id)
        
        quote = Quote(
            name=name,
            user_id=user_id,
            status="active"
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote
    
    @staticmethod
    def get_quote(db: Session, quote_id: str, user_id: Optional[str] = None) -> Optional[Quote]:
        """
        Get quote by ID.
        If user_id is provided, verify ownership.
        """
        # Validate UUIDs
        if not validate_uuid(quote_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        quote = db.query(Quote).filter(Quote.quote_id == quote_id).first()
        if quote and user_id:
            if quote.user_id != user_id:
                return None
        return quote
    
    @staticmethod
    def get_active_quote(db: Session, user_id: str) -> Optional[Quote]:
        """Get active quote for a user."""
        if not validate_uuid(user_id):
            return None
        
        return db.query(Quote).filter(
            Quote.user_id == user_id,
            Quote.status == "active"
        ).first()
    
    @staticmethod
    def _save_active_quote_for_user(db: Session, user_id: str) -> None:
        """Save the active quote for a user (if exists)."""
        active_quote = QuoteServiceDB.get_active_quote(db, user_id)
        if active_quote:
            active_quote.status = "saved"
            active_quote.updated_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def update_quote(db: Session, quote_id: str, user_id: Optional[str] = None, **kwargs) -> Optional[Quote]:
        """
        Update quote.
        If user_id is provided, verify ownership.
        Handles status transitions (active/saved).
        """
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        # Handle status update with validation
        if "status" in kwargs and kwargs["status"] is not None:
            new_status = kwargs["status"]
            if not validate_status(new_status):
                raise ValueError(f"Invalid status: {new_status}. Must be 'active' or 'saved'")
            
            if new_status == "active" and quote.status == "saved":
                # Loading a saved quote: save current active, make this one active
                if user_id:
                    QuoteServiceDB._save_active_quote_for_user(db, user_id)
                quote.status = "active"
            elif new_status == "saved" and quote.status == "active":
                # Saving an active quote
                quote.status = "saved"
        
        # Update other fields with validation
        if "name" in kwargs and kwargs["name"] is not None:
            quote.name = sanitize_string(kwargs["name"], max_length=255, default="Untitled Quote")
        
        if "duration" in kwargs and kwargs["duration"] is not None:
            duration = sanitize_float(kwargs["duration"], default=1.0, min_value=0.0)
            quote.duration = duration
        
        if "duration_unit" in kwargs and kwargs["duration_unit"] is not None:
            quote.duration_unit = sanitize_string(kwargs["duration_unit"], max_length=20, default="months")
        
        if "commitment_period" in kwargs:
            commitment = kwargs["commitment_period"]
            if commitment is not None:
                quote.commitment_period = sanitize_string(commitment, max_length=20, default=None)
            else:
                quote.commitment_period = None
        
        if "global_discount_percent" in kwargs and kwargs["global_discount_percent"] is not None:
            discount = sanitize_float(kwargs["global_discount_percent"], default=0.0, min_value=0.0, max_value=100.0)
            if not validate_discount_percent(discount):
                raise ValueError(f"Invalid discount percentage: {discount}. Must be between 0 and 100")
            quote.global_discount_percent = discount
        
        quote.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(quote)
        return quote
    
    @staticmethod
    def load_quote(db: Session, quote_id: str, user_id: str) -> Optional[Quote]:
        """
        Load a saved quote (makes it active).
        Previous active quote becomes saved.
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(user_id):
            return None
        
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        if quote.status == "saved":
            # Save current active quote
            QuoteServiceDB._save_active_quote_for_user(db, user_id)
            # Make this quote active
            quote.status = "active"
            quote.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(quote)
        
        return quote
    
    @staticmethod
    def delete_quote(db: Session, quote_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete quote (regardless of status).
        If user_id is provided, verify ownership.
        """
        # Validate UUIDs
        if not validate_uuid(quote_id):
            return False
        
        if user_id and not validate_uuid(user_id):
            return False
        
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return False
        
        db.delete(quote)
        db.commit()
        return True
    
    @staticmethod
    def delete_quote_and_get_replacement(db: Session, quote_id: str, user_id: str) -> Optional[Quote]:
        """
        Delete quote and return replacement quote if available.
        If deleted quote was active, returns next saved quote (if exists) and makes it active.
        If user_id is provided, verify ownership.
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(user_id):
            return None
        
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        was_active = quote.status == "active"
        db.delete(quote)
        db.commit()
        
        if was_active:
            # Find next saved quote (most recently updated)
            next_quote = db.query(Quote).filter(
                Quote.user_id == user_id,
                Quote.status == "saved"
            ).order_by(Quote.updated_at.desc()).first()
            
            if next_quote:
                # Make it active
                next_quote.status = "active"
                next_quote.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(next_quote)
                return next_quote
        
        return None
    
    @staticmethod
    def list_quotes(db: Session, user_id: Optional[str] = None) -> List[Dict]:
        """
        List quotes (summary only).
        If user_id is provided, filter by user_id.
        """
        query = db.query(Quote)
        if user_id:
            # Validate user_id format
            if not validate_uuid(user_id):
                return []
            query = query.filter(Quote.user_id == user_id)
        
        quotes = query.all()
        
        return [
            {
                "quote_id": quote.quote_id,
                "name": quote.name,
                "status": quote.status,
                "item_count": len(quote.items),
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "updated_at": quote.updated_at.isoformat() if quote.updated_at else None
            }
            for quote in quotes
        ]
    
    @staticmethod
    def add_item(db: Session, quote_id: str, item_data: Dict, user_id: Optional[str] = None) -> Optional[Quote]:
        """
        Add item to quote with validation.
        
        Args:
            db: Database session
            quote_id: Quote ID
            item_data: Item data dictionary
            user_id: User ID for ownership verification
        
        Returns:
            Updated Quote or None if quote not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        # Get max display_order
        max_order = db.query(QuoteItem.display_order).filter(
            QuoteItem.quote_id == quote_id
        ).order_by(QuoteItem.display_order.desc()).first()
        next_order = (max_order[0] + 1) if max_order else 0
        
        # Create quote item with validation (from_dict handles all validation)
        try:
            item = QuoteItem.from_dict(item_data, quote_id)
            item.display_order = next_order
            db.add(item)
            quote.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(quote)
            return quote
        except (ValueError, TypeError) as e:
            db.rollback()
            raise ValueError(f"Failed to create quote item: {str(e)}")
    
    @staticmethod
    def remove_item(db: Session, quote_id: str, item_id: str, user_id: Optional[str] = None) -> Optional[Quote]:
        """
        Remove item from quote with validation.
        
        Args:
            db: Database session
            quote_id: Quote ID
            item_id: Item ID to remove
            user_id: User ID for ownership verification
        
        Returns:
            Updated Quote or None if quote/item not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(item_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        item = db.query(QuoteItem).filter(
            QuoteItem.item_id == item_id,
            QuoteItem.quote_id == quote_id
        ).first()
        
        if item:
            db.delete(item)
            quote.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(quote)
        
        return quote
    
    @staticmethod
    def create_group(db: Session, quote_id: str, name: str, user_id: Optional[str] = None) -> Optional[QuoteGroup]:
        """
        Create a new group for a quote.
        
        Args:
            db: Database session
            quote_id: Quote ID
            name: Group name
            user_id: User ID for ownership verification
        
        Returns:
            Created QuoteGroup or None if quote not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        # Get max display_order
        max_order = db.query(QuoteGroup.display_order).filter(
            QuoteGroup.quote_id == quote_id
        ).order_by(QuoteGroup.display_order.desc()).first()
        next_order = (max_order[0] + 1) if max_order else 0
        
        # Create group
        group = QuoteGroup.from_dict({"name": name}, quote_id)
        group.display_order = next_order
        db.add(group)
        quote.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(group)
        return group
    
    @staticmethod
    def update_group(db: Session, quote_id: str, group_id: str, name: str, user_id: Optional[str] = None) -> Optional[QuoteGroup]:
        """
        Update a group's name.
        
        Args:
            db: Database session
            quote_id: Quote ID
            group_id: Group ID
            name: New group name
            user_id: User ID for ownership verification
        
        Returns:
            Updated QuoteGroup or None if not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(group_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        # Get group
        group = db.query(QuoteGroup).filter(
            QuoteGroup.group_id == group_id,
            QuoteGroup.quote_id == quote_id
        ).first()
        
        if group:
            group.name = sanitize_string(name, max_length=255, default="New Group")
            quote.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(group)
        
        return group
    
    @staticmethod
    def delete_group(db: Session, quote_id: str, group_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a group. Items in the group will have their group_id set to NULL.
        
        Args:
            db: Database session
            quote_id: Quote ID
            group_id: Group ID
            user_id: User ID for ownership verification
        
        Returns:
            True if deleted, False if not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(group_id):
            return False
        
        if user_id and not validate_uuid(user_id):
            return False
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return False
        
        # Get group
        group = db.query(QuoteGroup).filter(
            QuoteGroup.group_id == group_id,
            QuoteGroup.quote_id == quote_id
        ).first()
        
        if group:
            # Set all items in this group to NULL (ungrouped)
            db.query(QuoteItem).filter(
                QuoteItem.group_id == group_id
            ).update({QuoteItem.group_id: None})
            
            # Delete group
            db.delete(group)
            quote.updated_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def assign_item_to_group(db: Session, quote_id: str, item_id: str, group_id: Optional[str], user_id: Optional[str] = None) -> Optional[Quote]:
        """
        Assign an item to a group (or ungroup if group_id is None).
        
        Args:
            db: Database session
            quote_id: Quote ID
            item_id: Item ID
            group_id: Group ID (None to ungroup)
            user_id: User ID for ownership verification
        
        Returns:
            Updated Quote or None if not found
        """
        # Validate UUIDs
        if not validate_uuid(quote_id) or not validate_uuid(item_id):
            return None
        
        if user_id and not validate_uuid(user_id):
            return None
        
        if group_id and not validate_uuid(group_id):
            return None
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return None
        
        # Get item
        item = db.query(QuoteItem).filter(
            QuoteItem.item_id == item_id,
            QuoteItem.quote_id == quote_id
        ).first()
        
        if not item:
            return None
        
        # If group_id provided, verify group exists and belongs to quote
        if group_id:
            group = db.query(QuoteGroup).filter(
                QuoteGroup.group_id == group_id,
                QuoteGroup.quote_id == quote_id
            ).first()
            if not group:
                return None
        
        # Assign item to group (or ungroup)
        item.group_id = group_id
        quote.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(quote)
        return quote
    
    @staticmethod
    def get_groups(db: Session, quote_id: str, user_id: Optional[str] = None) -> List[Dict]:
        """
        Get all groups for a quote.
        
        Args:
            db: Database session
            quote_id: Quote ID
            user_id: User ID for ownership verification
        
        Returns:
            List of group dictionaries
        """
        # Validate UUIDs
        if not validate_uuid(quote_id):
            return []
        
        if user_id and not validate_uuid(user_id):
            return []
        
        # Verify quote exists and user owns it
        quote = QuoteServiceDB.get_quote(db, quote_id, user_id)
        if not quote:
            return []
        
        groups = db.query(QuoteGroup).filter(
            QuoteGroup.quote_id == quote_id
        ).order_by(QuoteGroup.display_order).all()
        
        return [group.to_dict() for group in groups]

