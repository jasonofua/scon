"""
Vector database service for SCONIA.
Handles embedding storage, retrieval, and semantic search operations using Qdrant or ChromaDB.
"""
from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    PayloadSchemaType,
)
import uuid
from datetime import datetime, timezone

from app.config import settings
from app.services.chromadb_service import chromadb_service

logger = logging.getLogger(__name__)


class VectorDBService:
    """Service for managing vector database operations with Qdrant or ChromaDB."""

    def __init__(self):
        """Initialize clients and collections."""
        self.db_type = settings.vector_db_type

        # Initialize Qdrant only if selected — lazy connection avoids
        # crashing at import time when env vars are not yet set.
        self.client: Optional[QdrantClient] = None
        if self.db_type == "qdrant":
            try:
                self.client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                    timeout=30,
                )
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant at init: {e}")

        self.collection_name = "sconia_legal_documents"
        self.embedding_size = 3072  # gemini-embedding-001 dimension

    async def initialize_collections(self):
        """Initialize collections for legal documents."""
        if self.db_type == "chromadb":
            return await chromadb_service.initialize_collections()

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with vector configuration
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

            # Create indexes for better performance
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            raise

    async def _create_indexes(self):
        """Create indexes for efficient filtering in Qdrant."""
        if self.db_type == "chromadb" or not self.client:
            return

        try:
            # Create payload indexes for filtering.
            # Use PayloadSchemaType enum — the concrete *IndexParams classes
            # require a mandatory `type` field that varies by Qdrant version.
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_type",
                field_schema=PayloadSchemaType.KEYWORD,
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="created_at",
                field_schema=PayloadSchemaType.INTEGER,
            )

            logger.info("Created payload indexes")

        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    async def store_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
    ) -> List[str]:
        """Store embeddings with associated text and metadata."""
        if self.db_type == "chromadb":
            return await chromadb_service.store_embeddings(embeddings, texts, metadata_list)

        try:
            points = []
            point_ids = []

            for i, (embedding, text, metadata) in enumerate(zip(embeddings, texts, metadata_list)):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)

                # Prepare payload with text and metadata.
                # Use timezone-aware UTC timestamp (datetime.utcnow() is deprecated).
                payload = {
                    "text": text,
                    "document_id": metadata.get("document_id"),
                    "document_type": metadata.get("document_type"),
                    "chunk_index": metadata.get("chunk_index", i),
                    "token_count": metadata.get("token_count"),
                    "created_at": int(datetime.now(timezone.utc).timestamp()),
                    **metadata,  # Include all additional metadata
                }

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(f"Stored {len(points)} embeddings in vector database")
            return point_ids

        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            raise

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        document_types: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        if self.db_type == "chromadb":
            return await chromadb_service.search_similar(
                query_embedding, limit, score_threshold, document_types, document_ids
            )

        try:
            # Build filter conditions.
            # MatchValue is for a single value; MatchAny handles lists.
            filter_conditions = []

            if document_types:
                filter_conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchAny(any=document_types),
                    )
                )

            if document_ids:
                filter_conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids),
                    )
                )

            # Create filter if conditions exist
            query_filter = Filter(must=filter_conditions) if filter_conditions else None

            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Format results
            results = []
            for result in search_results:
                results.append(
                    {
                        "id": result.id,
                        "text": result.payload.get("text", ""),
                        "score": result.score,
                        "document_id": result.payload.get("document_id"),
                        "document_type": result.payload.get("document_type"),
                        "chunk_index": result.payload.get("chunk_index"),
                        "metadata": {
                            k: v
                            for k, v in result.payload.items()
                            if k not in ["text", "document_id", "document_type", "chunk_index"]
                        },
                    }
                )

            logger.info(f"Found {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            raise

    async def delete_document_embeddings(self, document_id: str) -> bool:
        """Delete all embeddings for a specific document."""
        if self.db_type == "chromadb":
            return await chromadb_service.delete_document_embeddings(document_id)

        try:
            # Delete points with matching document_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )

            logger.info(f"Deleted embeddings for document: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document embeddings: {e}")
            return False

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        if self.db_type == "chromadb":
            return await chromadb_service.get_collection_info()

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    async def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        document_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search."""
        try:
            # Perform semantic search — get more results for reranking
            semantic_results = await self.search_similar(
                query_embedding=query_embedding,
                limit=limit * 2,
                score_threshold=0.0,  # No threshold during reranking; apply after
                document_types=document_types,
            )

            # Simple keyword matching on top of semantic results
            query_terms = query_text.lower().split()
            combined_results = []

            for result in semantic_results:
                text_lower = result["text"].lower()
                keyword_score = (
                    sum(1 for term in query_terms if term in text_lower) / len(query_terms)
                    if query_terms
                    else 0.0
                )

                combined_score = (
                    semantic_weight * result["score"] + keyword_weight * keyword_score
                )
                combined_results.append(
                    {
                        **result,
                        "keyword_score": keyword_score,
                        "combined_score": combined_score,
                    }
                )

            # Sort by combined score and return top results
            combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
            return combined_results[:limit]

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to plain semantic search with all required kwargs
            return await self.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=0.7,
                document_types=document_types,
            )

    async def search_by_document_id(
        self,
        document_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        if self.db_type == "chromadb":
            return await chromadb_service.search_by_document_id(document_id, limit)

        try:
            # Use scroll to get all points for the document
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
            )

            results = []
            for point in scroll_result[0]:
                payload = point.payload
                results.append(
                    {
                        "id": point.id,
                        "text": payload.get("text", ""),
                        "document_id": payload.get("document_id"),
                        "document_type": payload.get("document_type"),
                        "chunk_index": payload.get("chunk_index", 0),
                        "metadata": payload,
                    }
                )

            # Sort by chunk index
            results.sort(key=lambda x: x["chunk_index"])
            return results

        except Exception as e:
            logger.error(f"Error searching by document ID {document_id}: {e}")
            return []


# Global vector database service instance
vector_db_service = VectorDBService()
