"""
Monitoring API endpoints for SCONIA.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.database import get_async_db
from app.services.auth import get_current_superuser
from app.services.monitoring import performance_monitor
from app.models.admin import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def get_health_status():
    """
    Get system health status (public endpoint).
    """
    try:
        health_status = performance_monitor.get_health_status()
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health status")


@router.get("/metrics/system")
async def get_system_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get system performance metrics (admin only).
    """
    try:
        metrics = performance_monitor.get_system_metrics()
        return {
            "system_metrics": metrics,
            "timestamp": performance_monitor.start_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/metrics/api")
async def get_api_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get API performance metrics (admin only).
    """
    try:
        metrics = performance_monitor.get_api_metrics()
        return {
            "api_metrics": metrics,
            "monitoring_period": "last_1000_requests"
        }
        
    except Exception as e:
        logger.error(f"Error getting API metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API metrics")


@router.get("/metrics/chat")
async def get_chat_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get chat service metrics (admin only).
    """
    try:
        metrics = performance_monitor.get_chat_metrics()
        return {
            "chat_metrics": metrics,
            "monitoring_period": "last_24_hours"
        }
        
    except Exception as e:
        logger.error(f"Error getting chat metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat metrics")


@router.get("/metrics/search")
async def get_search_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get search service metrics (admin only).
    """
    try:
        metrics = performance_monitor.get_search_metrics()
        return {
            "search_metrics": metrics,
            "monitoring_period": "last_24_hours"
        }
        
    except Exception as e:
        logger.error(f"Error getting search metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search metrics")


@router.get("/metrics/vector-db")
async def get_vector_db_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get vector database metrics (admin only).
    """
    try:
        metrics = performance_monitor.get_vector_db_metrics()
        return {
            "vector_db_metrics": metrics,
            "monitoring_period": "last_24_hours"
        }
        
    except Exception as e:
        logger.error(f"Error getting vector DB metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vector DB metrics")


@router.get("/metrics/database")
async def get_database_metrics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get database metrics (admin only).
    """
    try:
        metrics = await performance_monitor.get_database_metrics(db)
        return {
            "database_metrics": metrics,
            "monitoring_period": "all_time"
        }
        
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database metrics")


@router.get("/metrics/comprehensive")
async def get_comprehensive_metrics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive metrics report (admin only).
    """
    try:
        # Get all metrics
        system_metrics = performance_monitor.get_system_metrics()
        api_metrics = performance_monitor.get_api_metrics()
        chat_metrics = performance_monitor.get_chat_metrics()
        search_metrics = performance_monitor.get_search_metrics()
        vector_db_metrics = performance_monitor.get_vector_db_metrics()
        database_metrics = await performance_monitor.get_database_metrics(db)
        health_status = performance_monitor.get_health_status()
        
        return {
            "comprehensive_metrics": {
                "health": health_status,
                "system": system_metrics,
                "api": api_metrics,
                "chat": chat_metrics,
                "search": search_metrics,
                "vector_db": vector_db_metrics,
                "database": database_metrics
            },
            "report_generated_at": performance_monitor.start_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting comprehensive metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comprehensive metrics")


@router.get("/alerts")
async def get_system_alerts(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get system alerts and warnings (admin only).
    """
    try:
        health_status = performance_monitor.get_health_status()
        system_metrics = performance_monitor.get_system_metrics()
        api_metrics = performance_monitor.get_api_metrics()
        
        alerts = []
        warnings = []
        
        # Check for critical issues
        if health_status.get('status') == 'unhealthy':
            alerts.extend([
                {
                    "level": "critical",
                    "message": f"System unhealthy: {', '.join(health_status.get('issues', []))}",
                    "timestamp": health_status.get('timestamp')
                }
            ])
        
        # Check for warnings
        cpu_usage = system_metrics.get('cpu_usage', {}).get('current', 0)
        if cpu_usage > 70:
            warnings.append({
                "level": "warning",
                "message": f"High CPU usage: {cpu_usage:.1f}%",
                "metric": "cpu_usage",
                "value": cpu_usage
            })
        
        memory_usage = system_metrics.get('memory_usage', {}).get('current', 0)
        if memory_usage > 80:
            warnings.append({
                "level": "warning",
                "message": f"High memory usage: {memory_usage:.1f}%",
                "metric": "memory_usage",
                "value": memory_usage
            })
        
        error_rate = api_metrics.get('error_rate', 0)
        if error_rate > 2:
            warnings.append({
                "level": "warning",
                "message": f"Elevated error rate: {error_rate:.1f}%",
                "metric": "error_rate",
                "value": error_rate
            })
        
        avg_response_time = api_metrics.get('average_response_time', 0)
        if avg_response_time > 3:
            warnings.append({
                "level": "warning",
                "message": f"Slow response times: {avg_response_time:.2f}s",
                "metric": "response_time",
                "value": avg_response_time
            })
        
        return {
            "alerts": alerts,
            "warnings": warnings,
            "alert_count": len(alerts),
            "warning_count": len(warnings),
            "overall_status": health_status.get('status', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system alerts")


@router.post("/metrics/reset")
async def reset_metrics(
    current_user: User = Depends(get_current_superuser)
):
    """
    Reset collected metrics (admin only).
    """
    try:
        # Clear metrics
        performance_monitor.metrics.clear()
        performance_monitor.response_times.clear()
        performance_monitor.error_counts.clear()
        performance_monitor.endpoint_metrics.clear()
        
        return {
            "message": "Metrics reset successfully",
            "reset_at": performance_monitor.start_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset metrics")


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_superuser)
):
    """
    Get performance summary dashboard (admin only).
    """
    try:
        health_status = performance_monitor.get_health_status()
        system_metrics = performance_monitor.get_system_metrics()
        api_metrics = performance_monitor.get_api_metrics()
        
        # Calculate key performance indicators
        kpis = {
            "system_health": health_status.get('status', 'unknown'),
            "uptime_hours": system_metrics.get('uptime_seconds', 0) / 3600,
            "cpu_usage_percent": system_metrics.get('cpu_usage', {}).get('current', 0),
            "memory_usage_percent": system_metrics.get('memory_usage', {}).get('current', 0),
            "total_requests": api_metrics.get('total_requests', 0),
            "error_rate_percent": api_metrics.get('error_rate', 0),
            "avg_response_time_seconds": api_metrics.get('average_response_time', 0),
            "active_requests": system_metrics.get('active_requests', 0)
        }
        
        # Performance grades
        grades = {
            "overall": "A" if health_status.get('status') == 'healthy' else "B" if health_status.get('status') == 'degraded' else "F",
            "response_time": "A" if kpis["avg_response_time_seconds"] < 1 else "B" if kpis["avg_response_time_seconds"] < 3 else "C",
            "error_rate": "A" if kpis["error_rate_percent"] < 1 else "B" if kpis["error_rate_percent"] < 5 else "F",
            "resource_usage": "A" if max(kpis["cpu_usage_percent"], kpis["memory_usage_percent"]) < 70 else "B"
        }
        
        return {
            "performance_summary": {
                "kpis": kpis,
                "grades": grades,
                "status": health_status.get('status', 'unknown'),
                "issues": health_status.get('issues', [])
            },
            "generated_at": health_status.get('timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance summary")
