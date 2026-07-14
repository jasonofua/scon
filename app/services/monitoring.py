"""
Performance monitoring and metrics collection service for SCONIA.
"""
from typing import Dict, List, Any, Optional
import time
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import threading
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.embeddings import SearchQuery, UserSession
from app.models.admin import Feedback

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring and metrics collection service."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = defaultdict(list)
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.error_counts = defaultdict(int)
        self.active_requests = 0
        self.start_time = datetime.utcnow()
        
        # System metrics
        self.cpu_usage = deque(maxlen=100)
        self.memory_usage = deque(maxlen=100)
        self.disk_usage = deque(maxlen=100)
        
        # API metrics
        self.endpoint_metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'errors': 0,
            'avg_response_time': 0.0
        })
        
        # Start background monitoring
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._monitor_thread.start()
    
    def _background_monitor(self):
        """Background thread for system monitoring."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                self.cpu_usage.append(psutil.cpu_percent())
                self.memory_usage.append(psutil.virtual_memory().percent)
                self.disk_usage.append(psutil.disk_usage('/').percent)
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(60)  # Wait longer on error
    
    @asynccontextmanager
    async def track_request(self, endpoint: str, method: str = "GET"):
        """Context manager to track request performance."""
        start_time = time.time()
        self.active_requests += 1
        
        try:
            yield
            
            # Success - record metrics
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            endpoint_key = f"{method} {endpoint}"
            metrics = self.endpoint_metrics[endpoint_key]
            metrics['count'] += 1
            metrics['total_time'] += response_time
            metrics['avg_response_time'] = metrics['total_time'] / metrics['count']
            
        except Exception as e:
            # Error - record error metrics
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            endpoint_key = f"{method} {endpoint}"
            self.endpoint_metrics[endpoint_key]['errors'] += 1
            self.error_counts[str(type(e).__name__)] += 1
            
            raise
        
        finally:
            self.active_requests -= 1
    
    def record_chat_query(self, response_time: float, intent: str, success: bool = True):
        """Record chat query metrics."""
        self.metrics['chat_queries'].append({
            'timestamp': datetime.utcnow(),
            'response_time': response_time,
            'intent': intent,
            'success': success
        })
        
        # Keep only recent metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.metrics['chat_queries'] = [
            m for m in self.metrics['chat_queries'] 
            if m['timestamp'] > cutoff_time
        ]
    
    def record_search_query(self, response_time: float, result_count: int, query_type: str):
        """Record search query metrics."""
        self.metrics['search_queries'].append({
            'timestamp': datetime.utcnow(),
            'response_time': response_time,
            'result_count': result_count,
            'query_type': query_type
        })
        
        # Keep only recent metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.metrics['search_queries'] = [
            m for m in self.metrics['search_queries'] 
            if m['timestamp'] > cutoff_time
        ]
    
    def record_vector_db_operation(self, operation: str, response_time: float, success: bool = True):
        """Record vector database operation metrics."""
        self.metrics['vector_db_ops'].append({
            'timestamp': datetime.utcnow(),
            'operation': operation,
            'response_time': response_time,
            'success': success
        })
        
        # Keep only recent metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.metrics['vector_db_ops'] = [
            m for m in self.metrics['vector_db_ops'] 
            if m['timestamp'] > cutoff_time
        ]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            return {
                'cpu_usage': {
                    'current': psutil.cpu_percent(),
                    'average': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
                    'max': max(self.cpu_usage) if self.cpu_usage else 0
                },
                'memory_usage': {
                    'current': psutil.virtual_memory().percent,
                    'average': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                    'max': max(self.memory_usage) if self.memory_usage else 0,
                    'available_gb': psutil.virtual_memory().available / (1024**3)
                },
                'disk_usage': {
                    'current': psutil.disk_usage('/').percent,
                    'average': sum(self.disk_usage) / len(self.disk_usage) if self.disk_usage else 0,
                    'max': max(self.disk_usage) if self.disk_usage else 0,
                    'free_gb': psutil.disk_usage('/').free / (1024**3)
                },
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'active_requests': self.active_requests
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics."""
        try:
            total_requests = sum(metrics['count'] for metrics in self.endpoint_metrics.values())
            total_errors = sum(metrics['errors'] for metrics in self.endpoint_metrics.values())
            
            # Calculate percentiles for response times
            sorted_times = sorted(self.response_times)
            percentiles = {}
            if sorted_times:
                percentiles = {
                    'p50': sorted_times[int(len(sorted_times) * 0.5)],
                    'p90': sorted_times[int(len(sorted_times) * 0.9)],
                    'p95': sorted_times[int(len(sorted_times) * 0.95)],
                    'p99': sorted_times[int(len(sorted_times) * 0.99)]
                }
            
            return {
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
                'average_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                'response_time_percentiles': percentiles,
                'endpoints': dict(self.endpoint_metrics),
                'error_breakdown': dict(self.error_counts)
            }
        except Exception as e:
            logger.error(f"Error getting API metrics: {e}")
            return {}
    
    def get_chat_metrics(self) -> Dict[str, Any]:
        """Get chat-specific metrics."""
        try:
            chat_queries = self.metrics.get('chat_queries', [])
            
            if not chat_queries:
                return {'total_queries': 0}
            
            # Calculate metrics
            total_queries = len(chat_queries)
            successful_queries = sum(1 for q in chat_queries if q['success'])
            avg_response_time = sum(q['response_time'] for q in chat_queries) / total_queries
            
            # Intent breakdown
            intent_counts = defaultdict(int)
            for query in chat_queries:
                intent_counts[query['intent']] += 1
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                'average_response_time': avg_response_time,
                'intent_breakdown': dict(intent_counts)
            }
        except Exception as e:
            logger.error(f"Error getting chat metrics: {e}")
            return {}
    
    def get_search_metrics(self) -> Dict[str, Any]:
        """Get search-specific metrics."""
        try:
            search_queries = self.metrics.get('search_queries', [])
            
            if not search_queries:
                return {'total_searches': 0}
            
            # Calculate metrics
            total_searches = len(search_queries)
            avg_response_time = sum(q['response_time'] for q in search_queries) / total_searches
            avg_results = sum(q['result_count'] for q in search_queries) / total_searches
            
            # Query type breakdown
            type_counts = defaultdict(int)
            for query in search_queries:
                type_counts[query['query_type']] += 1
            
            return {
                'total_searches': total_searches,
                'average_response_time': avg_response_time,
                'average_results_per_search': avg_results,
                'query_type_breakdown': dict(type_counts)
            }
        except Exception as e:
            logger.error(f"Error getting search metrics: {e}")
            return {}
    
    def get_vector_db_metrics(self) -> Dict[str, Any]:
        """Get vector database metrics."""
        try:
            vector_ops = self.metrics.get('vector_db_ops', [])
            
            if not vector_ops:
                return {'total_operations': 0}
            
            # Calculate metrics
            total_ops = len(vector_ops)
            successful_ops = sum(1 for op in vector_ops if op['success'])
            avg_response_time = sum(op['response_time'] for op in vector_ops) / total_ops
            
            # Operation breakdown
            op_counts = defaultdict(int)
            for op in vector_ops:
                op_counts[op['operation']] += 1
            
            return {
                'total_operations': total_ops,
                'successful_operations': successful_ops,
                'success_rate': (successful_ops / total_ops * 100) if total_ops > 0 else 0,
                'average_response_time': avg_response_time,
                'operation_breakdown': dict(op_counts)
            }
        except Exception as e:
            logger.error(f"Error getting vector DB metrics: {e}")
            return {}
    
    async def get_database_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get database-related metrics."""
        try:
            # Get query counts
            search_query_count = await db.execute(select(func.count(SearchQuery.id)))
            total_search_queries = search_query_count.scalar()
            
            session_count = await db.execute(select(func.count(UserSession.id)))
            total_sessions = session_count.scalar()
            
            feedback_count = await db.execute(select(func.count(Feedback.id)))
            total_feedback = feedback_count.scalar()
            
            # Get recent activity (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            recent_queries = await db.execute(
                select(func.count(SearchQuery.id))
                .where(SearchQuery.created_at >= cutoff_time)
            )
            recent_query_count = recent_queries.scalar()
            
            recent_sessions = await db.execute(
                select(func.count(UserSession.id))
                .where(UserSession.created_at >= cutoff_time)
            )
            recent_session_count = recent_sessions.scalar()
            
            return {
                'total_search_queries': total_search_queries,
                'total_sessions': total_sessions,
                'total_feedback': total_feedback,
                'recent_queries_24h': recent_query_count,
                'recent_sessions_24h': recent_session_count
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {}
    
    def get_comprehensive_metrics(self, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Get all metrics in one comprehensive report."""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'system': self.get_system_metrics(),
                'api': self.get_api_metrics(),
                'chat': self.get_chat_metrics(),
                'search': self.get_search_metrics(),
                'vector_db': self.get_vector_db_metrics()
            }
            
            if db:
                # This would need to be called from an async context
                pass
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting comprehensive metrics: {e}")
            return {'error': str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            system_metrics = self.get_system_metrics()
            api_metrics = self.get_api_metrics()
            
            # Determine health status
            health_issues = []
            
            # Check CPU usage
            if system_metrics.get('cpu_usage', {}).get('current', 0) > 80:
                health_issues.append("High CPU usage")
            
            # Check memory usage
            if system_metrics.get('memory_usage', {}).get('current', 0) > 85:
                health_issues.append("High memory usage")
            
            # Check error rate
            if api_metrics.get('error_rate', 0) > 5:
                health_issues.append("High error rate")
            
            # Check response time
            if api_metrics.get('average_response_time', 0) > 5:
                health_issues.append("Slow response times")
            
            status = "healthy" if not health_issues else "degraded" if len(health_issues) < 3 else "unhealthy"
            
            return {
                'status': status,
                'issues': health_issues,
                'uptime_seconds': system_metrics.get('uptime_seconds', 0),
                'active_requests': system_metrics.get('active_requests', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'unknown',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
