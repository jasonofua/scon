#!/usr/bin/env python3
"""
Test search functionality for the new legal content.
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service


async def test_legal_content_search():
    """Test search for legal content."""
    
    print("🔍 Testing legal content search...")
    
    test_queries = [
        "How to file an appeal to the Supreme Court",
        "What are the fees for filing an appeal",
        "Marwa v. Nyako case",
        "Constitutional interpretation application",
        "Motion on notice form"
    ]
    
    for query in test_queries:
        print(f"\n📋 Testing query: '{query}'")
        
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Search vector database
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=5,
                score_threshold=0.7
            )
            
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results):
                doc_type = result.get('metadata', {}).get('document_type', 'unknown')
                title = result.get('metadata', {}).get('title', 'No title')
                score = result.get('score', 0)
                text_preview = result.get('text', '')[:100] + '...'
                
                print(f"   {i+1}. [{doc_type}] {title}")
                print(f"      Score: {score:.3f}")
                print(f"      Preview: {text_preview}")
                print()
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_legal_content_search())
