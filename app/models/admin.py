"""
Administrative and user management models for SCONIA.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import uuid
from app.models.base import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """System users (administrators, content managers)."""
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    permissions = Column(JSON, nullable=True)  # Role-based permissions
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str):
        """Set password hash."""
        self.hashed_password = pwd_context.hash(password)


class ContentUpdate(BaseModel):
    """Track content updates and changes."""
    __tablename__ = "content_updates"
    
    content_type = Column(String(50), nullable=False)  # judge, case, constitution, etc.
    content_id = Column(String(100), nullable=False)
    update_type = Column(String(50), nullable=False)  # create, update, delete
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    updated_by = Column(Integer, nullable=True)  # Reference to User.id
    update_reason = Column(Text, nullable=True)
    approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, nullable=True)  # Reference to User.id
    approved_at = Column(DateTime(timezone=True), nullable=True)


class SystemLog(BaseModel):
    """System activity and error logs."""
    __tablename__ = "system_logs"
    
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    user_id = Column(Integer, nullable=True)  # Reference to User.id
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)


class Feedback(BaseModel):
    """User feedback and ratings."""
    __tablename__ = "feedback"
    
    session_id = Column(String(100), nullable=True)
    query_id = Column(Integer, nullable=True)  # Reference to SearchQuery.id
    rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback_text = Column(Text, nullable=True)
    feedback_type = Column(String(50), nullable=True)  # helpful, not_helpful, suggestion, complaint
    category = Column(String(100), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(Integer, nullable=True)  # Reference to User.id
    resolution_notes = Column(Text, nullable=True)
