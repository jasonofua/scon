#!/usr/bin/env python3
"""
Check the status of constitution processing in SCONIA.
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from app.models.embeddings import ProcessedDocument
from app.services.vector_db import vector_db_service
from sqlalchemy import select


async def check_constitution_status():
    """Check if constitution is properly loaded."""
    
    print("🔍 Checking constitution processing status...")
    
    try:
        # Check database record
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ProcessedDocument).where(
                    ProcessedDocument.document_type == "constitution"
                )
            )
            constitution_docs = result.scalars().all()
            
            print(f"\n📊 Found {len(constitution_docs)} constitution documents in database:")
            for doc in constitution_docs:
                print(f"  - Document ID: {doc.document_id}")
                print(f"  - Status: {doc.processing_status}")
                print(f"  - Chunks: {doc.chunk_count}")
                print(f"  - Processed: {doc.processed_at}")
                print(f"  - Error: {doc.error_message}")
                print()
        
        # Check vector database
        print("🔍 Checking vector database...")
        try:
            # Search for constitution content
            from app.services.embeddings import embedding_service
            
            test_query = "fundamental rights"
            query_embedding = await embedding_service.generate_query_embedding(test_query)
            
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=5,
                document_types=["constitution"]
            )
            
            print(f"📋 Found {len(results)} constitution chunks in vector database")
            if results:
                print("✅ Constitution is properly loaded in vector database!")
                print("\nSample results:")
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. Score: {result.get('score', 0):.3f}")
                    print(f"     Text: {result.get('text', '')[:100]}...")
                    print()
            else:
                print("❌ No constitution content found in vector database")
                
        except Exception as e:
            print(f"❌ Error checking vector database: {e}")
            
    except Exception as e:
        print(f"❌ Error checking constitution status: {e}")


if __name__ == "__main__":
    asyncio.run(check_constitution_status())
