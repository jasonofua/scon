"""
Embedding generation service for SCONIA.
Handles text embedding generation using Google Gemini and sentence-transformers.
"""
from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
from google import genai
import numpy as np
from functools import lru_cache
import hashlib
import json

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings."""

    def __init__(self):
        """Initialize embedding models and clients."""
        # Initialize Google GenAI client
        self.gemini_client = None
        try:
            if settings.gemini_api_key:
                self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
            else:
                # Try loading from environment automatically if not explicitly configured in settings
                self.gemini_client = genai.Client()
        except ValueError:
            logger.warning("Google GenAI client could not be initialized in EmbeddingService because GEMINI_API_KEY is missing.")
            self.gemini_client = None
            
        self.gemini_model = settings.gemini_embedding_model
        self._sentence_transformer = None

        # Cache for embeddings to avoid regenerating
        self._embedding_cache = {}

    @property
    def sentence_transformer(self):
        """Lazy load sentence transformer model."""
        if self._sentence_transformer is None:
            try:
                # Import here to avoid loading heavy dependencies at startup
                from sentence_transformers import SentenceTransformer
                self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer model: {e}")
                self._sentence_transformer = None
        return self._sentence_transformer

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model combination."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{model}:{text_hash}"
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count in text (fallback helper)."""
        # Roughly estimated for Gemini context models (chars / 4 is a common rule of thumb, or words * 1.3)
        return int(len(text.split()) * 1.3)
    
    def chunk_text(
        self,
        text: str,
        max_tokens: int = 8000,
        overlap_tokens: int = 200,
        preserve_sentences: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces for embedding.
        
        Args:
            text: Input text to chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between chunks
            preserve_sentences: Try to preserve sentence boundaries
            
        Returns:
            List of chunks with metadata
        """
        try:
            # Split into sentences if preserving sentence boundaries
            if preserve_sentences:
                sentences = text.split('. ')
                sentences = [s + '.' if not s.endswith('.') else s for s in sentences]
            else:
                # Simple word-based splitting
                words = text.split()
                sentences = [' '.join(words[i:i+50]) for i in range(0, len(words), 50)]
            
            chunks = []
            current_chunk = ""
            current_tokens = 0
            chunk_index = 0
            
            for sentence in sentences:
                sentence_tokens = self.count_tokens(sentence)
                
                # If adding this sentence would exceed max tokens, start new chunk
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Add overlap from previous chunk
                    overlap_text = ""
                    if chunks and overlap_tokens > 0:
                        prev_words = current_chunk.split()
                        overlap_words = prev_words[-overlap_tokens:] if len(prev_words) > overlap_tokens else prev_words
                        overlap_text = ' '.join(overlap_words) + " "
                    
                    chunks.append({
                        "text": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "token_count": current_tokens,
                        "start_overlap": len(overlap_text) > 0
                    })
                    
                    current_chunk = overlap_text + sentence
                    current_tokens = self.count_tokens(current_chunk)
                    chunk_index += 1
                else:
                    current_chunk += (" " if current_chunk else "") + sentence
                    current_tokens += sentence_tokens
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "token_count": current_tokens,
                    "start_overlap": False
                })
            
            logger.info(f"Chunked text into {len(chunks)} pieces")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            # Fallback: return original text as single chunk
            return [{
                "text": text,
                "chunk_index": 0,
                "token_count": self.count_tokens(text),
                "start_overlap": False
            }]
    
    async def generate_gemini_embedding(self, text: str) -> List[float]:
        """Generate embedding using Google Gemini API."""
        try:
            # Check cache first
            cache_key = self._get_cache_key(text, self.gemini_model)
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]
            
            # Generate embedding asynchronously using google-genai SDK
            response = await self.gemini_client.aio.models.embed_content(
                model=self.gemini_model,
                contents=text
            )
            
            # Extract embedding values (list of floats)
            embedding = response.embeddings[0].values
            
            # Cache the result
            self._embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {e}")
            raise
    
    def generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local sentence transformer model."""
        try:
            model = self.sentence_transformer
 
            if model is None:
                raise Exception("Local model not available")
 
            # Check cache first
            cache_key = self._get_cache_key(text, "local")
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]
 
            # Generate embedding
            embedding = model.encode(text).tolist()
 
            # Cache the result
            self._embedding_cache[cache_key] = embedding
 
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating local embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        use_gemini: bool = True,
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            use_gemini: Whether to use Gemini API or local model
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        try:
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = []
                
                if use_gemini and self.gemini_client:
                    # Process batch with Gemini
                    # Gemini embed_content supports passing a list directly
                    response = await self.gemini_client.aio.models.embed_content(
                        model=self.gemini_model,
                        contents=batch
                    )
                    batch_embeddings = [emb.values for emb in response.embeddings]
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.1)
                else:
                    # Process batch with local model
                    model = self.sentence_transformer
 
                    if model is not None:
                        batch_embeddings = model.encode(batch).tolist()
                    else:
                        raise Exception("No embedding model available")
                
                embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    async def embed_document(
        self,
        text: str,
        document_id: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        use_gemini: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process and embed a complete document.
        
        Args:
            text: Document text
            document_id: Unique document identifier
            document_type: Type of document (constitution, case, etc.)
            metadata: Additional metadata
            use_gemini: Whether to use Gemini API
            
        Returns:
            List of embedding records with metadata
        """
        try:
            # Chunk the document
            chunks = self.chunk_text(text)
            
            # Extract texts for embedding
            chunk_texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self.generate_embeddings_batch(
                chunk_texts,
                use_gemini=use_gemini
            )
            
            # Combine embeddings with metadata
            embedding_records = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                record = {
                    "embedding": embedding,
                    "text": chunk["text"],
                    "metadata": {
                        "document_id": document_id,
                        "document_type": document_type,
                        "chunk_index": chunk["chunk_index"],
                        "token_count": chunk["token_count"],
                        "start_overlap": chunk["start_overlap"],
                        **(metadata or {})
                    }
                }
                embedding_records.append(record)
            
            logger.info(f"Embedded document {document_id} into {len(embedding_records)} chunks")
            return embedding_records
            
        except Exception as e:
            logger.error(f"Error embedding document: {e}")
            raise
    
    async def generate_query_embedding(
        self,
        query: str,
        use_gemini: bool = True
    ) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            use_gemini: Whether to use Gemini API
            
        Returns:
            Query embedding vector
        """
        try:
            if use_gemini and self.gemini_client:
                return await self.generate_gemini_embedding(query)
            else:
                return self.generate_local_embedding(query)
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            # Fallback to local model if Gemini fails
            if use_gemini:
                logger.info("Falling back to local model")
                return self.generate_local_embedding(query)
            raise
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._embedding_cache),
            "gemini_cached": sum(1 for k in self._embedding_cache.keys() if k.startswith(self.gemini_model)),
            "local_cached": sum(1 for k in self._embedding_cache.keys() if k.startswith("local"))
        }


# Global embedding service instance
embedding_service = EmbeddingService()
