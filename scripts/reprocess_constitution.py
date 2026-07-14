#!/usr/bin/env python3
"""
Reprocess constitution and generate embeddings.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from app.models.embeddings import ProcessedDocument, DocumentEmbedding
from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from sqlalchemy import select, delete


async def reprocess_constitution():
    """Reprocess constitution and generate embeddings."""
    
    print("🔄 Reprocessing constitution with embeddings...")
    
    constitution_path = Path(__file__).parent.parent / "constitution.txt"
    
    if not constitution_path.exists():
        print(f"❌ Constitution file not found at: {constitution_path}")
        return False
    
    try:
        async with AsyncSessionLocal() as db:
            # Delete existing processed document record
            await db.execute(
                delete(ProcessedDocument).where(
                    ProcessedDocument.document_type == "constitution"
                )
            )
            await db.commit()
            print("🗑️  Deleted existing constitution record")
            
            # Read constitution file
            with open(constitution_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print(f"📄 Read constitution file: {len(text)} characters")
            
            # Process document and generate embeddings
            document_id = "constitution_nigeria_1999"
            
            # Generate embeddings for the document
            embedding_records = await embedding_service.embed_document(
                text=text,
                document_id=document_id,
                document_type="constitution",
                metadata={
                    "title": "Constitution of the Federal Republic of Nigeria 1999",
                    "source": "Official Constitution",
                    "year": 1999
                },
                use_openai=True
            )
            
            print(f"📊 Generated {len(embedding_records)} embedding chunks")
            
            # Store embeddings in database
            embeddings_to_store = []
            vectors = []
            texts = []
            metadata_list = []
            
            for record in embedding_records:
                # Store in PostgreSQL
                embedding_obj = DocumentEmbedding(
                    document_id=record["metadata"]["document_id"],
                    document_type=record["metadata"]["document_type"],
                    chunk_text=record["text"],
                    embedding=record["embedding"],
                    doc_metadata=record["metadata"],
                    chunk_index=record["metadata"]["chunk_index"],
                    token_count=record["metadata"]["token_count"]
                )
                embeddings_to_store.append(embedding_obj)
                
                # Prepare for vector database
                vectors.append(record["embedding"])
                texts.append(record["text"])
                metadata_list.append(record["metadata"])
            
            # Save to PostgreSQL
            db.add_all(embeddings_to_store)
            await db.commit()
            print(f"💾 Saved {len(embeddings_to_store)} embeddings to PostgreSQL")
            
            # Upload to vector database
            point_ids = await vector_db_service.store_embeddings(
                embeddings=vectors,
                texts=texts,
                metadata_list=metadata_list
            )
            print(f"📤 Uploaded {len(point_ids)} vectors to Qdrant")
            
            # Create processed document record
            processed_doc = ProcessedDocument(
                document_id=document_id,
                document_name="constitution.txt",
                document_type="constitution",
                file_path=str(constitution_path),
                file_size=len(text),
                processing_status="completed",
                chunk_count=len(embedding_records),
                processed_at=None  # Will be set automatically
            )
            db.add(processed_doc)
            await db.commit()
            
            print("✅ Constitution reprocessing completed successfully!")
            
            # Test search
            print("\n🔍 Testing search...")
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
            
            return True
            
    except Exception as e:
        print(f"❌ Error reprocessing constitution: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(reprocess_constitution())
