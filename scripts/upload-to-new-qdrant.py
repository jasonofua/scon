#!/usr/bin/env python3
"""
Upload all legal documents to the new Qdrant instance.
This script uploads documents to your new Qdrant cluster with proper configuration.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import re

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from app.config import settings

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_colored(message, color=NC):
    """Print colored message."""
    print(f"{color}{message}{NC}")

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 300) -> list:
    """
    Chunk text into overlapping segments for better retrieval.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum tokens per chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from previous chunk
            if overlap > 0:
                words = current_chunk.split()
                overlap_text = ' '.join(words[-overlap//10:])  # Rough word-based overlap
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

async def upload_document_to_vector_db(file_path: str, document_type: str, title: str):
    """Upload a single document to the vector database with proper chunking."""
    
    print_colored(f"📄 Processing: {title}", BLUE)
    
    try:
        # Read the document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            print_colored(f"⚠️  Warning: {file_path} is empty, skipping...", YELLOW)
            return False
        
        # Chunk the content
        print_colored(f"✂️  Chunking document...", BLUE)
        chunks = chunk_text(content, chunk_size=1500, overlap=300)
        print_colored(f"📝 Created {len(chunks)} chunks", GREEN)
        
        # Generate document ID base
        document_id_base = f"{document_type}_{Path(file_path).stem}"
        
        successful_chunks = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Create unique document ID for each chunk
                document_id = f"{document_id_base}_chunk_{i}"
                
                # Create metadata
                metadata = {
                    "title": title,
                    "document_type": document_type,
                    "source": "Nigerian Legal Documents",
                    "uploaded_at": datetime.now().isoformat(),
                    "file_name": Path(file_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                # Generate embeddings for this chunk
                embedding_records = await embedding_service.embed_document(
                    text=chunk,
                    document_id=document_id,
                    document_type=document_type,
                    metadata=metadata,
                    use_openai=True
                )
                
                # Store embeddings in vector database
                embeddings = [record["embedding"] for record in embedding_records]
                texts = [record["text"] for record in embedding_records]
                metadata_list = [record["metadata"] for record in embedding_records]
                
                point_ids = await vector_db_service.store_embeddings(
                    embeddings=embeddings,
                    texts=texts,
                    metadata_list=metadata_list
                )
                
                successful_chunks += 1
                print_colored(f"   ✅ Chunk {i+1}/{len(chunks)} uploaded ({len(point_ids)} vectors)", GREEN)
                
            except Exception as e:
                print_colored(f"   ❌ Error uploading chunk {i}: {e}", RED)
        
        print_colored(f"✅ Successfully uploaded {successful_chunks}/{len(chunks)} chunks for {title}", GREEN)
        return successful_chunks > 0
        
    except Exception as e:
        print_colored(f"❌ Error processing {file_path}: {e}", RED)
        return False

async def test_search_functionality():
    """Test the search functionality with sample queries."""
    
    print_colored("\n🔍 Testing search functionality...", BLUE)
    
    test_queries = [
        "fundamental rights",
        "Supreme Court powers",
        "electoral process",
        "criminal code provisions",
        "court hierarchy"
    ]
    
    for query in test_queries:
        try:
            print_colored(f"\n🔎 Query: '{query}'", BLUE)
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Search vector database
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=3,
                score_threshold=0.6
            )
            
            if results:
                print_colored(f"   Found {len(results)} relevant sections:", GREEN)
                for i, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    text_preview = result.get('text', '')[:150].replace('\n', ' ')
                    print_colored(f"   {i}. Score: {score:.3f} - {text_preview}...", NC)
            else:
                print_colored("   No relevant sections found", YELLOW)
                
        except Exception as e:
            print_colored(f"   ❌ Error testing query '{query}': {e}", RED)

async def main():
    """Main function to upload all documents."""
    
    print_colored("🏛️  SCONIA Document Upload to New Qdrant", BLUE)
    print_colored("=" * 60, BLUE)
    print_colored(f"📊 Qdrant URL: {settings.qdrant_url}", BLUE)
    print_colored(f"🔑 API Key configured: {'Yes' if settings.qdrant_api_key else 'No'}", BLUE)
    print("")
    
    try:
        # Initialize vector database collections
        print_colored("1. Initializing vector database collections...", BLUE)
        await vector_db_service.initialize_collections()
        print_colored("✅ Vector database collections initialized", GREEN)
        
        # Define documents to upload
        documents = [
            {
                "file": "constitution.txt",
                "type": "constitution",
                "title": "Constitution of the Federal Republic of Nigeria 1999"
            },
            {
                "file": "nigeria_electoral_act_2022.txt",
                "type": "legislation",
                "title": "Electoral Act 2022 - Federal Republic of Nigeria"
            },
            {
                "file": "nigeria_constitution_provisions.txt", 
                "type": "constitution",
                "title": "Nigerian Constitution Provisions"
            },
            {
                "file": "nigeria_court_hierarchy_and_judges.txt",
                "type": "judicial_structure", 
                "title": "Nigeria Court Hierarchy and Judges"
            },
            {
                "file": "nigeria_criminal_code_provisions.txt",
                "type": "legislation",
                "title": "Nigerian Criminal Code Provisions"
            },
            {
                "file": "nigeria_current_judges_profiles.txt",
                "type": "judicial_profiles",
                "title": "Current Nigerian Judges Profiles"
            },
            {
                "file": "nigeria_supreme_court_landmark_cases.txt",
                "type": "case_law",
                "title": "Nigerian Supreme Court Landmark Cases"
            }
        ]
        
        print_colored(f"\n2. Uploading {len(documents)} documents...", BLUE)
        
        successful_uploads = 0
        total_documents = len(documents)
        
        for doc in documents:
            file_path = doc["file"]
            
            # Check if file exists
            if not os.path.exists(file_path):
                print_colored(f"⚠️  Warning: {file_path} not found, skipping...", YELLOW)
                continue
            
            # Upload document
            success = await upload_document_to_vector_db(
                file_path=file_path,
                document_type=doc["type"],
                title=doc["title"]
            )
            
            if success:
                successful_uploads += 1
            
            print("")  # Add spacing between documents
        
        # Test search functionality
        await test_search_functionality()
        
        # Get collection info
        print_colored(f"\n3. Vector database status:", BLUE)
        try:
            info = await vector_db_service.get_collection_info()
            print_colored(f"   Collection info: {info}", GREEN)
        except Exception as e:
            print_colored(f"   Could not get collection info: {e}", YELLOW)
        
        print_colored("\n" + "=" * 60, BLUE)
        print_colored(f"🎉 Upload completed!", GREEN)
        print_colored(f"📊 Successfully uploaded: {successful_uploads}/{total_documents} documents", GREEN)
        
        if successful_uploads > 0:
            print_colored("\n📋 Next steps:", BLUE)
            print_colored("   1. Deploy the updated API with new Qdrant config", NC)
            print_colored("   2. Test the chat endpoints", NC)
            print_colored("   3. The system now has access to all legal documents", NC)
        else:
            print_colored("\n❌ No documents were uploaded successfully!", RED)
            print_colored("Please check the error messages above and try again.", RED)
        
    except Exception as e:
        print_colored(f"\n❌ Error during upload: {e}", RED)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
