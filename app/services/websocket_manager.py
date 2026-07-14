"""
WebSocket connection manager for SCONIA.
Handles real-time connections, typing indicators, and notifications.
"""
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for SCONIA."""
    
    def __init__(self):
        # Active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Typing indicators
        self.typing_sessions: Dict[str, datetime] = {}
        
        # Connection groups (for broadcasting)
        self.connection_groups: Dict[str, Set[str]] = {}
        
        # Message queue for offline sessions
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str, user_type: str = "citizen"):
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[session_id] = websocket
            
            # Store metadata
            self.connection_metadata[session_id] = {
                "connected_at": datetime.utcnow(),
                "user_type": user_type,
                "last_activity": datetime.utcnow(),
                "message_count": 0
            }
            
            # Add to default group
            if "all" not in self.connection_groups:
                self.connection_groups["all"] = set()
            self.connection_groups["all"].add(session_id)
            
            # Send welcome message
            await self.send_personal_message(session_id, {
                "type": "connection_established",
                "session_id": session_id,
                "message": "Connected to SCONIA - Supreme Court of Nigeria Information Assistant",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send queued messages if any
            await self._send_queued_messages(session_id)
            
            logger.info(f"WebSocket connected: {session_id}")
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket {session_id}: {e}")
            raise
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket connection."""
        try:
            # Remove from active connections
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            
            # Remove from typing sessions
            if session_id in self.typing_sessions:
                del self.typing_sessions[session_id]
            
            # Remove from groups
            for group_sessions in self.connection_groups.values():
                group_sessions.discard(session_id)
            
            # Update metadata
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["disconnected_at"] = datetime.utcnow()
            
            logger.info(f"WebSocket disconnected: {session_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {session_id}: {e}")
    
    async def send_personal_message(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session."""
        try:
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
                
                # Update activity
                if session_id in self.connection_metadata:
                    self.connection_metadata[session_id]["last_activity"] = datetime.utcnow()
                    self.connection_metadata[session_id]["message_count"] += 1
            else:
                # Queue message for when user reconnects
                if session_id not in self.message_queue:
                    self.message_queue[session_id] = []
                self.message_queue[session_id].append({
                    **message,
                    "queued_at": datetime.utcnow().isoformat()
                })
                
        except WebSocketDisconnect:
            await self.disconnect(session_id)
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")
    
    async def broadcast_to_group(self, group: str, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all connections in a group."""
        if group not in self.connection_groups:
            return
        
        exclude = exclude or set()
        tasks = []
        
        for session_id in self.connection_groups[group]:
            if session_id not in exclude:
                tasks.append(self.send_personal_message(session_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all active connections."""
        await self.broadcast_to_group("all", message, exclude)
    
    async def set_typing_indicator(self, session_id: str, is_typing: bool):
        """Set typing indicator for a session."""
        try:
            if is_typing:
                self.typing_sessions[session_id] = datetime.utcnow()
                
                # Send typing indicator to others (if needed for group chats)
                await self.send_personal_message(session_id, {
                    "type": "typing_indicator",
                    "status": "typing",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                if session_id in self.typing_sessions:
                    del self.typing_sessions[session_id]
                
                await self.send_personal_message(session_id, {
                    "type": "typing_indicator",
                    "status": "stopped",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error setting typing indicator for {session_id}: {e}")
    
    async def send_system_notification(self, session_id: str, notification_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Send a system notification to a session."""
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(session_id, notification)
    
    async def send_query_progress(self, session_id: str, stage: str, progress: float, message: str):
        """Send query processing progress to a session."""
        progress_update = {
            "type": "query_progress",
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(session_id, progress_update)
    
    async def send_streaming_chunk(self, session_id: str, chunk: str, chunk_type: str = "text"):
        """Send a streaming response chunk."""
        chunk_message = {
            "type": "streaming_chunk",
            "chunk_type": chunk_type,
            "content": chunk,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(session_id, chunk_message)
    
    async def send_sources_update(self, session_id: str, sources: List[Dict[str, Any]]):
        """Send sources information during query processing."""
        sources_message = {
            "type": "sources_update",
            "sources": sources,
            "count": len(sources),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(session_id, sources_message)
    
    async def _send_queued_messages(self, session_id: str):
        """Send queued messages to a reconnected session."""
        if session_id in self.message_queue:
            messages = self.message_queue[session_id]
            
            if messages:
                # Send notification about queued messages
                await self.send_personal_message(session_id, {
                    "type": "queued_messages",
                    "count": len(messages),
                    "message": f"You have {len(messages)} queued message(s)"
                })
                
                # Send each queued message
                for message in messages:
                    await self.send_personal_message(session_id, message)
                
                # Clear the queue
                del self.message_queue[session_id]
    
    async def cleanup_inactive_connections(self):
        """Clean up inactive connections and typing indicators."""
        try:
            current_time = datetime.utcnow()
            inactive_sessions = []
            
            # Check for inactive connections (no activity for 30 minutes)
            for session_id, metadata in self.connection_metadata.items():
                if session_id in self.active_connections:
                    last_activity = metadata.get("last_activity", metadata.get("connected_at"))
                    if current_time - last_activity > timedelta(minutes=30):
                        inactive_sessions.append(session_id)
            
            # Disconnect inactive sessions
            for session_id in inactive_sessions:
                if session_id in self.active_connections:
                    try:
                        await self.active_connections[session_id].close()
                    except:
                        pass
                    await self.disconnect(session_id)
            
            # Clean up old typing indicators (older than 10 seconds)
            old_typing = []
            for session_id, typing_time in self.typing_sessions.items():
                if current_time - typing_time > timedelta(seconds=10):
                    old_typing.append(session_id)
            
            for session_id in old_typing:
                await self.set_typing_indicator(session_id, False)
            
            # Clean up old queued messages (older than 24 hours)
            old_queues = []
            for session_id, messages in self.message_queue.items():
                if messages:
                    oldest_message = min(
                        datetime.fromisoformat(msg.get("queued_at", current_time.isoformat()))
                        for msg in messages
                    )
                    if current_time - oldest_message > timedelta(hours=24):
                        old_queues.append(session_id)
            
            for session_id in old_queues:
                del self.message_queue[session_id]
            
            if inactive_sessions or old_typing or old_queues:
                logger.info(f"Cleaned up: {len(inactive_sessions)} inactive connections, "
                          f"{len(old_typing)} old typing indicators, "
                          f"{len(old_queues)} old message queues")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections."""
        active_count = len(self.active_connections)
        typing_count = len(self.typing_sessions)
        queued_messages = sum(len(messages) for messages in self.message_queue.values())
        
        # User type breakdown
        user_types = {}
        for metadata in self.connection_metadata.values():
            user_type = metadata.get("user_type", "unknown")
            user_types[user_type] = user_types.get(user_type, 0) + 1
        
        return {
            "active_connections": active_count,
            "typing_sessions": typing_count,
            "queued_messages": queued_messages,
            "user_types": user_types,
            "total_sessions": len(self.connection_metadata)
        }
    
    def is_connected(self, session_id: str) -> bool:
        """Check if a session is currently connected."""
        return session_id in self.active_connections


# Global connection manager instance
connection_manager = ConnectionManager()
