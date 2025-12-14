"""QuoteItem model for database."""
import json
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import BaseModel
from backend.utils.validators import sanitize_string, sanitize_float, sanitize_json, validate_uuid


class QuoteItem(BaseModel):
    """QuoteItem model for individual items in a quote."""
    __tablename__ = "quote_items"
    
    item_id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(UUID(as_uuid=False), ForeignKey("quotes.quote_id", ondelete="CASCADE"), nullable=False, index=True)
    resource_name = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_data = Column(Text, nullable=False)  # JSON stored as TEXT
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False)
    region = Column(String(50), nullable=False)
    parameters = Column(Text, nullable=True)  # JSON stored as TEXT
    iops_unit_price = Column(Float, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    group_id = Column(UUID(as_uuid=False), ForeignKey("quote_groups.group_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    quote = relationship("Quote", back_populates="items")
    group = relationship("QuoteGroup", back_populates="items")
    
    def __repr__(self):
        return f"<QuoteItem(item_id={self.item_id}, resource_name={self.resource_name})>"
    
    def get_resource_data(self):
        """Get resource_data as dictionary."""
        try:
            return json.loads(self.resource_data) if self.resource_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_resource_data(self, data):
        """Set resource_data from dictionary with error handling."""
        self.resource_data = sanitize_json(data, default="{}")
    
    def get_parameters(self):
        """Get parameters as dictionary."""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_parameters(self, params):
        """Set parameters from dictionary with error handling."""
        if params is None:
            self.parameters = None
        else:
            self.parameters = sanitize_json(params, default=None)
            if self.parameters == "{}":
                self.parameters = None
    
    def to_dict(self):
        """Convert quote item to dictionary."""
        return {
            "id": self.item_id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "resource_data": self.get_resource_data(),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "region": self.region,
            "parameters": self.get_parameters(),
            "iops_unit_price": self.iops_unit_price,
            "display_order": self.display_order,
            "group_id": self.group_id
        }
    
    @classmethod
    def from_dict(cls, item_dict, quote_id):
        """
        Create QuoteItem from dictionary with validation and sanitization.
        
        Args:
            item_dict: Dictionary with item data
            quote_id: Parent quote ID
        
        Returns:
            QuoteItem instance
        """
        # Validate and sanitize item_id
        item_id = item_dict.get("id")
        if not item_id or not validate_uuid(item_id):
            item_id = str(uuid.uuid4())
        
        # Validate quote_id
        if not validate_uuid(quote_id):
            raise ValueError(f"Invalid quote_id format: {quote_id}")
        
        # Sanitize string fields (truncate to max length, ensure non-empty)
        resource_name = sanitize_string(
            item_dict.get("resource_name"),
            max_length=255,
            default="Unknown Resource"
        )
        
        resource_type = sanitize_string(
            item_dict.get("resource_type"),
            max_length=100,
            default="Unknown"
        )
        
        region = sanitize_string(
            item_dict.get("region"),
            max_length=50,
            default="eu-west-2"
        )
        
        # Sanitize numeric fields (handle NaN, None, negative values)
        quantity = sanitize_float(
            item_dict.get("quantity"),
            default=1.0,
            min_value=0.0
        )
        
        unit_price = sanitize_float(
            item_dict.get("unit_price"),
            default=0.0,
            min_value=0.0
        )
        
        iops_unit_price = None
        if item_dict.get("iops_unit_price") is not None:
            iops_unit_price = sanitize_float(
                item_dict.get("iops_unit_price"),
                default=None,
                min_value=0.0
            )
            if iops_unit_price == 0.0:
                iops_unit_price = None
        
        display_order = int(sanitize_float(
            item_dict.get("display_order"),
            default=0.0,
            min_value=0.0
        ))
        
        # Create item
        item = cls(
            quote_id=quote_id,
            item_id=item_id,
            resource_name=resource_name,
            resource_type=resource_type,
            quantity=quantity,
            unit_price=unit_price,
            region=region,
            iops_unit_price=iops_unit_price,
            display_order=display_order
        )
        
        # Set JSON fields with error handling
        item.set_resource_data(item_dict.get("resource_data", {}))
        item.set_parameters(item_dict.get("parameters"))
        
        return item

