"""
ChromaDB service for SCONIA.
Handles local embedding storage, retrieval, and semantic search operations.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import os
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class ChromaDBService:
    """Service for managing vector database operations with ChromaDB locally."""
    
    def __init__(self):
        """Initialize Chroma client and collection."""
        # Ensure the chromadb directory exists
        os.makedirs(settings.chromadb_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "sconia_legal_documents"
        self.collection = None
        
    async def initialize_collections(self):
        """Initialize Chroma collections for legal documents."""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
            
    async def store_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Store embeddings with associated text and metadata.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of text chunks
            metadata_list: List of metadata dictionaries
            
        Returns:
            List of point IDs
        """
        try:
            if self.collection is None:
                await self.initialize_collections()
                
            ids = []
            metadatas = []
            
            for i, metadata in enumerate(metadata_list):
                point_id = metadata.get("point_id") or str(uuid.uuid4())
                ids.append(point_id)
                
                # Format metadata to make sure all values are strings, ints, floats, or bools for Chroma
                formatted_metadata = {}
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        formatted_metadata[k] = v
                    elif v is None:
                        continue
                    else:
                        formatted_metadata[k] = str(v)
                
                # Include standard payload info
                formatted_metadata["document_id"] = metadata.get("document_id", "")
                formatted_metadata["document_type"] = metadata.get("document_type", "")
                formatted_metadata["chunk_index"] = metadata.get("chunk_index", i)
                
                metadatas.append(formatted_metadata)
                
            # Upsert into Chroma collection
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"Stored {len(ids)} embeddings in Chroma vector database")
            return ids
            
        except Exception as e:
            logger.error(f"Error storing embeddings in Chroma: {e}")
            raise
            
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        document_types: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score (cosine threshold)
            document_types: Filter by document types
            document_ids: Filter by specific document IDs
            
        Returns:
            List of search results with text, metadata, and scores
        """
        try:
            if self.collection is None:
                await self.initialize_collections()
                
            # Build filters
            where_clause = {}
            
            if document_types and len(document_types) > 0:
                if len(document_types) == 1:
                    where_clause["document_type"] = document_types[0]
                else:
                    where_clause["$or"] = [{"document_type": t} for t in document_types]
                    
            if document_ids and len(document_ids) > 0:
                id_filters = []
                for doc_id in document_ids:
                    id_filters.append({"document_id": doc_id})
                
                if where_clause:
                    # Combine with existing filters
                    current_where = where_clause.copy()
                    id_where = id_filters[0] if len(id_filters) == 1 else {"$or": id_filters}
                    where_clause = {"$and": [current_where, id_where]}
                else:
                    where_clause = id_filters[0] if len(id_filters) == 1 else {"$or": id_filters}
                    
            # Perform query
            query_args = {
                "query_embeddings": [query_embedding],
                "n_results": limit
            }
            if where_clause:
                query_args["where"] = where_clause
                
            query_results = self.collection.query(**query_args)
            
            results = []
            if not query_results or not query_results["ids"]:
                return results
                
            # Chroma returns lists of lists since it supports batch queries
            ids = query_results["ids"][0]
            distances = query_results["distances"][0] if "distances" in query_results and query_results["distances"] else [0.0] * len(ids)
            metadatas = query_results["metadatas"][0] if "metadatas" in query_results and query_results["metadatas"] else [{}] * len(ids)
            documents = query_results["documents"][0] if "documents" in query_results and query_results["documents"] else [""] * len(ids)
            
            for i in range(len(ids)):
                # Chroma's cosine distance is typically 1 - cosine_similarity (range 0 to 2)
                # We convert distance to similarity score: similarity = 1 - distance
                similarity_score = 1.0 - distances[i]
                
                # Apply score threshold
                if similarity_score < score_threshold:
                    continue
                    
                results.append({
                    "id": ids[i],
                    "text": documents[i],
                    "score": similarity_score,
                    "document_id": metadatas[i].get("document_id"),
                    "document_type": metadatas[i].get("document_type"),
                    "chunk_index": metadatas[i].get("chunk_index"),
                    "metadata": metadatas[i]
                })
                
            logger.info(f"Found {len(results)} similar documents in Chroma")
            return results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            raise
            
    async def delete_document_embeddings(self, document_id: str) -> bool:
        """Delete all embeddings for a specific document."""
        try:
            if self.collection is None:
                await self.initialize_collections()
                
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted Chroma embeddings for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting Chroma embeddings: {e}")
            return False
            
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection info/stats."""
        try:
            if self.collection is None:
                await self.initialize_collections()
                
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "vectors_count": count,
                "points_count": count,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting Chroma info: {e}")
            return {}
            
    async def search_by_document_id(
        self,
        document_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            if self.collection is None:
                await self.initialize_collections()
                
            get_results = self.collection.get(
                where={"document_id": document_id},
                limit=limit
            )
            
            results = []
            if not get_results or not get_results["ids"]:
                return results
                
            ids = get_results["ids"]
            metadatas = get_results["metadatas"] or [{}] * len(ids)
            documents = get_results["documents"] or [""] * len(ids)
            
            for i in range(len(ids)):
                results.append({
                    "id": ids[i],
                    "text": documents[i],
                    "document_id": metadatas[i].get("document_id"),
                    "document_type": metadatas[i].get("document_type"),
                    "chunk_index": metadatas[i].get("chunk_index", 0),
                    "metadata": metadatas[i]
                })
                
            # Sort by chunk index
            results.sort(key=lambda x: x["chunk_index"])
            return results
            
        except Exception as e:
            logger.error(f"Error listing Chroma document chunks: {e}")
            return []


# Global instance
chromadb_service = ChromaDBService()
