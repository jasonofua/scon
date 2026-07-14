#!/usr/bin/env python3
"""
Initialize Qdrant vector database with Nigerian Constitution data.
"""
import asyncio
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
import openai
import os
import sys
import time
import httpx

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration with larger timeouts
QDRANT_URL = "https://6b71346c-f2c7-4515-a743-6adf2e81ea31.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.0b5XGbJR1rGa2uIQmf2sL9BuJjz_6E8vhrEQTLEWcxE"
TIMEOUT_SECONDS = 120  # 2 minutes timeout
MAX_CHUNK_SIZE = 200   # Much smaller chunks (200 chars instead of 1000)
BATCH_SIZE = 5         # Process 5 chunks at a time
DELAY_BETWEEN_BATCHES = 2  # 2 seconds delay between batches
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
COLLECTION_NAME = "sconia_legal_documents"
EMBEDDING_SIZE = 1536

async def main():
    """Initialize Qdrant with Nigerian Constitution data."""
    logger.info("Starting Qdrant initialization...")
    
    # Initialize OpenAI
    openai.api_key = OPENAI_API_KEY
    
    # Initialize Qdrant client with longer timeout
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=TIMEOUT_SECONDS, prefer_grpc=False)
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            # Create collection
            logger.info(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=models.Distance.COSINE
                )
            )
        else:
            logger.info(f"Collection {COLLECTION_NAME} already exists")
        
        # Read the Nigerian Constitution from file
        constitution_path = os.path.join(os.path.dirname(__file__), "..", "constitution.txt")
        logger.info(f"Reading constitution from: {constitution_path}")
        
        with open(constitution_path, 'r', encoding='utf-8') as f:
            constitution_text = f.read()
        
        # Split into chunks (approximately 1000 characters each for better embeddings)
        def chunk_text(text, chunk_size=MAX_CHUNK_SIZE, overlap=50):
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                if end >= len(text):
                    chunks.append(text[start:])
                    break
                
                # Try to break at sentence or paragraph boundary
                chunk = text[start:end]
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                
                if last_period > start + chunk_size * 0.7:
                    end = start + last_period + 1
                elif last_newline > start + chunk_size * 0.7:
                    end = start + last_newline + 1
                
                chunks.append(text[start:end])
                start = end - overlap
            
            return chunks
        
        # Chunk the constitution
        chunks = chunk_text(constitution_text)
        logger.info(f"Split constitution into {len(chunks)} chunks")
        
        # Create constitutional texts for embedding
        constitutional_texts = []
        for i, chunk in enumerate(chunks):
            # Skip very short chunks
            if len(chunk.strip()) < 50:
                continue
                
            # Determine section based on content
            section = "general"
            title = f"Constitution Chunk {i+1}"
            
            if "CHAPTER I" in chunk.upper() or "GENERAL PROVISIONS" in chunk.upper():
                section = "chapter_i_general_provisions"
                title = "General Provisions"
            elif "CHAPTER II" in chunk.upper() or "FUNDAMENTAL OBJECTIVES" in chunk.upper():
                section = "chapter_ii_fundamental_objectives"
                title = "Fundamental Objectives"
            elif "CHAPTER III" in chunk.upper() or "CITIZENSHIP" in chunk.upper():
                section = "chapter_iii_citizenship"
                title = "Citizenship"
            elif "CHAPTER IV" in chunk.upper() or "FUNDAMENTAL RIGHTS" in chunk.upper():
                section = "chapter_iv_fundamental_rights"
                title = "Fundamental Rights"
            elif "PREAMBLE" in chunk.upper():
                section = "preamble"
                title = "Constitution Preamble"
            
            constitutional_texts.append({
                "id": i + 1,
                "text": chunk.strip(),
                "metadata": {
                    "document_type": "constitution",
                    "title": title,
                    "section": section,
                    "chunk_index": i + 1
                }
            })
        
        logger.info(f"Prepared {len(constitutional_texts)} constitutional text chunks for embedding")
        
        # Generate embeddings and store in Qdrant in small batches
        logger.info(f"Generating embeddings and storing in Qdrant in batches of {BATCH_SIZE}...")
        total_docs = len(constitutional_texts)
        
        for i in range(0, total_docs, BATCH_SIZE):
            batch = constitutional_texts[i:i + BATCH_SIZE]
            batch_points = []
            
            logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(total_docs + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} documents)")
            
            for doc in batch:
                try:
                    # Generate embedding using OpenAI
                    response = openai.embeddings.create(
                        model="text-embedding-ada-002",
                        input=doc["text"]
                    )
                    embedding = response.data[0].embedding
                    
                    # Create point for Qdrant
                    point = models.PointStruct(
                        id=doc["id"],
                        vector=embedding,
                        payload={
                            "text": doc["text"],
                            **doc["metadata"]
                        }
                    )
                    batch_points.append(point)
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc['id']}: {e}")
                    continue
            
            # Upsert batch to Qdrant
            if batch_points:
                try:
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch_points
                    )
                    logger.info(f"Successfully uploaded batch of {len(batch_points)} points")
                except Exception as e:
                    logger.error(f"Error uploading batch: {e}")
                    continue
            
            # Delay between batches to avoid overwhelming the services
            if i + BATCH_SIZE < total_docs:
                logger.info(f"Waiting {DELAY_BETWEEN_BATCHES} seconds before next batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        logger.info(f"Completed processing all {total_docs} documents")
        
        # Verify the collection
        collection_info = client.get_collection(COLLECTION_NAME)
        logger.info(f"Collection info: {collection_info}")
        
        logger.info("Qdrant initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
