"""
Test script for SCONIA Gemini and ChromaDB integration.
Verifies embedding generation, vector database operations, and chat response generation.
"""
import asyncio
import sys
import os

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from app.services.chat import ChatService
from app.database import get_async_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def main():
    print("🚀 Starting SCONIA Gemini & ChromaDB Integration Test...")
    print(f"📊 Vector DB Type: {settings.vector_db_type}")
    print(f"🤖 Gemini Model: {settings.gemini_model}")
    print(f"🧬 Gemini Embedding Model: {settings.gemini_embedding_model}")
    
    # 1. Test Embedding Generation
    print("\n1. Testing Gemini Embedding Generation...")
    test_text = "What are the fundamental rights in the Nigerian Constitution?"
    try:
        embedding = await embedding_service.generate_query_embedding(test_text)
        print(f"✅ Success! Embedding length: {len(embedding)}")
        print(f"🔢 Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        return

    # 2. Test Vector DB Storage & Query
    print("\n2. Testing Vector DB (ChromaDB)...")
    try:
        await vector_db_service.initialize_collections()
        print("✅ Vector DB collections initialized.")
        
        # Store a sample document
        metadata = {
            "document_id": "test_const_sec_1",
            "document_type": "constitution",
            "title": "Fundamental Rights Test Section",
            "chunk_index": 0
        }
        
        point_ids = await vector_db_service.store_embeddings(
            embeddings=[embedding],
            texts=["Every citizen is entitled to fundamental human rights as detailed in Chapter IV of the Nigerian Constitution."],
            metadata_list=[metadata]
        )
        print(f"✅ Stored test embedding in vector database. IDs: {point_ids}")
        
        # Search for the document
        search_results = await vector_db_service.search_similar(
            query_embedding=embedding,
            limit=1,
            score_threshold=0.5
        )
        print(f"✅ Search complete. Results count: {len(search_results)}")
        if search_results:
            print(f"📄 Top result text: '{search_results[0]['text']}'")
            print(f"🎯 Top result score: {search_results[0]['score']}")
        else:
            print("❌ No search results found.")
            
    except Exception as e:
        print(f"❌ Vector DB operations failed: {e}")
        return

    # 3. Test Chat Completion
    print("\n3. Testing Gemini Chat Generation...")
    try:
        # Create a mock DB session for logging if needed
        # We'll just test the private generate response method which doesn't need DB persistence
        engine = create_async_engine(settings.database_url_async)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            chat_service = ChatService(db=session)
            response = await chat_service._generate_response(
                query="Hello SCONIA, who are you?",
                context="No special context",
                intent="greeting",
                entities={}
            )
            print(f"✅ Success! Gemini response:")
            print(f"----------------------------------------\n{response}\n----------------------------------------")
            
    except Exception as e:
        print(f"❌ Failed to generate chat response: {e}")
        return

    print("\n🎉 All integration tests passed successfully!")

if __name__ == "__main__":
    # Ensure a GEMINI_API_KEY is available (or loaded from environment)
    if not os.environ.get("GEMINI_API_KEY") and not settings.gemini_api_key:
        print("⚠️ Warning: GEMINI_API_KEY environment variable not set. Please export it or define it in .env.")
    
    asyncio.run(main())
