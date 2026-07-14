"""
Advanced search service for SCONIA.
Implements faceted search, filtering, and search suggestions.
"""
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from collections import defaultdict, Counter
import re

from app.services.vector_db import vector_db_service
from app.services.embeddings import embedding_service
from app.models.legal import (
    Judge, ConstitutionalProvision, SupremeCourtCase, 
    FeeSchedule, Procedure, RequiredForm
)

logger = logging.getLogger(__name__)


class AdvancedSearchService:
    """Advanced search service with faceted search and filtering."""
    
    def __init__(self):
        """Initialize advanced search service."""
        self.search_history = []
        self.popular_queries = Counter()
        
        # Search facets configuration
        self.facets_config = {
            "document_type": {
                "field": "document_type",
                "display_name": "Document Type",
                "values": ["constitution", "case", "procedure", "judge", "fee", "form"]
            },
            "year": {
                "field": "year",
                "display_name": "Year",
                "type": "range"
            },
            "category": {
                "field": "category",
                "display_name": "Category",
                "type": "dynamic"
            },
            "status": {
                "field": "status",
                "display_name": "Status",
                "type": "dynamic"
            }
        }
    
    async def faceted_search(
        self,
        query: str,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        facets: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Perform faceted search across all legal content.
        
        Args:
            query: Search query
            db: Database session
            filters: Applied filters
            facets: Requested facets
            limit: Maximum results
            offset: Results offset
            
        Returns:
            Search results with facets
        """
        try:
            filters = filters or {}
            facets = facets or list(self.facets_config.keys())
            
            # Perform vector search
            vector_results = []
            if query.strip():
                query_embedding = await embedding_service.generate_query_embedding(query)
                
                # Apply document type filter for vector search
                doc_types = filters.get("document_type")
                vector_results = await vector_db_service.search_similar(
                    query_embedding=query_embedding,
                    limit=limit * 2,  # Get more for filtering
                    document_types=doc_types if doc_types else None
                )
            
            # Perform structured search
            structured_results = await self._structured_search(query, db, filters, limit, offset)
            
            # Combine and rank results
            combined_results = await self._combine_and_rank_results(
                vector_results, structured_results, query, filters
            )
            
            # Apply pagination
            paginated_results = combined_results[offset:offset + limit]
            
            # Generate facets
            search_facets = await self._generate_facets(
                query, db, filters, facets, combined_results
            )
            
            # Track search
            self._track_search(query, filters, len(combined_results))
            
            return {
                "query": query,
                "results": paginated_results,
                "total_count": len(combined_results),
                "offset": offset,
                "limit": limit,
                "facets": search_facets,
                "applied_filters": filters,
                "search_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in faceted search: {e}")
            return {
                "query": query,
                "results": [],
                "total_count": 0,
                "offset": offset,
                "limit": limit,
                "facets": {},
                "applied_filters": filters,
                "error": str(e)
            }
    
    async def _structured_search(
        self,
        query: str,
        db: AsyncSession,
        filters: Dict[str, Any],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Perform structured search across database tables."""
        results = []
        
        try:
            # Search judges
            if not filters.get("document_type") or "judge" in filters.get("document_type", []):
                judges = await self._search_judges(query, db, filters)
                results.extend(judges)
            
            # Search constitutional provisions
            if not filters.get("document_type") or "constitution" in filters.get("document_type", []):
                provisions = await self._search_constitution(query, db, filters)
                results.extend(provisions)
            
            # Search cases
            if not filters.get("document_type") or "case" in filters.get("document_type", []):
                cases = await self._search_cases(query, db, filters)
                results.extend(cases)
            
            # Search procedures
            if not filters.get("document_type") or "procedure" in filters.get("document_type", []):
                procedures = await self._search_procedures(query, db, filters)
                results.extend(procedures)
            
            # Search fees
            if not filters.get("document_type") or "fee" in filters.get("document_type", []):
                fees = await self._search_fees(query, db, filters)
                results.extend(fees)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in structured search: {e}")
            return []
    
    async def _search_judges(self, query: str, db: AsyncSession, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search judges table."""
        try:
            query_obj = select(Judge).where(Judge.is_active == True)
            
            if query:
                query_obj = query_obj.where(
                    or_(
                        Judge.full_name.ilike(f'%{query}%'),
                        Judge.title.ilike(f'%{query}%'),
                        Judge.background_summary.ilike(f'%{query}%')
                    )
                )
            
            result = await db.execute(query_obj.limit(10))
            judges = result.scalars().all()
            
            return [
                {
                    "id": f"judge_{judge.id}",
                    "title": judge.full_name,
                    "content": judge.background_summary or judge.title,
                    "document_type": "judge",
                    "url": f"/api/v1/judges/{judge.id}",
                    "metadata": {
                        "is_chief_justice": judge.is_chief_justice,
                        "appointment_date": judge.appointment_date.isoformat() if judge.appointment_date else None
                    },
                    "relevance_score": 0.9
                }
                for judge in judges
            ]
            
        except Exception as e:
            logger.error(f"Error searching judges: {e}")
            return []
    
    async def _search_constitution(self, query: str, db: AsyncSession, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search constitutional provisions."""
        try:
            query_obj = select(ConstitutionalProvision).where(ConstitutionalProvision.is_active == True)
            
            if query:
                query_obj = query_obj.where(
                    or_(
                        ConstitutionalProvision.title.ilike(f'%{query}%'),
                        ConstitutionalProvision.content.ilike(f'%{query}%'),
                        ConstitutionalProvision.section.ilike(f'%{query}%')
                    )
                )
            
            result = await db.execute(query_obj.limit(10))
            provisions = result.scalars().all()
            
            return [
                {
                    "id": f"constitution_{provision.id}",
                    "title": f"{provision.chapter} Section {provision.section}: {provision.title}",
                    "content": provision.content[:300] + "..." if len(provision.content) > 300 else provision.content,
                    "document_type": "constitution",
                    "url": f"/api/v1/constitution/section/{provision.section}",
                    "metadata": {
                        "chapter": provision.chapter,
                        "section": provision.section,
                        "keywords": provision.keywords
                    },
                    "relevance_score": 0.95
                }
                for provision in provisions
            ]
            
        except Exception as e:
            logger.error(f"Error searching constitution: {e}")
            return []
    
    async def _search_cases(self, query: str, db: AsyncSession, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Supreme Court cases."""
        try:
            query_obj = select(SupremeCourtCase).where(SupremeCourtCase.is_active == True)
            
            if query:
                query_obj = query_obj.where(
                    or_(
                        SupremeCourtCase.case_title.ilike(f'%{query}%'),
                        SupremeCourtCase.case_number.ilike(f'%{query}%'),
                        SupremeCourtCase.case_summary.ilike(f'%{query}%')
                    )
                )
            
            # Apply year filter
            if filters.get("year"):
                year = filters["year"]
                query_obj = query_obj.where(func.extract('year', SupremeCourtCase.judgment_date) == year)
            
            result = await db.execute(query_obj.limit(10))
            cases = result.scalars().all()
            
            return [
                {
                    "id": f"case_{case.id}",
                    "title": f"{case.case_number}: {case.case_title}",
                    "content": case.case_summary[:300] + "..." if case.case_summary and len(case.case_summary) > 300 else case.case_summary,
                    "document_type": "case",
                    "url": f"/api/v1/cases/{case.id}",
                    "metadata": {
                        "case_number": case.case_number,
                        "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
                        "legal_principles": case.legal_principles
                    },
                    "relevance_score": 0.9
                }
                for case in cases
            ]
            
        except Exception as e:
            logger.error(f"Error searching cases: {e}")
            return []
    
    async def _search_procedures(self, query: str, db: AsyncSession, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search procedures."""
        try:
            query_obj = select(Procedure).where(Procedure.is_active == True)
            
            if query:
                query_obj = query_obj.where(
                    or_(
                        Procedure.procedure_name.ilike(f'%{query}%'),
                        Procedure.category.ilike(f'%{query}%')
                    )
                )
            
            result = await db.execute(query_obj.limit(10))
            procedures = result.scalars().all()
            
            return [
                {
                    "id": f"procedure_{procedure.id}",
                    "title": procedure.procedure_name,
                    "content": f"Category: {procedure.category}. Timeline: {procedure.estimated_timeline}",
                    "document_type": "procedure",
                    "url": f"/api/v1/procedures/{procedure.id}",
                    "metadata": {
                        "category": procedure.category,
                        "estimated_timeline": procedure.estimated_timeline
                    },
                    "relevance_score": 0.85
                }
                for procedure in procedures
            ]
            
        except Exception as e:
            logger.error(f"Error searching procedures: {e}")
            return []
    
    async def _search_fees(self, query: str, db: AsyncSession, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search fee schedules."""
        try:
            query_obj = select(FeeSchedule).where(FeeSchedule.is_active == True)
            
            if query:
                query_obj = query_obj.where(
                    or_(
                        FeeSchedule.service_type.ilike(f'%{query}%'),
                        FeeSchedule.description.ilike(f'%{query}%')
                    )
                )
            
            result = await db.execute(query_obj.limit(10))
            fees = result.scalars().all()
            
            return [
                {
                    "id": f"fee_{fee.id}",
                    "title": f"{fee.service_type} - {fee.case_category or 'General'}",
                    "content": f"Fee: ₦{fee.fee_amount:,.2f}. {fee.description}",
                    "document_type": "fee",
                    "url": f"/api/v1/fees/{fee.id}",
                    "metadata": {
                        "service_type": fee.service_type,
                        "fee_amount": float(fee.fee_amount) if fee.fee_amount else 0
                    },
                    "relevance_score": 0.8
                }
                for fee in fees
            ]
            
        except Exception as e:
            logger.error(f"Error searching fees: {e}")
            return []
    
    async def _combine_and_rank_results(
        self,
        vector_results: List[Dict[str, Any]],
        structured_results: List[Dict[str, Any]],
        query: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Combine and rank search results."""
        try:
            all_results = []
            seen_ids = set()
            
            # Add vector results
            for result in vector_results:
                result_id = result.get("document_id", result.get("id"))
                if result_id not in seen_ids:
                    all_results.append({
                        "id": result_id,
                        "title": result.get("title", "Legal Document"),
                        "content": result.get("text", ""),
                        "document_type": result.get("document_type", "unknown"),
                        "relevance_score": result.get("score", 0.0),
                        "source": "vector",
                        "metadata": result.get("metadata", {})
                    })
                    seen_ids.add(result_id)
            
            # Add structured results
            for result in structured_results:
                result_id = result.get("id")
                if result_id not in seen_ids:
                    all_results.append({
                        **result,
                        "source": "structured"
                    })
                    seen_ids.add(result_id)
            
            # Sort by relevance score
            all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error combining results: {e}")
            return []
    
    async def _generate_facets(
        self,
        query: str,
        db: AsyncSession,
        filters: Dict[str, Any],
        requested_facets: List[str],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate facets for search results."""
        try:
            facets = {}
            
            # Document type facet
            if "document_type" in requested_facets:
                doc_type_counts = Counter(result.get("document_type", "unknown") for result in results)
                facets["document_type"] = {
                    "display_name": "Document Type",
                    "values": [
                        {"value": doc_type, "count": count, "selected": doc_type in filters.get("document_type", [])}
                        for doc_type, count in doc_type_counts.most_common()
                    ]
                }
            
            # Year facet (for cases)
            if "year" in requested_facets:
                years = []
                for result in results:
                    if result.get("document_type") == "case":
                        judgment_date = result.get("metadata", {}).get("judgment_date")
                        if judgment_date:
                            try:
                                year = datetime.fromisoformat(judgment_date).year
                                years.append(year)
                            except:
                                pass
                
                year_counts = Counter(years)
                facets["year"] = {
                    "display_name": "Year",
                    "type": "range",
                    "values": [
                        {"value": year, "count": count, "selected": year == filters.get("year")}
                        for year, count in sorted(year_counts.items(), reverse=True)
                    ]
                }
            
            return facets
            
        except Exception as e:
            logger.error(f"Error generating facets: {e}")
            return {}
    
    def _track_search(self, query: str, filters: Dict[str, Any], result_count: int):
        """Track search for analytics."""
        try:
            search_record = {
                "query": query,
                "filters": filters,
                "result_count": result_count,
                "timestamp": datetime.utcnow()
            }
            
            self.search_history.append(search_record)
            self.popular_queries[query.lower()] += 1
            
            # Keep only recent history
            if len(self.search_history) > 1000:
                self.search_history = self.search_history[-500:]
                
        except Exception as e:
            logger.error(f"Error tracking search: {e}")
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = []
            partial_lower = partial_query.lower()
            
            # Get suggestions from popular queries
            for query, count in self.popular_queries.most_common(50):
                if partial_lower in query and query not in suggestions:
                    suggestions.append(query)
                    if len(suggestions) >= limit:
                        break
            
            # Add predefined suggestions
            predefined = [
                "fundamental rights",
                "Chief Justice of Nigeria",
                "Supreme Court procedures",
                "constitutional provisions",
                "landmark cases",
                "court fees",
                "filing requirements"
            ]
            
            for suggestion in predefined:
                if partial_lower in suggestion.lower() and suggestion not in suggestions:
                    suggestions.append(suggestion)
                    if len(suggestions) >= limit:
                        break
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []


# Global advanced search service instance
advanced_search_service = AdvancedSearchService()
