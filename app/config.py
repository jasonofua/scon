"""
Configuration settings for SCONIA application.
"""
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "SCONIA"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Server port (Render assigns this dynamically)
    port: int = 8000

    # Skip DB init during build/startup when DB isn't available
    skip_db_init: bool = False

    # Database
    database_url: str
    # Async URL is auto-derived from DATABASE_URL if not explicitly set
    # (Render's Postgres add-on only provides the sync postgresql:// URL)
    database_url_async: Optional[str] = None

    @model_validator(mode="after")
    def derive_async_database_url(self) -> "Settings":
        """Auto-derive asyncpg URL from sync URL if not explicitly provided."""
        if self.database_url_async is None:
            self.database_url_async = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            ).replace(
                "postgres://", "postgresql+asyncpg://", 1  # Render uses postgres://
            )
        return self
    
    # Vector Database
    vector_db_type: str = "chromadb"  # qdrant or chromadb or pgvector
    qdrant_url: str = "https://46d164a0-aa9f-48c0-8ffc-1b0d1b60a591.us-east4-0.gcp.cloud.qdrant.io:6333"
    qdrant_api_key: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.SPNWCGECEkm2mU5cVWGJxS_ImkZpahtae08n7N27u_Q"
    chromadb_path: str = "./data/chromadb"
    
    # AI/ML
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        # Render URLs (update after first deploy)
        "https://sconia-frontend.onrender.com",
        "https://sconia-api.onrender.com",
        # Previous deployments
        "https://sconia-frontend-114876416729.us-central1.run.app",
        "https://sconia-gao3h1dgq-codeforgexs-projects.vercel.app",
        "https://sconia.vercel.app",
    ]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"
    allowed_file_types: List[str] = ["pdf", "docx", "txt"]
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Content Moderation
    enable_content_moderation: bool = True
    profanity_filter: bool = True
    
    # Analytics
    enable_analytics: bool = True
    prometheus_port: int = 8001
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("allowed_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# SCONIA-specific prompts and configurations
SCONIA_SYSTEM_PROMPT = """
You are SCONIA, the Supreme Court of Nigeria Information Assistant deployed on touchscreen kiosks nationwide.

Identity & Mission:
- Professional, helpful, culturally aware, and educationally focused
- Democratize access to legal information across Nigeria
- Serve citizens, legal practitioners, students, and court visitors

Core Functions:
1. Legal Information Provider - Constitutional law, Supreme Court rules, procedures
2. Educational Assistant - Explain complex concepts simply, provide context
3. Procedural Guide - Step-by-step processes, requirements, fee calculations
4. Cultural Sensitivity - Respect Nigerian values, adapt to understanding levels

Communication Guidelines:
- Acknowledge query → Core information → Additional context → Next steps → Further assistance
- Professional but approachable
- Clear, concise language avoiding jargon
- Educational focus with practical guidance
- Equal respect for all users

Limitations:
- Cannot provide specific legal advice for individual cases
- Cannot represent users or make legal judgments
- Cannot handle confidential information
- Must refer to legal practitioners for specific advice

Context: {context}
Query: {query}

Respond as SCONIA with the above guidelines.
"""

QUICK_OPTIONS_PROMPT = """
Based on the user's query, suggest relevant quick options:
- "File a case or appeal"
- "Understand court procedures" 
- "Access legal documents"
- "Find court information"
- "Calculate fees"
- "Ask a legal question"

Select 2-3 most relevant options for follow-up.
"""

# Legal document categories for classification
DOCUMENT_CATEGORIES = {
    "constitution": "Constitutional provisions and amendments",
    "case_law": "Supreme Court cases and precedents",
    "procedures": "Court procedures and filing requirements",
    "judges": "Judge profiles and court personnel",
    "schedules": "Court schedules and calendar",
    "fees": "Court fees and payment information",
    "forms": "Legal forms and templates",
    "general": "General legal information"
}

# Intent classification categories
INTENT_CATEGORIES = [
    "constitutional_query",
    "judge_information", 
    "court_schedule",
    "case_law",
    "procedural_information",
    "fee_calculation",
    "general_information",
    "greeting",
    "help_request"
]
