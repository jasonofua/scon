#!/usr/bin/env python3
"""
Upload processed constitution chunks to vector database.
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from app.models.embeddings import DocumentEmbedding
from app.services.vector_db import vector_db_service
from app.services.embeddings import embedding_service
from sqlalchemy import select


async def upload_constitution_to_vector_db():
    """Upload constitution chunks to vector database."""
    
    print("🔄 Uploading constitution to vector database...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get all constitution embeddings from database
            result = await db.execute(
                select(DocumentEmbedding).where(
                    DocumentEmbedding.document_type == "constitution"
                )
            )
            embeddings = result.scalars().all()
            
            if not embeddings:
                print("❌ No constitution embeddings found in database")
                return False
            
            print(f"📊 Found {len(embeddings)} constitution chunks to upload")
            
            # Prepare data for vector database
            vectors = []
            texts = []
            metadata_list = []
            
            for embedding in embeddings:
                if embedding.embedding_vector:
                    vectors.append(embedding.embedding_vector)
                    texts.append(embedding.text_content)
                    metadata_list.append({
                        "document_id": embedding.document_id,
                        "document_type": embedding.document_type,
                        "chunk_index": embedding.chunk_index,
                        "token_count": embedding.token_count,
                        "title": f"Constitution - Chunk {embedding.chunk_index}",
                        "url": None
                    })
            
            if not vectors:
                print("❌ No valid embeddings found")
                return False
            
            print(f"📤 Uploading {len(vectors)} vectors to Qdrant...")
            
            # Upload to vector database
            point_ids = await vector_db_service.add_embeddings(
                embeddings=vectors,
                texts=texts,
                metadata_list=metadata_list
            )
            
            print(f"✅ Successfully uploaded {len(point_ids)} constitution chunks!")
            print(f"📋 Point IDs: {point_ids[:3]}..." if len(point_ids) > 3 else f"📋 Point IDs: {point_ids}")
            
            # Test search
            print("\n🔍 Testing vector search...")
            test_query = "fundamental rights"
            query_embedding = await embedding_service.generate_query_embedding(test_query)
            
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=3
            )
            
            print(f"📋 Search test returned {len(results)} results")
            if results:
                print("✅ Vector search is working!")
                for i, result in enumerate(results):
                    print(f"  {i+1}. Score: {result.get('score', 0):.3f}")
                    print(f"     Text: {result.get('text', '')[:100]}...")
            else:
                print("⚠️  No results found in search test")
            
            return True
            
    except Exception as e:
        print(f"❌ Error uploading constitution: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(upload_constitution_to_vector_db())
