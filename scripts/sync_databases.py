#!/usr/bin/env python3
"""
Script to sync document IDs between PostgreSQL and Qdrant databases.
This fixes the mismatch where documents exist in one database but not the other.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any, List

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_db
from app.models.embeddings import ProcessedDocument
from app.services.vector_db import VectorDBService
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession


async def get_qdrant_document_ids() -> Dict[str, Dict[str, Any]]:
    """Get all document IDs and their metadata from Qdrant."""
    vector_db = VectorDBService()
    
    try:
        # Get all points from Qdrant
        response = vector_db.client.scroll(
            collection_name=vector_db.collection_name,
            limit=1000,  # Adjust if you have more documents
            with_payload=True
        )
        
        document_info = {}
        for point in response[0]:
            payload = point.payload
            doc_id = payload.get('document_id')
            if doc_id and doc_id not in document_info:
                document_info[doc_id] = {
                    'document_type': payload.get('document_type', 'unknown'),
                    'file_path': payload.get('file_path', ''),
                    'file_size': payload.get('file_size', 0),
                    'processed_at': payload.get('processed_at', ''),
                    'chunk_count': 0
                }
            
            if doc_id:
                document_info[doc_id]['chunk_count'] += 1
        
        print(f"Found {len(document_info)} unique documents in Qdrant")
        return document_info
        
    except Exception as e:
        print(f"Error getting Qdrant document IDs: {e}")
        return {}


async def get_postgres_document_ids(db: AsyncSession) -> Set[str]:
    """Get all document IDs from PostgreSQL."""
    try:
        result = await db.execute(select(ProcessedDocument.document_id))
        document_ids = {row[0] for row in result.fetchall()}
        print(f"Found {len(document_ids)} documents in PostgreSQL")
        return document_ids
        
    except Exception as e:
        print(f"Error getting PostgreSQL document IDs: {e}")
        return set()


async def create_missing_postgres_records(
    db: AsyncSession, 
    qdrant_docs: Dict[str, Dict[str, Any]], 
    postgres_ids: Set[str]
) -> int:
    """Create ProcessedDocument records for Qdrant documents missing in PostgreSQL."""
    missing_docs = []
    
    for doc_id, info in qdrant_docs.items():
        if doc_id not in postgres_ids:
            # Determine document name from document_id
            if doc_id.startswith('constitution'):
                doc_name = 'constitution.txt'
            elif 'case' in doc_id.lower():
                doc_name = 'legal_cases.txt'
            elif 'court' in doc_id.lower() or 'judge' in doc_id.lower():
                doc_name = 'court_structure.txt'
            elif 'procedure' in doc_id.lower():
                doc_name = 'court_procedures.txt'
            else:
                doc_name = f'{doc_id}.txt'
            
            # Create ProcessedDocument record
            processed_doc = ProcessedDocument(
                document_id=doc_id,
                document_name=doc_name,
                document_type=info['document_type'],
                file_path=info['file_path'] or f'/app/{doc_name}',
                file_size=info['file_size'] or 1000,
                processing_status='completed',
                chunk_count=info['chunk_count'],
                processed_at=datetime.utcnow()
            )
            missing_docs.append(processed_doc)
    
    if missing_docs:
        db.add_all(missing_docs)
        await db.commit()
        print(f"Created {len(missing_docs)} missing PostgreSQL records")
        
        for doc in missing_docs:
            print(f"  - {doc.document_id} ({doc.document_type})")
    
    return len(missing_docs)


async def handle_orphaned_postgres_records(
    db: AsyncSession, 
    qdrant_docs: Dict[str, Dict[str, Any]], 
    postgres_ids: Set[str]
) -> int:
    """Handle PostgreSQL records that don't have corresponding Qdrant documents."""
    orphaned_ids = postgres_ids - set(qdrant_docs.keys())
    
    if not orphaned_ids:
        print("No orphaned PostgreSQL records found")
        return 0
    
    print(f"Found {len(orphaned_ids)} orphaned PostgreSQL records:")
    for doc_id in orphaned_ids:
        print(f"  - {doc_id}")
    
    # Option 1: Mark as failed (recommended)
    result = await db.execute(
        select(ProcessedDocument).where(
            ProcessedDocument.document_id.in_(orphaned_ids)
        )
    )
    orphaned_docs = result.scalars().all()
    
    for doc in orphaned_docs:
        doc.processing_status = 'failed'
        doc.error_message = 'No corresponding vector embeddings found'
    
    await db.commit()
    print(f"Marked {len(orphaned_docs)} orphaned records as failed")
    
    return len(orphaned_docs)


async def main():
    """Main function to sync databases."""
    print("🔄 Starting database synchronization...")
    
    # Get document IDs from both databases
    qdrant_docs = await get_qdrant_document_ids()
    
    if not qdrant_docs:
        print("❌ No documents found in Qdrant. Exiting.")
        return
    
    async for db in get_async_db():
        try:
            postgres_ids = await get_postgres_document_ids(db)
            
            print(f"\n📊 Database Status:")
            print(f"  Qdrant documents: {len(qdrant_docs)}")
            print(f"  PostgreSQL documents: {len(postgres_ids)}")
            print(f"  Common documents: {len(set(qdrant_docs.keys()) & postgres_ids)}")
            print(f"  Missing in PostgreSQL: {len(set(qdrant_docs.keys()) - postgres_ids)}")
            print(f"  Missing in Qdrant: {len(postgres_ids - set(qdrant_docs.keys()))}")
            
            # Create missing PostgreSQL records
            print(f"\n🔧 Creating missing PostgreSQL records...")
            created_count = await create_missing_postgres_records(db, qdrant_docs, postgres_ids)
            
            # Handle orphaned PostgreSQL records
            print(f"\n🧹 Handling orphaned PostgreSQL records...")
            orphaned_count = await handle_orphaned_postgres_records(db, qdrant_docs, postgres_ids)
            
            print(f"\n✅ Synchronization complete!")
            print(f"  Created: {created_count} PostgreSQL records")
            print(f"  Marked as failed: {orphaned_count} orphaned records")
            
            # Show final status
            postgres_ids_after = await get_postgres_document_ids(db)
            active_postgres_ids = set()
            
            result = await db.execute(
                select(ProcessedDocument.document_id).where(
                    ProcessedDocument.processing_status == 'completed'
                )
            )
            active_postgres_ids = {row[0] for row in result.fetchall()}
            
            print(f"\n📈 Final Status:")
            print(f"  Active PostgreSQL documents: {len(active_postgres_ids)}")
            print(f"  Qdrant documents: {len(qdrant_docs)}")
            print(f"  Synchronized documents: {len(set(qdrant_docs.keys()) & active_postgres_ids)}")
            
            break
            
        except Exception as e:
            print(f"❌ Error during synchronization: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
