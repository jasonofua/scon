"""
Retrieval-Augmented Generation (RAG) service for SCONIA.
Implements semantic search, context ranking, and response generation.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.services.vector_db import vector_db_service
from app.services.embeddings import embedding_service
from app.services.cache import cache_service
from app.models.legal import Judge, ConstitutionalProvision, SupremeCourtCase, FeeSchedule, Procedure
from app.models.embeddings import SearchQuery
from app.config import settings, DOCUMENT_CATEGORIES

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for legal queries."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.max_context_length = 8000  # Maximum tokens for context
        self.min_relevance_score = 0.7
        self.max_retrieved_docs = 10
        
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of legal query."""
        query_lower = query.lower()
        
        # Constitutional queries
        if any(term in query_lower for term in ['constitution', 'fundamental rights', 'chapter', 'section']):
            return 'constitutional_query'
        
        # Judge information
        if any(term in query_lower for term in ['judge', 'justice', 'chief justice', 'court personnel']):
            return 'judge_information'
        
        # Case law queries
        if any(term in query_lower for term in ['case', 'precedent', 'judgment', 'ruling', 'appeal']):
            return 'case_law'
        
        # Procedural queries
        if any(term in query_lower for term in ['procedure', 'filing', 'process', 'how to', 'steps']):
            return 'procedural_information'
        
        # Fee queries
        if any(term in query_lower for term in ['fee', 'cost', 'payment', 'charge', 'amount']):
            return 'fee_calculation'
        
        # Court schedule
        if any(term in query_lower for term in ['schedule', 'session', 'calendar', 'when', 'time']):
            return 'court_schedule'
        
        return 'general_information'
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract legal entities from query."""
        entities = {
            'sections': [],
            'chapters': [],
            'case_numbers': [],
            'judge_names': [],
            'years': []
        }
        
        # Extract constitutional sections
        sections = re.findall(r'section\s+(\d+)', query, re.IGNORECASE)
        entities['sections'] = sections
        
        # Extract chapters
        chapters = re.findall(r'chapter\s+([IVX]+|\d+)', query, re.IGNORECASE)
        entities['chapters'] = chapters
        
        # Extract years
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        entities['years'] = years
        
        # Extract potential judge names (capitalized words after "Justice")
        judge_names = re.findall(r'Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', query)
        entities['judge_names'] = judge_names
        
        return entities
    
    async def _get_structured_data(
        self,
        query_type: str,
        entities: Dict[str, List[str]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Retrieve structured data from database based on query type and entities."""
        structured_results = []
        
        try:
            if query_type == 'judge_information':
                # Query judges
                query_obj = select(Judge).where(Judge.is_active == True)
                
                if entities['judge_names']:
                    # Search for specific judges
                    name_conditions = []
                    for name in entities['judge_names']:
                        name_conditions.append(Judge.full_name.ilike(f'%{name}%'))
                    query_obj = query_obj.where(or_(*name_conditions))
                
                result = await db.execute(query_obj.limit(5))
                judges = result.scalars().all()
                
                for judge in judges:
                    structured_results.append({
                        'type': 'judge',
                        'title': f"Justice {judge.full_name}",
                        'content': f"{judge.title} - {judge.background_summary or 'Supreme Court Justice'}",
                        'metadata': {
                            'appointment_date': judge.appointment_date.isoformat() if judge.appointment_date else None,
                            'is_chief_justice': judge.is_chief_justice
                        }
                    })
            
            elif query_type == 'constitutional_query':
                # Query constitutional provisions
                query_obj = select(ConstitutionalProvision).where(ConstitutionalProvision.is_active == True)
                
                if entities['sections']:
                    section_conditions = []
                    for section in entities['sections']:
                        section_conditions.append(ConstitutionalProvision.section == section)
                    query_obj = query_obj.where(or_(*section_conditions))
                
                if entities['chapters']:
                    chapter_conditions = []
                    for chapter in entities['chapters']:
                        chapter_conditions.append(ConstitutionalProvision.chapter.ilike(f'%{chapter}%'))
                    query_obj = query_obj.where(or_(*chapter_conditions))
                
                result = await db.execute(query_obj.limit(5))
                provisions = result.scalars().all()
                
                for provision in provisions:
                    structured_results.append({
                        'type': 'constitution',
                        'title': f"{provision.chapter} Section {provision.section}: {provision.title}",
                        'content': provision.content,
                        'metadata': {
                            'chapter': provision.chapter,
                            'section': provision.section,
                            'keywords': provision.keywords
                        }
                    })
            
            elif query_type == 'fee_calculation':
                # Query fee schedules
                result = await db.execute(
                    select(FeeSchedule)
                    .where(FeeSchedule.is_active == True)
                    .limit(10)
                )
                fees = result.scalars().all()
                
                for fee in fees:
                    structured_results.append({
                        'type': 'fee',
                        'title': f"{fee.service_type} - {fee.case_category or 'General'}",
                        'content': f"Fee: ₦{fee.fee_amount:,.2f} - {fee.description}",
                        'metadata': {
                            'service_type': fee.service_type,
                            'amount': float(fee.fee_amount),
                            'payment_methods': fee.payment_methods
                        }
                    })
            
        except Exception as e:
            logger.error(f"Error retrieving structured data: {e}")
        
        return structured_results
    
    async def _rank_and_filter_results(
        self,
        vector_results: List[Dict[str, Any]],
        structured_results: List[Dict[str, Any]],
        query: str,
        query_type: str
    ) -> List[Dict[str, Any]]:
        """Rank and filter retrieved results based on relevance and authority."""
        all_results = []
        
        # Add vector search results
        for result in vector_results:
            all_results.append({
                **result,
                'source_type': 'vector',
                'authority_score': self._get_authority_score(result.get('document_type', '')),
                'recency_score': self._get_recency_score(result.get('metadata', {}))
            })
        
        # Add structured results
        for result in structured_results:
            all_results.append({
                **result,
                'source_type': 'structured',
                'score': 0.9,  # High score for structured data
                'authority_score': self._get_authority_score(result['type']),
                'recency_score': 1.0  # Assume structured data is current
            })
        
        # Calculate final scores
        for result in all_results:
            relevance = result.get('score', 0.0)
            authority = result.get('authority_score', 0.5)
            recency = result.get('recency_score', 0.5)

            # Get query type boost
            doc_type = result.get('document_type', result.get('type', ''))
            query_boost = self._get_query_type_boost(query_type, doc_type)

            # Weighted final score with query type boost
            final_score = (relevance * 0.6) + (authority * 0.3) + (recency * 0.1) + query_boost
            result['final_score'] = final_score
        
        # Sort by final score and filter
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Remove duplicates and low-scoring results
        filtered_results = []
        seen_content = set()
        
        for result in all_results:
            content_key = result.get('text', result.get('content', ''))[:100]
            if content_key not in seen_content and result['final_score'] > 0.5:
                seen_content.add(content_key)
                filtered_results.append(result)
                
                if len(filtered_results) >= self.max_retrieved_docs:
                    break
        
        return filtered_results
    
    def _get_authority_score(self, document_type: str) -> float:
        """Get authority score based on document type."""
        authority_scores = {
            'constitution': 1.0,
            'judicial_profiles': 0.95,  # Very high priority for current judges info
            'case_law': 0.9,  # High priority for case law
            'case': 0.9,
            'judicial_structure': 0.85,  # High priority for court structure
            'judge': 0.8,
            'fee': 0.8,
            'procedure': 0.7,
            'general': 0.5
        }
        return authority_scores.get(document_type, 0.5)

    def _get_query_type_boost(self, query_type: str, document_type: str) -> float:
        """Get additional boost based on query type and document type alignment."""
        query_boosts = {
            'judge_information': {
                'judicial_profiles': 0.3,  # Extra boost for judge queries
                'judicial_structure': 0.2,
                'judge': 0.3
            },
            'constitutional_query': {
                'constitution': 0.2
            },
            'case_law': {
                'case_law': 0.2,
                'case': 0.2
            },
            'procedural_information': {
                'procedure': 0.2
            }
        }

        return query_boosts.get(query_type, {}).get(document_type, 0.0)

    def _get_recency_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate recency score based on document metadata."""
        try:
            created_at = metadata.get('created_at')
            if not created_at:
                return 0.5
            
            if isinstance(created_at, (int, float)):
                doc_date = datetime.fromtimestamp(created_at)
            else:
                doc_date = datetime.fromisoformat(str(created_at))
            
            days_old = (datetime.utcnow() - doc_date).days
            
            # Decay function: newer documents get higher scores
            if days_old <= 30:
                return 1.0
            elif days_old <= 365:
                return 0.8
            elif days_old <= 1825:  # 5 years
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved results."""
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results):
            # Format result based on type
            if result.get('source_type') == 'structured':
                content = f"**{result['title']}**\n{result['content']}"
            else:
                doc_type = result.get('document_type', 'document')
                content = f"**{doc_type.title()} Reference:**\n{result.get('text', result.get('content', ''))}"
            
            # Check if adding this would exceed max length
            if current_length + len(content) > self.max_context_length:
                break
            
            context_parts.append(f"[Source {i+1}] {content}")
            current_length += len(content)
        
        return "\n\n".join(context_parts)
    
    async def retrieve_context(
        self,
        query: str,
        db: AsyncSession,
        max_results: int = 10
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant context for a query using RAG pipeline.
        
        Args:
            query: User query
            db: Database session
            max_results: Maximum number of results to retrieve
            
        Returns:
            Tuple of (context_string, source_list)
        """
        try:
            # Classify query and extract entities
            query_type = self._classify_query_type(query)
            entities = self._extract_entities(query)
            
            logger.info(f"Query type: {query_type}, Entities: {entities}")
            
            # Generate query embedding for vector search
            query_embedding = await embedding_service.generate_query_embedding(query)
            
            # Perform vector search
            vector_results = await vector_db_service.search_similar(
                query_embedding=query_embedding,
                limit=max_results,
                score_threshold=self.min_relevance_score
            )
            
            # Get structured data from database
            structured_results = await self._get_structured_data(query_type, entities, db)
            
            # Rank and filter results
            final_results = await self._rank_and_filter_results(
                vector_results, structured_results, query, query_type
            )
            
            # Build context
            context = self._build_context(final_results)
            
            # Format sources for response
            sources = []
            for i, result in enumerate(final_results[:5]):  # Limit sources in response
                source = {
                    'document_id': result.get('document_id', f'source_{i+1}'),
                    'document_type': result.get('document_type', result.get('type', 'unknown')),
                    'title': result.get('title', f"Legal Reference {i+1}"),
                    'content_snippet': (result.get('text', result.get('content', ''))[:200] + '...'),
                    'relevance_score': result.get('final_score', 0.0),
                    'url': result.get('metadata', {}).get('url')
                }
                sources.append(source)
            
            logger.info(f"Retrieved {len(final_results)} relevant documents for query")
            return context, sources
            
        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}")
            return "", []
    
    async def log_search_query(
        self,
        query: str,
        query_type: str,
        session_id: str,
        response_time: float,
        documents_retrieved: int,
        db: AsyncSession
    ):
        """Log search query for analytics."""
        try:
            search_query = SearchQuery(
                query_text=query,
                query_type=query_type,
                user_session=session_id,
                response_time=response_time,
                documents_retrieved=documents_retrieved,
                intent_classification=query_type
            )
            
            db.add(search_query)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error logging search query: {e}")


# Global RAG service instance
rag_service = RAGService()
