"""
Pydantic schemas for chat functionality.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[str] = Field(None, description="Additional context from previous conversation")
    user_type: Optional[str] = Field(None, description="Type of user: citizen, legal_professional, student")


class Source(BaseModel):
    """Source document information."""
    document_id: str
    document_type: str
    title: str
    content_snippet: str
    relevance_score: float
    url: Optional[str] = None


class QuickOption(BaseModel):
    """Quick option for follow-up actions."""
    text: str
    action: str
    category: str


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    answer: str = Field(..., description="AI-generated response")
    sources: List[Source] = Field(default=[], description="Source documents used")
    quick_options: List[QuickOption] = Field(default=[], description="Suggested follow-up actions")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the response")
    session_id: str = Field(..., description="Session ID")
    query_id: int = Field(..., description="Unique query identifier")
    response_time: float = Field(..., description="Response time in seconds")
    intent_classification: Optional[str] = Field(None, description="Classified intent of the query")


class ChatMessage(BaseModel):
    """Individual chat message."""
    id: int
    query: str
    response: str
    sources: List[Source]
    timestamp: datetime
    rating: Optional[int] = None
    feedback: Optional[str] = None


class ChatSession(BaseModel):
    """Chat session with message history."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    messages: List[ChatMessage]
    user_type: Optional[str] = None
    total_queries: int
    average_rating: Optional[float] = None


class FeedbackRequest(BaseModel):
    """Feedback submission schema."""
    session_id: str
    query_id: Optional[int] = None
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Detailed feedback")
    feedback_type: Optional[str] = Field(None, description="Type: helpful, not_helpful, suggestion, complaint")


class StreamingResponse(BaseModel):
    """Streaming response chunk."""
    type: str  # "chunk", "sources", "complete"
    content: str
    metadata: Optional[Dict[str, Any]] = None
