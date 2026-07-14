"""
Pydantic schemas for legal entities.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class JudgeResponse(BaseModel):
    """Response schema for judge information."""
    id: int
    full_name: str
    title: Optional[str] = None
    appointment_date: Optional[str] = None
    background_summary: Optional[str] = None
    education: Optional[Dict[str, Any]] = None
    previous_positions: Optional[List[str]] = None
    current_status: Optional[str] = None
    image_url: Optional[str] = None
    is_chief_justice: bool = False
    is_active: bool = True


class JudgeListResponse(BaseModel):
    """Response schema for list of judges."""
    judges: List[JudgeResponse]
    total_count: int
    active_count: int
    chief_justice_included: bool


class ConstitutionalProvisionResponse(BaseModel):
    """Response schema for constitutional provision."""
    id: int
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    title: Optional[str] = None
    content: str
    keywords: Optional[List[str]] = None
    related_sections: Optional[List[str]] = None


class ConstitutionalProvisionListResponse(BaseModel):
    """Response schema for list of constitutional provisions."""
    provisions: List[ConstitutionalProvisionResponse]
    total_count: int
    chapters_included: List[str]


class FeeScheduleResponse(BaseModel):
    """Response schema for fee schedule."""
    id: int
    service_type: str
    case_category: Optional[str] = None
    fee_amount: Optional[float] = None
    payment_methods: Optional[List[str]] = None
    effective_date: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class FeeCalculationRequest(BaseModel):
    """Request schema for fee calculation."""
    service_type: str
    case_category: Optional[str] = None
    additional_services: Optional[List[str]] = None


class FeeCalculationResponse(BaseModel):
    """Response schema for fee calculation."""
    service_type: str
    case_category: Optional[str] = None
    base_fee: float
    additional_fees: List[Dict[str, Any]] = []
    total_fee: float
    payment_methods: List[str]
    breakdown: List[Dict[str, Any]]


class QuickOptionResponse(BaseModel):
    """Response schema for quick options."""
    id: int
    option_text: str
    category: str
    target_procedure: Optional[str] = None
    display_order: Optional[int] = None
    icon_name: Optional[str] = None
