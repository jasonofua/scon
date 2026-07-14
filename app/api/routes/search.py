"""
Search API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.database import get_async_db
from app.services.rag import rag_service
from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from app.models.legal import SupremeCourtCase, Procedure
from sqlalchemy import func

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/semantic")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform semantic search across legal documents.
    """
    try:
        # Try vector database first
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Search vector database
            results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                document_types=document_types
            )
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "search_type": "vector"
            }
            
        except Exception as vector_error:
            logger.warning(f"Vector search failed, falling back to database search: {vector_error}")
            
            # Fallback to database text search
            from sqlalchemy import text
            from app.models.legal import LegalDocument
            
            # Build search query with parameterized queries for safety
            search_terms = [term.strip() for term in query.lower().split() if term.strip()]
            
            if not search_terms:
                return {
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "search_type": "database_fallback",
                    "message": "No search terms provided"
                }
            
            # Create ILIKE conditions for partial matching
            conditions = []
            params = {}
            
            for i, term in enumerate(search_terms):
                term_param = f"term_{i}"
                conditions.append(f"(LOWER(title) ILIKE :title_{term_param} OR LOWER(content) ILIKE :content_{term_param})")
                params[f"title_{term_param}"] = f"%{term}%"
                params[f"content_{term_param}"] = f"%{term}%"
            
            where_clause = " AND ".join(conditions)
            
            # Add document type filter if specified
            if document_types:
                type_params = []
                for i, dtype in enumerate(document_types):
                    type_param = f"dtype_{i}"
                    type_params.append(f":type_{type_param}")
                    params[f"type_{type_param}"] = dtype
                where_clause += f" AND document_type IN ({', '.join(type_params)})"
            
            # Execute search query
            query_text = f"""
                SELECT id, title, content, document_type, source, created_at
                FROM legal_documents 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit_param
            """
            params["limit_param"] = limit
            
            result = await db.execute(text(query_text), params)
            rows = result.fetchall()
            
            # Format results
            results = []
            for row in rows:
                # Calculate a simple relevance score based on term matches
                content_lower = (row.content or "").lower()
                title_lower = (row.title or "").lower()
                
                score = 0.0
                for term in search_terms:
                    # Title matches are weighted more heavily
                    score += title_lower.count(term) * 0.3
                    score += content_lower.count(term) * 0.1
                
                # Normalize score
                score = min(score, 1.0)
                
                # Create preview (first 200 chars)
                preview = row.content[:200] + "..." if row.content and len(row.content) > 200 else (row.content or "")
                
                results.append({
                    "document_id": row.id,
                    "title": row.title or "Untitled",
                    "content": preview,
                    "document_type": row.document_type or "unknown",
                    "source": row.source or "Unknown",
                    "score": score,
                    "metadata": {
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "search_method": "database_fallback"
                    }
                })
            
            # Sort by score
            results = sorted(results, key=lambda x: x["score"], reverse=True)
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "search_type": "database_fallback",
                "message": "Using database search (vector search temporarily unavailable)"
            }
        
    except Exception as e:
        logger.error(f"All search methods failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/hybrid")
async def hybrid_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for semantic search"),
    keyword_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for keyword search"),
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform hybrid search combining semantic and keyword search.
    """
    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_query_embedding(query)
        
        # Perform hybrid search
        results = await vector_db_service.hybrid_search(
            query_embedding=query_embedding,
            query_text=query,
            limit=limit,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            document_types=document_types
        )
        
        return {
            "query": query,
            "search_type": "hybrid",
            "weights": {
                "semantic": semantic_weight,
                "keyword": keyword_weight
            },
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/context")
async def get_search_context(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(10, ge=1, le=20, description="Maximum results for context"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get search context using RAG pipeline (same as used in chat).
    """
    try:
        context, sources = await rag_service.retrieve_context(
            query=query,
            db=db,
            max_results=max_results
        )
        
        return {
            "query": query,
            "context": context,
            "sources": sources,
            "source_count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Context retrieval failed")


@router.get("/faceted")
async def faceted_search(
    query: str = Query(..., description="Search query"),
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    year: Optional[int] = Query(None, description="Filter by year"),
    category: Optional[str] = Query(None, description="Filter by category"),
    facets: Optional[List[str]] = Query(None, description="Requested facets"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Perform faceted search with filtering and facet generation.
    """
    try:
        from app.services.advanced_search import advanced_search_service

        # Build filters
        filters = {}
        if document_types:
            filters["document_type"] = document_types
        if year:
            filters["year"] = year
        if category:
            filters["category"] = category

        # Perform faceted search
        results = await advanced_search_service.faceted_search(
            query=query,
            db=db,
            filters=filters,
            facets=facets,
            limit=limit,
            offset=offset
        )

        return results

    except Exception as e:
        logger.error(f"Faceted search error: {e}")
        raise HTTPException(status_code=500, detail="Faceted search failed")


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial query for suggestions"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions")
):
    """
    Get intelligent search suggestions based on partial query.
    """
    try:
        from app.services.advanced_search import advanced_search_service

        suggestions = await advanced_search_service.get_search_suggestions(query, limit)

        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }

    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.get("/filters")
async def get_available_filters(db: AsyncSession = Depends(get_async_db)):
    """
    Get available filter options for search.
    """
    try:
        # Get document types
        document_types = ["constitution", "case", "procedure", "judge", "fee", "form"]

        # Get available years from cases
        result = await db.execute(
            select(func.extract('year', SupremeCourtCase.judgment_date).label('year'))
            .where(SupremeCourtCase.is_active == True)
            .distinct()
            .order_by('year')
        )
        years = [int(row[0]) for row in result.fetchall() if row[0]]

        # Get categories from procedures
        result = await db.execute(
            select(Procedure.category)
            .where(Procedure.is_active == True)
            .distinct()
        )
        categories = [row[0] for row in result.fetchall() if row[0]]

        return {
            "filters": {
                "document_types": {
                    "display_name": "Document Type",
                    "options": document_types
                },
                "years": {
                    "display_name": "Year",
                    "options": years,
                    "type": "range"
                },
                "categories": {
                    "display_name": "Category",
                    "options": categories
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get filter options")


@router.get("/stats")
async def get_search_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get search and vector database statistics.
    """
    try:
        # Get vector database info
        vector_info = await vector_db_service.get_collection_info()
        
        # Get embedding service stats
        embedding_stats = embedding_service.get_cache_stats()
        
        return {
            "vector_database": vector_info,
            "embedding_cache": embedding_stats,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
