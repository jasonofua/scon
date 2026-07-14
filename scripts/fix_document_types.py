#!/usr/bin/env python3
"""
Script to fix document types in the database.
This script updates the document_type field for documents that were uploaded
but don't have the correct metadata set.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_async_db_session
from app.models.document import ProcessedDocument

# Document type mappings based on document IDs
DOCUMENT_TYPE_MAPPINGS = {
    'constitution_nigeria_1999': 'constitution',
    'constitution_nigeria_constitution_provisions': 'constitution',
    'case_5': 'case',
    'judicial_profiles_nigeria_current_judges_profiles': 'judicial',
    'judicial_structure_nigeria_court_hierarchy_and_judges': 'judicial',
    'legislation_nigeria_criminal_code_provisions': 'legislation',
    'legislation_nigeria_electoral_act_2022': 'legislation',
    'legislation_nigeria_evidence_act_2011': 'legislation',
    'legislation_nigeria_companies_and_allied_matters_act': 'legislation',
    'legislation_nigeria_land_use_act_1978': 'legislation',
    'legislation_nigeria_public_procurement_act_2007': 'legislation',
    'case_1': 'case',
    'case_2': 'case',
    'case_3': 'case',
    'case_4': 'case',
}

async def fix_document_types():
    """Fix document types in the database."""
    print("🔧 Fixing document types in database...")
    
    async with get_async_db_session() as db:
        try:
            # Get all documents
            result = await db.execute(
                select(ProcessedDocument).where(ProcessedDocument.is_active == True)
            )
            documents = result.scalars().all()
            
            print(f"📄 Found {len(documents)} documents")
            
            updated_count = 0
            for document in documents:
                # Determine document type from document_id
                document_type = None
                
                for doc_id_pattern, doc_type in DOCUMENT_TYPE_MAPPINGS.items():
                    if doc_id_pattern in document.document_id:
                        document_type = doc_type
                        break
                
                # If no specific mapping, try to infer from document_id
                if not document_type:
                    if 'constitution' in document.document_id.lower():
                        document_type = 'constitution'
                    elif 'case' in document.document_id.lower():
                        document_type = 'case'
                    elif 'legislation' in document.document_id.lower():
                        document_type = 'legislation'
                    elif 'judicial' in document.document_id.lower():
                        document_type = 'judicial'
                    else:
                        document_type = 'general'
                
                # Update if different
                if document.document_type != document_type:
                    print(f"📝 Updating {document.document_id}: {document.document_type} -> {document_type}")
                    
                    await db.execute(
                        update(ProcessedDocument)
                        .where(ProcessedDocument.id == document.id)
                        .values(document_type=document_type)
                    )
                    updated_count += 1
                else:
                    print(f"✅ {document.document_id}: already has correct type '{document_type}'")
            
            await db.commit()
            print(f"🎉 Updated {updated_count} documents successfully!")
            
            # Verify the updates
            print("\n📊 Document type summary:")
            result = await db.execute(
                select(ProcessedDocument.document_type, ProcessedDocument.document_id)
                .where(ProcessedDocument.is_active == True)
            )
            documents = result.all()
            
            type_counts = {}
            for doc_type, doc_id in documents:
                if doc_type not in type_counts:
                    type_counts[doc_type] = []
                type_counts[doc_type].append(doc_id)
            
            for doc_type, doc_ids in type_counts.items():
                print(f"  {doc_type}: {len(doc_ids)} documents")
                for doc_id in doc_ids[:3]:  # Show first 3
                    print(f"    - {doc_id}")
                if len(doc_ids) > 3:
                    print(f"    ... and {len(doc_ids) - 3} more")
            
        except Exception as e:
            print(f"❌ Error fixing document types: {e}")
            await db.rollback()
            raise

async def main():
    """Main function."""
    print("🏛️  SCONIA Document Type Fixer")
    print("=" * 50)
    
    try:
        await fix_document_types()
        print("\n✅ Document types fixed successfully!")
        print("\nNow the constitution and cases endpoints should work properly.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
