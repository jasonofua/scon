"""
Legal-related database models for SCONIA.
"""
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ARRAY, JSON, DECIMAL, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid
from app.models.base import BaseModel


class Judge(BaseModel):
    """Supreme Court judges and court personnel."""
    __tablename__ = "judges"
    
    full_name = Column(String(255), nullable=False, index=True)
    title = Column(String(100), nullable=True)
    appointment_date = Column(Date, nullable=True)
    background_summary = Column(Text, nullable=True)
    education = Column(JSON, nullable=True)  # JSONB for structured education data
    previous_positions = Column(ARRAY(Text), nullable=True)
    current_status = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_chief_justice = Column(Boolean, default=False, nullable=False)


class ConstitutionalProvision(BaseModel):
    """Nigerian Constitution articles and sections."""
    __tablename__ = "constitutional_provisions"
    
    chapter = Column(String(50), nullable=True, index=True)
    section = Column(String(50), nullable=True, index=True)
    subsection = Column(String(10), nullable=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    keywords = Column(ARRAY(Text), nullable=True)
    related_sections = Column(ARRAY(String(100)), nullable=True)


class SupremeCourtCase(BaseModel):
    """Supreme Court cases and precedents."""
    __tablename__ = "supreme_court_cases"
    
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    case_title = Column(String(500), nullable=False)
    judgment_date = Column(Date, nullable=True)
    judges_panel = Column(ARRAY(Integer), nullable=True)  # References to Judge.id
    case_summary = Column(Text, nullable=True)
    legal_principles = Column(ARRAY(Text), nullable=True)
    constitutional_provisions_cited = Column(ARRAY(Integer), nullable=True)  # References to ConstitutionalProvision.id
    case_status = Column(String(50), nullable=True)
    full_judgment_url = Column(String(500), nullable=True)


class CourtSession(BaseModel):
    """Court sessions and schedules."""
    __tablename__ = "court_sessions"
    
    session_date = Column(Date, nullable=False, index=True)
    session_time = Column(Time, nullable=True)
    case_numbers = Column(ARRAY(Text), nullable=True)
    session_type = Column(String(100), nullable=True)
    judges_assigned = Column(ARRAY(Integer), nullable=True)  # References to Judge.id
    court_room = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)


class FeeSchedule(BaseModel):
    """Court fees and payment information."""
    __tablename__ = "fee_schedules"
    
    service_type = Column(String(100), nullable=False, index=True)
    case_category = Column(String(100), nullable=True)
    fee_amount = Column(DECIMAL(15, 2), nullable=True)
    payment_methods = Column(ARRAY(Text), nullable=True)
    effective_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)


class RequiredForm(BaseModel):
    """Legal forms and templates."""
    __tablename__ = "required_forms"
    
    form_name = Column(String(255), nullable=False, index=True)
    form_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(ARRAY(Text), nullable=True)
    file_url = Column(String(500), nullable=True)
    completion_guide = Column(Text, nullable=True)
    related_procedures = Column(ARRAY(Text), nullable=True)


class Procedure(BaseModel):
    """Court procedures and processes."""
    __tablename__ = "procedures"
    
    procedure_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    step_by_step_guide = Column(JSON, nullable=True)  # JSONB for structured steps
    required_documents = Column(ARRAY(Text), nullable=True)
    estimated_timeline = Column(String(100), nullable=True)
    associated_fees = Column(ARRAY(Integer), nullable=True)  # References to FeeSchedule.id
    contact_departments = Column(ARRAY(Text), nullable=True)


class QuickOption(BaseModel):
    """Quick options for kiosk interface."""
    __tablename__ = "quick_options"
    
    option_text = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    target_procedure = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    icon_name = Column(String(100), nullable=True)
