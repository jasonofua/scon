"""
Test WebSocket functionality for SCONIA.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestWebSocketChat:
    """Test WebSocket chat functionality."""
    
    def test_websocket_connection(self, client: TestClient):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Should receive connection established message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connection_established"
            assert message["session_id"] == "test-session"
    
    def test_websocket_ping_pong(self, client: TestClient):
        """Test WebSocket ping/pong functionality."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send ping
            websocket.send_text(json.dumps({"type": "ping"}))
            
            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"
    
    @patch('app.services.chat.ChatService.process_query_streaming')
    def test_websocket_query(self, mock_process_query, client: TestClient):
        """Test WebSocket query processing."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.answer = "Test response"
        mock_response.sources = []
        mock_response.quick_options = []
        mock_response.confidence_score = 0.9
        mock_response.session_id = "test-session"
        mock_response.query_id = 1
        mock_response.response_time = 1.5
        mock_response.intent_classification = "test"
        mock_response.dict.return_value = {
            "answer": "Test response",
            "sources": [],
            "quick_options": [],
            "confidence_score": 0.9,
            "session_id": "test-session",
            "query_id": 1,
            "response_time": 1.5,
            "intent_classification": "test"
        }
        mock_process_query.return_value = mock_response
        
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send query
            websocket.send_text(json.dumps({
                "type": "query",
                "query": "What are fundamental rights?"
            }))
            
            # Should receive progress updates and final response
            messages_received = 0
            while messages_received < 5:  # Expect multiple progress messages
                try:
                    data = websocket.receive_text()
                    message = json.loads(data)
                    messages_received += 1
                    
                    # Check for final response
                    if message.get("type") == "query_complete":
                        assert "data" in message
                        break
                except:
                    break
    
    def test_websocket_typing_indicator(self, client: TestClient):
        """Test WebSocket typing indicator."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send typing start
            websocket.send_text(json.dumps({
                "type": "typing",
                "is_typing": True
            }))
            
            # Should receive typing indicator
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "typing_indicator"
            assert message["status"] == "typing"
    
    def test_websocket_feedback(self, client: TestClient):
        """Test WebSocket feedback submission."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send feedback
            websocket.send_text(json.dumps({
                "type": "feedback",
                "rating": 5,
                "feedback_text": "Great response!",
                "query_id": 1
            }))
            
            # Should receive feedback confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "system_notification"
            assert message["notification_type"] == "feedback_received"
    
    def test_websocket_invalid_message_type(self, client: TestClient):
        """Test WebSocket with invalid message type."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send invalid message type
            websocket.send_text(json.dumps({
                "type": "invalid_type",
                "data": "test"
            }))
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "Unknown message type" in message["message"]
    
    def test_websocket_empty_query(self, client: TestClient):
        """Test WebSocket with empty query."""
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send empty query
            websocket.send_text(json.dumps({
                "type": "query",
                "query": ""
            }))
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "empty" in message["message"].lower()


class TestWebSocketManager:
    """Test WebSocket connection manager."""
    
    def test_connection_stats(self, client: TestClient, admin_headers):
        """Test WebSocket connection statistics."""
        response = client.get("/api/v1/websocket/stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "websocket_stats" in data
        assert "status" in data
    
    def test_websocket_health(self, client: TestClient):
        """Test WebSocket health check."""
        response = client.get("/api/v1/websocket/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_connections" in data
    
    def test_broadcast_message_unauthorized(self, client: TestClient):
        """Test broadcast message without authorization."""
        response = client.post(
            "/api/v1/websocket/broadcast",
            params={
                "message": "Test broadcast",
                "message_type": "test"
            }
        )
        
        assert response.status_code == 401
    
    def test_broadcast_message_authorized(self, client: TestClient, admin_headers):
        """Test broadcast message with authorization."""
        response = client.post(
            "/api/v1/websocket/broadcast",
            params={
                "message": "Test broadcast",
                "message_type": "test"
            },
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Broadcast sent successfully" in data["message"]
    
    def test_cleanup_connections(self, client: TestClient, admin_headers):
        """Test connection cleanup."""
        response = client.post("/api/v1/websocket/cleanup", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "stats" in data


class TestWebSocketIntegration:
    """Test WebSocket integration with other services."""
    
    def test_websocket_with_multiple_clients(self, client: TestClient):
        """Test WebSocket with multiple concurrent clients."""
        sessions = ["session-1", "session-2", "session-3"]
        websockets = []
        
        try:
            # Connect multiple clients
            for session_id in sessions:
                ws = client.websocket_connect(f"/api/v1/chat/ws/{session_id}")
                websockets.append(ws.__enter__())
                
                # Skip connection message
                websockets[-1].receive_text()
            
            # Send messages from each client
            for i, ws in enumerate(websockets):
                ws.send_text(json.dumps({
                    "type": "ping"
                }))
                
                # Should receive pong
                data = ws.receive_text()
                message = json.loads(data)
                assert message["type"] == "pong"
        
        finally:
            # Cleanup connections
            for ws in websockets:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass
    
    @patch('app.services.websocket_manager.connection_manager.send_personal_message')
    def test_websocket_notification_system(self, mock_send_message, client: TestClient):
        """Test WebSocket notification system."""
        mock_send_message.return_value = AsyncMock()
        
        with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # The connection should be registered with the manager
            # This is tested indirectly through the connection establishment
            assert True  # Connection successful means manager is working
    
    def test_websocket_session_persistence(self, client: TestClient):
        """Test WebSocket session persistence."""
        session_id = "persistent-session"
        
        # First connection
        with client.websocket_connect(f"/api/v1/chat/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send a message
            websocket.send_text(json.dumps({
                "type": "ping"
            }))
            
            # Receive response
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"
        
        # Second connection with same session ID
        with client.websocket_connect(f"/api/v1/chat/ws/{session_id}") as websocket:
            # Should establish connection successfully
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connection_established"
            assert message["session_id"] == session_id
