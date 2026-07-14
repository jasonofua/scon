"""
WebSocket management API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from app.services.auth import get_current_superuser
from app.services.websocket_manager import connection_manager
from app.models.admin import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get WebSocket connection statistics (admin only).
    """
    try:
        stats = connection_manager.get_connection_stats()
        return {
            "websocket_stats": stats,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket statistics")


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "system_announcement",
    target_group: str = "all",
    current_user: User = Depends(get_current_superuser)
):
    """
    Broadcast a message to all connected users (admin only).
    """
    try:
        broadcast_data = {
            "type": "system_broadcast",
            "message_type": message_type,
            "message": message,
            "from": "SCONIA System",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        if target_group == "all":
            await connection_manager.broadcast_to_all(broadcast_data)
        else:
            await connection_manager.broadcast_to_group(target_group, broadcast_data)
        
        return {
            "message": "Broadcast sent successfully",
            "target_group": target_group,
            "message_type": message_type
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


@router.post("/cleanup")
async def cleanup_connections(
    current_user: User = Depends(get_current_superuser)
):
    """
    Clean up inactive WebSocket connections (admin only).
    """
    try:
        await connection_manager.cleanup_inactive_connections()
        
        return {
            "message": "Connection cleanup completed",
            "stats": connection_manager.get_connection_stats()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup connections")


@router.get("/health")
async def websocket_health():
    """
    Check WebSocket service health.
    """
    try:
        stats = connection_manager.get_connection_stats()
        
        return {
            "status": "healthy",
            "active_connections": stats["active_connections"],
            "service": "websocket_manager"
        }
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        raise HTTPException(status_code=500, detail="WebSocket service unhealthy")
