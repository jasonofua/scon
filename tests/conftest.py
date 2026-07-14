"""
Test configuration and fixtures for SCONIA tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.main import app
from app.database import get_async_db, Base
from app.models.admin import User
from app.services.auth import create_access_token
from app.config import settings


# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def client(test_db) -> TestClient:
    """Create test client with database override."""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_superuser=False,
        is_staff=False
    )
    user.set_password("testpassword")
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    return user


@pytest.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """Create test admin user."""
    admin = User(
        username="testadmin",
        email="admin@example.com",
        full_name="Test Admin",
        is_superuser=True,
        is_staff=True
    )
    admin.set_password("adminpassword")
    
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    
    return admin


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create JWT token for test user."""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Create JWT token for test admin."""
    return create_access_token(data={"sub": test_admin.username})


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers for test user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Create authorization headers for test admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_legal_data():
    """Sample legal data for testing."""
    return {
        "judge": {
            "full_name": "Hon. Justice Test Judge",
            "title": "Justice of the Supreme Court",
            "appointment_date": "2020-01-01",
            "background_summary": "Test judge for unit testing",
            "is_chief_justice": False
        },
        "constitutional_provision": {
            "chapter": "Chapter IV",
            "section": "999",
            "title": "Test Right",
            "content": "This is a test constitutional provision for unit testing purposes.",
            "keywords": ["test", "unit testing", "constitutional"]
        },
        "case": {
            "case_number": "TEST/2024/001",
            "case_title": "Test Case v. Unit Testing",
            "judgment_date": "2024-01-01",
            "case_summary": "This is a test case for unit testing purposes.",
            "legal_principles": ["test principle", "unit testing principle"]
        },
        "fee": {
            "service_type": "Test Filing",
            "case_category": "Test Category",
            "fee_amount": 1000.00,
            "payment_methods": ["Test Payment"],
            "description": "Test fee for unit testing"
        }
    }


@pytest.fixture
def temp_file():
    """Create temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for SCONIA unit testing.\n")
        f.write("It contains sample legal content for processing.\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "data": [
            {
                "embedding": [0.1] * 1536,  # Mock embedding vector
                "index": 0,
                "object": "embedding"
            }
        ],
        "model": "text-embedding-ada-002",
        "object": "list",
        "usage": {
            "prompt_tokens": 10,
            "total_tokens": 10
        }
    }


@pytest.fixture
def mock_chat_response():
    """Mock chat completion response for testing."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from SCONIA for unit testing purposes."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        }
    }


# Test configuration overrides
@pytest.fixture(autouse=True)
def test_settings():
    """Override settings for testing."""
    original_debug = settings.debug
    original_openai_key = settings.openai_api_key
    
    # Set test values
    settings.debug = True
    settings.openai_api_key = "test-key"
    
    yield
    
    # Restore original values
    settings.debug = original_debug
    settings.openai_api_key = original_openai_key
