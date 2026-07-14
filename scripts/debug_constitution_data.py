#!/usr/bin/env python3
"""
Debug constitution data storage.
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import text


async def debug_constitution_data():
    """Debug where constitution data is stored."""
    
    print("🔍 Debugging constitution data storage...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Check all tables for constitution data
            tables_to_check = [
                "processed_documents",
                "document_embeddings", 
                "constitutional_provisions",
                "search_queries"
            ]
            
            for table in tables_to_check:
                try:
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"📊 {table}: {count} records")
                    
                    if table == "processed_documents":
                        result = await db.execute(text(f"SELECT document_id, document_type, processing_status, chunk_count FROM {table} WHERE document_type = 'constitution'"))
                        rows = result.fetchall()
                        for row in rows:
                            print(f"  - {row}")
                    
                except Exception as e:
                    print(f"❌ Error checking {table}: {e}")
            
            # Check if there are any embeddings at all
            try:
                result = await db.execute(text("SELECT document_type, COUNT(*) FROM document_embeddings GROUP BY document_type"))
                rows = result.fetchall()
                print(f"\n📊 Document embeddings by type:")
                for row in rows:
                    print(f"  - {row[0]}: {row[1]} embeddings")
            except Exception as e:
                print(f"❌ Error checking embeddings: {e}")
                
            # Check table schema
            try:
                result = await db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'document_embeddings'"))
                rows = result.fetchall()
                print(f"\n📋 document_embeddings table schema:")
                for row in rows:
                    print(f"  - {row[0]}: {row[1]}")
            except Exception as e:
                print(f"❌ Error checking schema: {e}")
                
    except Exception as e:
        print(f"❌ Error debugging: {e}")


if __name__ == "__main__":
    asyncio.run(debug_constitution_data())
