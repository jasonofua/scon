"""
Database configuration and session management for SCONIA.
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Synchronous database setup
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous database setup
async_engine = create_async_engine(
    settings.database_url_async,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    try:
        async with async_engine.begin() as conn:
            # Enable uuid-ossp extension
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            # Enable vector extension for pgvector compatibility
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            # Create all registered tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def close_db():
    """Close database connections."""
    await async_engine.dispose()
    engine.dispose()
    logger.info("Database connections closed")
