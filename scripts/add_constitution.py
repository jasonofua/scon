"""
Add the Nigerian Constitution to the vector database for SCONIA.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.document_processor import document_processor
from app.database import AsyncSessionLocal


async def add_constitution_to_vector_db():
    """Add the constitution.txt file to the vector database."""
    
    # Path to the constitution file
    constitution_path = Path(__file__).parent.parent / "constitution.txt"
    
    if not constitution_path.exists():
        print(f"❌ Constitution file not found at: {constitution_path}")
        print("Please ensure constitution.txt is in the project root directory.")
        return False
    
    print(f"📄 Found constitution file: {constitution_path}")
    print(f"📊 File size: {constitution_path.stat().st_size / 1024:.1f} KB")
    
    try:
        # Create database session
        async with AsyncSessionLocal() as db:
            print("🔄 Processing constitution document...")
            
            # Process the document using the document processor
            document_id = await document_processor.process_document(
                file_path=str(constitution_path),
                document_type="constitution",
                db=db,
                use_openai=True  # Set to False to use local embeddings
            )
            
            print(f"✅ Constitution successfully added to vector database!")
            print(f"📋 Document ID: {document_id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error processing constitution: {e}")
        return False


async def test_constitution_search():
    """Test searching the constitution content."""
    print("\n🔍 Testing constitution search...")
    
    from app.services.embeddings import embedding_service
    from app.services.vector_db import vector_db_service
    
    test_queries = [
        "fundamental rights",
        "freedom of expression", 
        "right to life",
        "citizenship by birth",
        "federal character",
        "separation of powers"
    ]
    
    for query in test_queries:
        try:
            print(f"\n🔎 Query: '{query}'")
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Search vector database for constitution content
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=3,
                score_threshold=0.6
                # Note: document_types filter removed due to API change
            )
            
            if results:
                print(f"   Found {len(results)} relevant sections:")
                for i, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    text_preview = result.get('text', '')[:150].replace('\n', ' ')
                    print(f"   {i}. Score: {score:.3f} - {text_preview}...")
            else:
                print("   No relevant sections found")
                
        except Exception as e:
            print(f"   ❌ Error testing query '{query}': {e}")


async def main():
    """Main function to add constitution and test."""
    print("🏛️  SCONIA Constitution Import Tool")
    print("=" * 50)
    
    # Add constitution to vector database
    success = await add_constitution_to_vector_db()
    
    if success:
        # Test the search functionality
        await test_constitution_search()
        
        print("\n" + "=" * 50)
        print("✅ Constitution import completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Start the SCONIA API server")
        print("   2. Test constitutional queries through the chat interface")
        print("   3. The system will now have access to the full Nigerian Constitution")
        
    else:
        print("\n❌ Constitution import failed!")
        print("Please check the error messages above and try again.")


if __name__ == "__main__":
    asyncio.run(main())
