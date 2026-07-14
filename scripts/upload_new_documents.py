#!/usr/bin/env python3
"""
Upload new Nigerian legal documents to SCONIA vector database.
This script uploads the documents you added locally to the Kubernetes deployment.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service


async def upload_document_to_vector_db(file_path: str, document_type: str, title: str):
    """Upload a single document to the vector database."""
    
    print(f"📄 Processing: {title}")
    
    try:
        # Read the document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            print(f"⚠️  Warning: {file_path} is empty, skipping...")
            return False
        
        # Generate document ID
        document_id = f"{document_type}_{Path(file_path).stem}"
        
        # Create metadata
        metadata = {
            "title": title,
            "document_type": document_type,
            "source": "Nigerian Legal Documents",
            "uploaded_at": datetime.now().isoformat(),
            "file_name": Path(file_path).name
        }
        
        # Generate embeddings
        print(f"🔄 Generating embeddings for {title}...")
        embedding_records = await embedding_service.embed_document(
            text=content,
            document_id=document_id,
            document_type=document_type,
            metadata=metadata,
            use_openai=True
        )
        
        # Store embeddings in vector database
        print(f"💾 Storing {len(embedding_records)} chunks in vector database...")
        vectors = [record["embedding"] for record in embedding_records]
        texts = [record["text"] for record in embedding_records]
        metadata_list = [record["metadata"] for record in embedding_records]
        
        await vector_db_service.store_embeddings(
            embeddings=vectors,
            texts=texts,
            metadata_list=metadata_list
        )
        
        print(f"✅ Successfully uploaded {title} ({len(embedding_records)} chunks)")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading {title}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to upload all new documents."""
    
    print("🏛️  SCONIA New Documents Upload")
    print("=" * 50)
    print("Uploading your new Nigerian legal documents to the Kubernetes deployment...")
    print()
    
    # Define documents to upload
    documents = [
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
    
    successful_uploads = 0
    total_documents = len(documents)
    
    for doc in documents:
        file_path = doc["file"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"⚠️  Warning: {file_path} not found, skipping...")
            continue
        
        # Upload document
        success = await upload_document_to_vector_db(
            file_path=file_path,
            document_type=doc["type"],
            title=doc["title"]
        )
        
        if success:
            successful_uploads += 1
        
        print()  # Add spacing between documents
    
    print("=" * 50)
    print(f"📊 Upload Summary:")
    print(f"   ✅ Successful: {successful_uploads}/{total_documents}")
    print(f"   ❌ Failed: {total_documents - successful_uploads}/{total_documents}")
    
    if successful_uploads == total_documents:
        print("\n🎉 All documents uploaded successfully!")
        print("Your new Nigerian legal documents are now available in the RAG system.")
    elif successful_uploads > 0:
        print(f"\n⚠️  {successful_uploads} documents uploaded, {total_documents - successful_uploads} failed.")
        print("Check the error messages above for details.")
    else:
        print("\n❌ No documents were uploaded successfully.")
        print("Please check the error messages and try again.")


if __name__ == "__main__":
    asyncio.run(main())
