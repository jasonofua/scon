"""
Main chat service for SCONIA.
Orchestrates query processing, retrieval, and response generation.
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
import time
import uuid
import json
from datetime import datetime
from google import genai
from google.genai import types
from fastapi import WebSocket

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings, SCONIA_SYSTEM_PROMPT
from app.schemas.chat import ChatResponse, Source, QuickOption, StreamingResponse
from app.services.query_processor import query_processor
from app.services.rag import rag_service
from app.services.cache import cache_service
from app.models.embeddings import UserSession, SearchQuery
from app.models.admin import Feedback

logger = logging.getLogger(__name__)


class ChatService:
    """Main chat service for SCONIA legal assistant."""
    
    def __init__(self, db: AsyncSession):
        """Initialize chat service with database session."""
        self.db = db
        # Initialize Google GenAI client
        self.gemini_client = None
        try:
            if settings.gemini_api_key:
                self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
            else:
                self.gemini_client = genai.Client()
        except ValueError:
            logger.warning("Google GenAI client could not be initialized in ChatService because GEMINI_API_KEY is missing.")
            self.gemini_client = None
        self.model = settings.gemini_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    async def _get_or_create_session(self, session_id: Optional[str]) -> str:
        """Get existing session or create new one."""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Check if session exists
            result = await self.db.execute(
                select(UserSession).where(UserSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                # Create new session
                session = UserSession(
                    session_id=session_id,
                    start_time=datetime.utcnow(),
                    query_count=0,
                    device_type="kiosk"  # Default for SCONIA kiosks
                )
                self.db.add(session)
                await self.db.commit()
                logger.info(f"Created new session: {session_id}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error managing session: {e}")
            return session_id or str(uuid.uuid4())
    
    async def _update_session_stats(self, session_id: str):
        """Update session statistics."""
        try:
            await self.db.execute(
                update(UserSession)
                .where(UserSession.session_id == session_id)
                .values(query_count=UserSession.query_count + 1)
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Source]:
        """Format sources for response."""
        formatted_sources = []
        
        for source in sources:
            formatted_source = Source(
                document_id=source.get('document_id', ''),
                document_type=source.get('document_type', 'unknown'),
                title=source.get('title', 'Legal Reference'),
                content_snippet=source.get('content_snippet', ''),
                relevance_score=source.get('relevance_score', 0.0),
                url=source.get('url')
            )
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def _format_quick_options(self, options: List[Dict[str, str]]) -> List[QuickOption]:
        """Format quick options for response."""
        formatted_options = []
        
        for option in options:
            formatted_option = QuickOption(
                text=option.get('text', ''),
                action=option.get('action', ''),
                category=option.get('category', 'general')
            )
            formatted_options.append(formatted_option)
        
        return formatted_options
    
    async def _generate_response(
        self,
        query: str,
        context: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> str:
        """Generate AI response using Google Gemini."""
        try:
            # For greetings and help requests, use simpler prompt without context
            if intent in {'greeting', 'help_request'}:
                system_prompt = """You are SCONIA, the Supreme Court of Nigeria Information Assistant.
                Respond warmly and professionally to greetings and help requests.
                Introduce yourself and offer assistance with Nigerian constitutional law, Supreme Court procedures, and legal information."""
            else:
                # Build the full prompt with context for informational queries
                system_prompt = SCONIA_SYSTEM_PROMPT.format(
                    context=context,
                    query=query
                )
 
                # Add intent and entity information to help the AI
                additional_context = f"\nQuery Intent: {intent}\nExtracted Entities: {json.dumps(entities, indent=2)}"
                system_prompt += additional_context
            
            # Generate response via google-genai
            response = await self.gemini_client.aio.models.generate_content(
                model=self.model,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return self._get_fallback_response(intent, entities)
    
    def _get_fallback_response(self, intent: str, entities: Dict[str, Any]) -> str:
        """Generate fallback response when AI fails."""
        fallback_responses = {
            'constitutional_query': "I can help you with constitutional questions. The Nigerian Constitution contains fundamental rights and governmental structures. Please try rephrasing your question or ask about specific sections.",
            'judge_information': "I can provide information about Supreme Court justices and court personnel. Please ask about specific judges or court structure.",
            'case_law': "I can help you find information about Supreme Court cases and legal precedents. Please specify the case or legal principle you're interested in.",
            'procedural_information': "I can guide you through court procedures and filing processes. Please ask about specific procedures or requirements.",
            'fee_calculation': "I can help you understand court fees and payment methods. Please ask about specific services or fee types.",
            'court_schedule': "I can provide information about court schedules and sessions. Please ask about specific dates or session types.",
            'greeting': "Hello! Welcome to the Supreme Court of Nigeria Information Assistant. How may I assist you today? Are you looking for information on the Nigerian Constitution, Supreme Court cases, or court filing procedures?",
            'help_request': "I'm here to help! I can assist you with questions about Nigerian constitutional law and Supreme Court procedures. You can ask me about fundamental rights, court cases, filing procedures, or any other legal matters related to the Supreme Court of Nigeria.",
            'general_information': "I'm SCONIA, your Supreme Court of Nigeria Information Assistant. I can help with constitutional questions, court procedures, judge information, and legal guidance. How can I assist you today?"
        }
        
        return fallback_responses.get(intent, fallback_responses['general_information'])
    
    def _calculate_confidence_score(
        self,
        intent_confidence: float,
        sources_count: int,
        response_length: int
    ) -> float:
        """Calculate overall confidence score for the response."""
        try:
            # Base confidence from intent classification
            base_confidence = intent_confidence
            
            # Boost confidence if we have good sources
            source_boost = min(sources_count * 0.1, 0.3)
            
            # Slight boost for longer, more detailed responses
            length_boost = min(response_length / 1000 * 0.1, 0.1)
            
            # Calculate final confidence (max 1.0)
            final_confidence = min(base_confidence + source_boost + length_boost, 1.0)
            
            return round(final_confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ChatResponse:
        """
        Process a user query and generate response.
        
        Args:
            query: User query
            session_id: Session identifier
            context: Previous conversation context
            user_id: User ID if authenticated
            
        Returns:
            ChatResponse with answer, sources, and metadata
        """
        start_time = time.time()
        
        try:
            # Get or create session
            session_id = await self._get_or_create_session(session_id)
 
            # Process query
            query_info = query_processor.process_query(query, context)
 
            # Try cache for full query result first
            cached_result = await cache_service.get_query_result(query, query_info['intent'])
            if cached_result:
                response_time = time.time() - start_time
                return ChatResponse(
                    answer=cached_result.get('answer', ''),
                    sources=self._format_sources(cached_result.get('sources', [])),
                    quick_options=self._format_quick_options(query_info['quick_options']),
                    confidence_score=cached_result.get('confidence_score', 0.8),
                    session_id=session_id,
                    query_id=cached_result.get('query_id', 0),
                    response_time=response_time,
                    intent_classification=query_info['intent']
                )
 
            # Check if we need RAG retrieval based on intent
            skip_rag_intents = {'greeting', 'help_request'}
            sources = []
            retrieved_context = ""
 
            if query_info['intent'] not in skip_rag_intents:
                # Try cache for RAG context
                rag_cached = await cache_service.get_rag_context(query_info['enhanced_query'])
                if rag_cached:
                    retrieved_context, sources = rag_cached
                else:
                    # Retrieve relevant context using RAG
                    retrieved_context, sources = await rag_service.retrieve_context(
                        query=query_info['enhanced_query'],
                        db=self.db
                    )
                    # Cache RAG results
                    await cache_service.set_rag_context(query_info['enhanced_query'], retrieved_context, sources)
 
            # Generate AI response
            ai_response = await self._generate_response(
                query=query,
                context=retrieved_context,
                intent=query_info['intent'],
                entities=query_info['entities']
            )
            
            # Calculate metrics
            response_time = time.time() - start_time
            confidence_score = self._calculate_confidence_score(
                query_info['confidence'],
                len(sources),
                len(ai_response)
            )
            
            # Create search query record
            search_query = SearchQuery(
                query_text=query,
                query_type=query_info['intent'],
                user_session=session_id,
                response_time=response_time,
                documents_retrieved=len(sources),
                intent_classification=query_info['intent']
            )
            self.db.add(search_query)
            await self.db.commit()
            
            # Update session stats
            await self._update_session_stats(session_id)
            
            # Format response
            response = ChatResponse(
                answer=ai_response,
                sources=self._format_sources(sources),
                quick_options=self._format_quick_options(query_info['quick_options']),
                confidence_score=confidence_score,
                session_id=session_id,
                query_id=search_query.id,
                response_time=response_time,
                intent_classification=query_info['intent']
            )
            
            # Cache the result for future queries
            cache_result = {
                'answer': ai_response,
                'sources': sources,
                'confidence_score': confidence_score,
                'query_id': search_query.id
            }
            await cache_service.set_query_result(query, query_info['intent'], cache_result)
            
            logger.info(f"Processed query in {response_time:.2f}s with confidence {confidence_score}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            
            # Return error response
            return ChatResponse(
                answer="I apologize, but I encountered an error processing your query. Please try again or rephrase your question.",
                sources=[],
                quick_options=[QuickOption(text="Try again", action="retry", category="help")],
                confidence_score=0.0,
                session_id=session_id or str(uuid.uuid4()),
                query_id=0,
                response_time=time.time() - start_time,
                intent_classification="error"
            )
    
    async def process_query_streaming(
        self,
        query: str,
        session_id: str,
        websocket: WebSocket
    ) -> ChatResponse:
        """
        Process query with streaming response via WebSocket.
        
        Args:
            query: User query
            session_id: Session identifier
            websocket: WebSocket connection
            
        Returns:
            Final ChatResponse
        """
        try:
            # Send initial processing message
            await websocket.send_text(json.dumps({
                "type": "status",
                "message": "Processing your query..."
            }))
            
            # Process query (same as regular processing)
            query_info = query_processor.process_query(query)
 
            # Check if we need RAG retrieval based on intent
            skip_rag_intents = {'greeting', 'help_request'}
            sources = []
            retrieved_context = ""
 
            if query_info['intent'] not in skip_rag_intents:
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "Searching legal database..."
                }))
 
                # Retrieve context
                retrieved_context, sources = await rag_service.retrieve_context(
                    query=query_info['enhanced_query'],
                    db=self.db
                )
            
            await websocket.send_text(json.dumps({
                "type": "status",
                "message": "Generating response..."
            }))
            
            # Generate streaming response
            response_text = ""
            async for chunk in self._generate_streaming_response(query, retrieved_context, query_info):
                response_text += chunk
                await websocket.send_text(json.dumps({
                    "type": "chunk",
                    "content": chunk
                }))
            
            # Send sources
            await websocket.send_text(json.dumps({
                "type": "sources",
                "sources": [source.__dict__ for source in self._format_sources(sources)]
            }))
            
            # Create final response
            final_response = ChatResponse(
                answer=response_text,
                sources=self._format_sources(sources),
                quick_options=self._format_quick_options(query_info['quick_options']),
                confidence_score=0.8,  # Default for streaming
                session_id=session_id,
                query_id=0,  # Will be set after DB insert
                response_time=0.0,  # Not applicable for streaming
                intent_classification=query_info['intent']
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in streaming query processing: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "An error occurred while processing your query."
            }))
            raise
    
    async def _generate_streaming_response(
        self,
        query: str,
        context: str,
        query_info: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming AI response."""
        try:
            system_prompt = SCONIA_SYSTEM_PROMPT.format(
                context=context,
                query=query
            )
            
            # Streaming content generation via google-genai
            response_stream = await self.gemini_client.aio.models.generate_content_stream(
                model=self.model,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I apologize, but I encountered an error generating the response."
    
    async def submit_feedback(
        self,
        session_id: str,
        query_id: Optional[int] = None,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None
    ):
        """Submit user feedback for a response."""
        try:
            feedback = Feedback(
                session_id=session_id,
                query_id=query_id,
                rating=rating,
                feedback_text=feedback_text,
                feedback_type="user_rating" if rating else "user_comment"
            )
            
            self.db.add(feedback)
            await self.db.commit()
            
            logger.info(f"Feedback submitted for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information and history."""
        try:
            # Get session
            result = await self.db.execute(
                select(UserSession).where(UserSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
 
            if not session:
                return None
 
            # Get queries for this session
            queries_result = await self.db.execute(
                select(SearchQuery)
                .where(SearchQuery.user_session == session_id)
                .order_by(SearchQuery.created_at.desc())
                .limit(20)
            )
            queries = queries_result.scalars().all()
 
            return {
                "session_id": session.session_id,
                "start_time": session.start_time,
                "query_count": session.query_count,
                "queries": [
                    {
                        "id": q.id,
                        "query": q.query_text,
                        "intent": q.intent_classification,
                        "response_time": q.response_time,
                        "timestamp": q.created_at
                    }
                    for q in queries
                ]
            }
 
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
 
    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all chat sessions."""
        try:
            # Get all sessions with their latest query
            result = await self.db.execute(
                select(UserSession)
                .order_by(UserSession.start_time.desc())
                .limit(50)  # Limit to recent sessions
            )
            sessions = result.scalars().all()
 
            session_list = []
            for session in sessions:
                # Get the latest query for this session
                latest_query_result = await self.db.execute(
                    select(SearchQuery)
                    .where(SearchQuery.user_session == session.session_id)
                    .order_by(SearchQuery.created_at.desc())
                    .limit(1)
                )
                latest_query = latest_query_result.scalar_one_or_none()
 
                session_data = {
                    "id": session.session_id,
                    "title": f"Chat Session {session.session_id[:8]}",
                    "lastMessage": latest_query.query_text[:100] + "..." if latest_query and len(latest_query.query_text) > 100 else (latest_query.query_text if latest_query else "No messages"),
                    "timestamp": session.start_time.isoformat(),
                    "messageCount": session.query_count,
                    "isActive": False
                }
                session_list.append(session_data)
 
            return session_list
 
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            return []
 
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        try:
            # Get all queries for this session
            queries_result = await self.db.execute(
                select(SearchQuery)
                .where(SearchQuery.user_session == session_id)
                .order_by(SearchQuery.created_at.asc())
            )
            queries = queries_result.scalars().all()
 
            messages = []
            for query in queries:
                messages.append({
                    "id": query.id,
                    "query": query.query_text,
                    "response": "Response generated",  # You might want to store actual responses
                    "sources": [],
                    "timestamp": query.created_at,
                    "rating": query.satisfaction_rating,
                    "feedback": None
                })
 
            return messages
 
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
