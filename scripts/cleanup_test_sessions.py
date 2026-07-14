"""
Clean up test/fake sessions from SCONIA database.
"""
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from app.models.embeddings import UserSession, SearchQuery


async def cleanup_test_sessions():
    """Remove test sessions and their associated queries."""
    async with AsyncSessionLocal() as session:
        # Define patterns for test sessions to remove
        test_patterns = [
            "rag-test-session",
            "rag-test-session-2", 
            "demo-session-001",
            "test-session-123",
            "test-session-456",
            "test-session",
            "demo-session",
            "sample-session"
        ]
        
        # Also remove sessions that start with "Chat Session session_" (auto-generated test data)
        auto_generated_pattern = "Chat Session session_%"
        
        print("Finding test sessions to remove...")
        
        # Get all sessions that match test patterns
        test_sessions_to_remove = []
        
        # Check for exact matches and pattern matches
        for pattern in test_patterns:
            result = await session.execute(
                select(UserSession).where(UserSession.session_id.like(f"%{pattern}%"))
            )
            sessions = result.scalars().all()
            test_sessions_to_remove.extend([s.session_id for s in sessions])
        
        # Check for auto-generated sessions
        result = await session.execute(
            select(UserSession).where(UserSession.session_id.like(auto_generated_pattern))
        )
        auto_sessions = result.scalars().all()
        test_sessions_to_remove.extend([s.session_id for s in auto_sessions])
        
        # Remove duplicates
        test_sessions_to_remove = list(set(test_sessions_to_remove))
        
        if not test_sessions_to_remove:
            print("No test sessions found to remove.")
            return
        
        print(f"Found {len(test_sessions_to_remove)} test sessions to remove:")
        for session_id in test_sessions_to_remove:
            print(f"  - {session_id}")
        
        # Remove associated search queries first (foreign key constraint)
        print("\nRemoving associated search queries...")
        for session_id in test_sessions_to_remove:
            result = await session.execute(
                delete(SearchQuery).where(SearchQuery.user_session == session_id)
            )
            if result.rowcount > 0:
                print(f"  Removed {result.rowcount} queries for session {session_id}")
        
        # Remove the sessions
        print("\nRemoving test sessions...")
        for session_id in test_sessions_to_remove:
            result = await session.execute(
                delete(UserSession).where(UserSession.session_id == session_id)
            )
            if result.rowcount > 0:
                print(f"  Removed session: {session_id}")
        
        # Commit all changes
        await session.commit()
        print(f"\nCleanup complete! Removed {len(test_sessions_to_remove)} test sessions and their associated data.")


async def list_all_sessions():
    """List all current sessions for review."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserSession).order_by(UserSession.start_time.desc())
        )
        sessions = result.scalars().all()
        
        print(f"\nCurrent sessions in database ({len(sessions)} total):")
        for s in sessions:
            print(f"  - {s.session_id} (started: {s.start_time}, queries: {s.query_count})")


async def main():
    """Main cleanup function."""
    print("SCONIA Test Session Cleanup Tool")
    print("=" * 40)
    
    # First, list current sessions
    await list_all_sessions()
    
    # Ask for confirmation
    print("\n" + "=" * 40)
    response = input("Do you want to proceed with cleanup? (y/N): ").strip().lower()
    
    if response == 'y':
        await cleanup_test_sessions()
        
        # Show remaining sessions
        await list_all_sessions()
    else:
        print("Cleanup cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
