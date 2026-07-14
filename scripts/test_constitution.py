"""
Test script to verify the Nigerian Constitution is properly indexed in the vector database.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from app.services.rag import rag_service
from app.database import AsyncSessionLocal


async def test_constitution_queries():
    """Test various constitutional queries to verify the constitution is accessible."""
    
    print("🧪 Testing Nigerian Constitution in Vector Database")
    print("=" * 60)
    
    # Test queries covering different parts of the constitution
    test_queries = [
        # Fundamental Rights (Chapter IV)
        {
            "query": "What is the right to life in Nigeria?",
            "expected_topics": ["Section 33", "right to life", "death penalty"]
        },
        {
            "query": "freedom of expression and press",
            "expected_topics": ["Section 39", "freedom of expression", "press freedom"]
        },
        {
            "query": "right to fair hearing",
            "expected_topics": ["Section 36", "fair hearing", "court", "tribunal"]
        },
        
        # Citizenship (Chapter III)
        {
            "query": "How do you become a Nigerian citizen by birth?",
            "expected_topics": ["Section 25", "citizenship by birth", "Nigerian parents"]
        },
        {
            "query": "citizenship by naturalization",
            "expected_topics": ["Section 27", "naturalization", "requirements"]
        },
        
        # Government Structure
        {
            "query": "What are the powers of the President of Nigeria?",
            "expected_topics": ["executive powers", "President", "Commander-in-Chief"]
        },
        {
            "query": "legislative powers of National Assembly",
            "expected_topics": ["National Assembly", "legislative powers", "Senate", "House of Representatives"]
        },
        
        # Federal Character and States
        {
            "query": "What is federal character principle?",
            "expected_topics": ["federal character", "diversity", "representation"]
        },
        {
            "query": "How many states are in Nigeria?",
            "expected_topics": ["36 states", "Federal Capital Territory", "Abuja"]
        },
        
        # Judiciary
        {
            "query": "What is the structure of Nigerian courts?",
            "expected_topics": ["Supreme Court", "Court of Appeal", "High Court"]
        }
    ]
    
    async with AsyncSessionLocal() as db:
        total_tests = len(test_queries)
        passed_tests = 0
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            expected_topics = test_case["expected_topics"]
            
            print(f"\n📋 Test {i}/{total_tests}: {query}")
            print("-" * 50)
            
            try:
                # Test using RAG service (same as chat endpoint)
                retrieved_context, sources = await rag_service.retrieve_context(
                    query=query,
                    db=db
                )
                
                if sources:
                    print(f"✅ Found {len(sources)} relevant sources")
                    
                    # Check if any sources are from constitution
                    constitution_sources = [s for s in sources if 'constitution' in s.get('document_type', '').lower()]
                    
                    if constitution_sources:
                        print(f"📜 Constitution sources: {len(constitution_sources)}")
                        
                        # Display top constitution source
                        top_source = constitution_sources[0]
                        print(f"   📄 Top match: {top_source.get('score', 0):.3f} relevance")
                        print(f"   📝 Content: {top_source.get('text', '')[:200]}...")
                        
                        # Check if expected topics are mentioned
                        content_lower = top_source.get('text', '').lower()
                        found_topics = [topic for topic in expected_topics if topic.lower() in content_lower]
                        
                        if found_topics:
                            print(f"   ✅ Found expected topics: {found_topics}")
                            passed_tests += 1
                        else:
                            print(f"   ⚠️  Expected topics not found: {expected_topics}")
                    else:
                        print("   ❌ No constitution sources found")
                else:
                    print("   ❌ No sources found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Constitution is properly indexed.")
        elif passed_tests > total_tests * 0.7:
            print("✅ Most tests passed. Constitution is accessible.")
        else:
            print("⚠️  Some issues detected. Check constitution indexing.")
        
        return passed_tests / total_tests


async def test_vector_database_stats():
    """Get statistics about the vector database."""
    print("\n🔍 Vector Database Statistics")
    print("=" * 40)
    
    try:
        # Get collection info
        info = await vector_db_service.get_collection_info()
        print(f"📊 Collection Info: {info}")
        
        # Test a simple search
        query_embedding = await embedding_service.generate_query_embedding("constitution")
        results = await vector_db_service.search_similar(
            query_embedding=query_embedding,
            limit=5,
            score_threshold=0.5
        )
        
        print(f"🔎 Sample search results: {len(results)} documents found")
        
        # Count constitution documents
        constitution_docs = [r for r in results if 'constitution' in r.get('document_type', '').lower()]
        print(f"📜 Constitution documents in results: {len(constitution_docs)}")
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")


async def main():
    """Main test function."""
    print("🏛️  SCONIA Constitution Test Suite")
    print("Testing Nigerian Constitution accessibility in vector database")
    print("=" * 70)
    
    try:
        # Test vector database stats
        await test_vector_database_stats()
        
        # Test constitution queries
        success_rate = await test_constitution_queries()
        
        print("\n" + "=" * 70)
        if success_rate >= 0.8:
            print("🎉 Constitution testing completed successfully!")
            print("✅ The Nigerian Constitution is properly indexed and searchable.")
        else:
            print("⚠️  Constitution testing completed with some issues.")
            print("🔧 You may need to re-run the constitution import script.")
        
        print(f"\n📈 Overall success rate: {success_rate:.1%}")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
