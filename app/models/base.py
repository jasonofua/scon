"""
Base model classes and common fields for SCONIA database models.
"""
from sqlalchemy import Column, Integer, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model class with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
