"""User service for managing users in database."""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.user import User


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    def get_user_by_account_id(db: Session, account_id: str) -> Optional[User]:
        """Get user by account_id."""
        return db.query(User).filter(User.account_id == account_id).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by user_id."""
        return db.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    def get_user_by_access_key(db: Session, access_key: str) -> Optional[User]:
        """Get user by access_key (returns first match, as multiple keys can exist per account)."""
        return db.query(User).filter(User.access_key == access_key).first()
    
    @staticmethod
    def create_or_update_user(db: Session, account_id: str, access_key: str) -> User:
        """
        Create user if not exists, or update access_key if user exists.
        Returns the user instance.
        """
        user = UserService.get_user_by_account_id(db, account_id)
        
        if user:
            # Update access_key and last_login_at
            user.access_key = access_key
            user.last_login_at = datetime.utcnow()
            user.is_active = True
        else:
            # Create new user
            user = User(
                account_id=account_id,
                access_key=access_key,
                last_login_at=datetime.utcnow()
            )
            db.add(user)
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            # If account_id conflict, try to get existing user
            user = UserService.get_user_by_account_id(db, account_id)
            if user:
                user.access_key = access_key
                user.last_login_at = datetime.utcnow()
                db.commit()
                db.refresh(user)
                return user
            raise
    
    @staticmethod
    def update_last_login(db: Session, user_id: str):
        """Update user's last login timestamp."""
        user = UserService.get_user_by_id(db, user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            db.commit()


# Global service instance (for backward compatibility)
def get_user_service():
    """Get user service instance."""
    return UserService()

