"""
Vector embeddings and document processing models for SCONIA.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from app.models.base import BaseModel


class DocumentEmbedding(BaseModel):
    """Document embeddings for vector search."""
    __tablename__ = "document_embeddings"
    
    document_id = Column(String(100), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)  # 'constitution', 'case', 'procedure', etc.
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # Gemini embedding dimension
    doc_metadata = Column(JSON, nullable=True)  # Additional metadata for filtering
    chunk_index = Column(Integer, nullable=True)  # Order of chunk in document
    token_count = Column(Integer, nullable=True)  # Number of tokens in chunk


class ProcessedDocument(BaseModel):
    """Track processed documents for embeddings."""
    __tablename__ = "processed_documents"
    
    document_id = Column(String(100), unique=True, nullable=False, index=True)
    document_name = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=False)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    chunk_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class SearchQuery(BaseModel):
    """Track user search queries for analytics."""
    __tablename__ = "search_queries"
    
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=True)  # chat, search, quick_option
    user_session = Column(String(100), nullable=True)
    response_time = Column(Float, nullable=True)  # Response time in seconds
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating
    documents_retrieved = Column(Integer, nullable=True)
    intent_classification = Column(String(100), nullable=True)


class UserSession(BaseModel):
    """Track user sessions for analytics."""
    __tablename__ = "user_sessions"
    
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    query_count = Column(Integer, default=0, nullable=False)
    user_type = Column(String(50), nullable=True)  # citizen, legal_professional, student, etc.
    location = Column(String(100), nullable=True)  # Kiosk location
    device_type = Column(String(50), nullable=True)  # kiosk, mobile, web
