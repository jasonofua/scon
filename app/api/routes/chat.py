"""
Chat API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import logging
from datetime import datetime

from app.database import get_async_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatSession
from app.services.chat import ChatService
from app.services.auth import get_current_user_optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Main chat endpoint for SCONIA.
    Processes user queries and returns AI-generated responses with legal information.
    """
    try:
        chat_service = ChatService(db)
        response = await chat_service.process_query(
            query=request.query,
            session_id=request.session_id,
            context=request.context,
            user_id=getattr(current_user, 'id', None)
        )
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")


@router.get("/sessions")
async def get_chat_sessions(
    db: AsyncSession = Depends(get_async_db)
):
    """Get all chat sessions."""
    try:
        chat_service = ChatService(db)
        sessions = await chat_service.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get chat session history."""
    try:
        chat_service = ChatService(db)
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get chat history for a session."""
    try:
        chat_service = ChatService(db)
        history = await chat_service.get_session_history(session_id)
        return {"messages": history}
    except Exception as e:
        logger.error(f"Get chat history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    query_id: Optional[int] = None,
    rating: Optional[int] = None,
    feedback_text: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Submit user feedback for a chat response."""
    try:
        chat_service = ChatService(db)
        await chat_service.submit_feedback(
            session_id=session_id,
            query_id=query_id,
            rating=rating,
            feedback_text=feedback_text
        )
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, user_type: str = "citizen"):
    """
    Enhanced WebSocket endpoint for real-time chat.
    Provides streaming responses, typing indicators, and connection management.
    """
    from app.services.websocket_manager import connection_manager

    try:
        # Connect to WebSocket manager
        await connection_manager.connect(websocket, session_id, user_type)

        # Get database session
        async with get_async_db() as db:
            chat_service = ChatService(db)

            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")

                if message_type == "query":
                    # Process query and stream response
                    query = message.get("query", "")

                    if not query.strip():
                        await connection_manager.send_personal_message(session_id, {
                            "type": "error",
                            "message": "Query cannot be empty"
                        })
                        continue

                    # Send processing stages
                    await connection_manager.send_query_progress(
                        session_id, "processing", 0.1, "Processing your query..."
                    )

                    await connection_manager.send_query_progress(
                        session_id, "searching", 0.3, "Searching legal database..."
                    )

                    # Process query with streaming
                    response = await chat_service.process_query_streaming(
                        query=query,
                        session_id=session_id,
                        websocket=websocket
                    )

                    await connection_manager.send_query_progress(
                        session_id, "complete", 1.0, "Response generated"
                    )

                    # Send final response
                    await connection_manager.send_personal_message(session_id, {
                        "type": "query_complete",
                        "data": response.dict()
                    })

                elif message_type == "typing":
                    # Handle typing indicators
                    is_typing = message.get("is_typing", False)
                    await connection_manager.set_typing_indicator(session_id, is_typing)

                elif message_type == "ping":
                    # Respond to ping for connection health
                    await connection_manager.send_personal_message(session_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_type == "feedback":
                    # Handle feedback submission
                    rating = message.get("rating")
                    feedback_text = message.get("feedback_text")
                    query_id = message.get("query_id")

                    try:
                        await chat_service.submit_feedback(
                            session_id=session_id,
                            query_id=query_id,
                            rating=rating,
                            feedback_text=feedback_text
                        )

                        await connection_manager.send_system_notification(
                            session_id, "feedback_received", "Thank you for your feedback!"
                        )
                    except Exception as e:
                        await connection_manager.send_system_notification(
                            session_id, "feedback_error", "Failed to submit feedback"
                        )

                elif message_type == "get_session_info":
                    # Send session information
                    session_info = await chat_service.get_session(session_id)
                    await connection_manager.send_personal_message(session_id, {
                        "type": "session_info",
                        "data": session_info
                    })

                else:
                    await connection_manager.send_personal_message(session_id, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await connection_manager.send_personal_message(session_id, {
                "type": "error",
                "message": "An error occurred in the chat service"
            })
        except:
            pass
    finally:
        await connection_manager.disconnect(session_id)
