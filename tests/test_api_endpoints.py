"""
Test API endpoints for SCONIA.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


class TestHealthEndpoints:
    """Test health and basic endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SCONIA" in data["message"]


class TestChatEndpoints:
    """Test chat API endpoints."""
    
    @patch('app.services.chat.ChatService.process_query')
    def test_chat_endpoint(self, mock_process_query, client: TestClient):
        """Test chat endpoint."""
        # Mock response
        mock_process_query.return_value = AsyncMock()
        mock_process_query.return_value.answer = "Test response"
        mock_process_query.return_value.sources = []
        mock_process_query.return_value.quick_options = []
        mock_process_query.return_value.confidence_score = 0.9
        mock_process_query.return_value.session_id = "test-session"
        mock_process_query.return_value.query_id = 1
        mock_process_query.return_value.response_time = 1.5
        mock_process_query.return_value.intent_classification = "test"
        
        response = client.post(
            "/api/v1/chat/",
            json={
                "query": "What are fundamental rights?",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "confidence_score" in data
    
    def test_chat_endpoint_empty_query(self, client: TestClient):
        """Test chat endpoint with empty query."""
        response = client.post(
            "/api/v1/chat/",
            json={
                "query": "",
                "session_id": "test-session"
            }
        )
        
        # Should handle empty query gracefully
        assert response.status_code in [200, 400]
    
    def test_chat_feedback(self, client: TestClient):
        """Test chat feedback endpoint."""
        response = client.post(
            "/api/v1/chat/feedback",
            params={
                "session_id": "test-session",
                "rating": 5,
                "feedback_text": "Great response!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestSearchEndpoints:
    """Test search API endpoints."""
    
    @patch('app.services.embeddings.embedding_service.generate_query_embedding')
    @patch('app.services.vector_db.vector_db_service.search_similar')
    def test_semantic_search(self, mock_search, mock_embedding, client: TestClient):
        """Test semantic search endpoint."""
        # Mock responses
        mock_embedding.return_value = [0.1] * 1536
        mock_search.return_value = [
            {
                "id": "test-doc-1",
                "text": "Test document content",
                "score": 0.9,
                "document_type": "constitution"
            }
        ]
        
        response = client.get(
            "/api/v1/search/semantic",
            params={"query": "fundamental rights", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_found" in data
    
    def test_search_suggestions(self, client: TestClient):
        """Test search suggestions endpoint."""
        response = client.get(
            "/api/v1/search/suggestions",
            params={"query": "const", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_search_stats(self, client: TestClient):
        """Test search statistics endpoint."""
        response = client.get("/api/v1/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestJudgesEndpoints:
    """Test judges API endpoints."""
    
    def test_get_judges(self, client: TestClient, sample_legal_data):
        """Test get judges endpoint."""
        response = client.get("/api/v1/judges/")
        
        assert response.status_code == 200
        data = response.json()
        assert "judges" in data
        assert "total_count" in data
        assert isinstance(data["judges"], list)
    
    def test_get_chief_justice(self, client: TestClient):
        """Test get chief justice endpoint."""
        response = client.get("/api/v1/judges/chief-justice")
        
        # May return 404 if no chief justice in test data
        assert response.status_code in [200, 404]
    
    def test_search_judges(self, client: TestClient):
        """Test search judges endpoint."""
        response = client.get("/api/v1/judges/search/test")
        
        assert response.status_code == 200
        data = response.json()
        assert "search_term" in data
        assert "results" in data
        assert "count" in data


class TestConstitutionEndpoints:
    """Test constitution API endpoints."""
    
    def test_get_constitutional_provisions(self, client: TestClient):
        """Test get constitutional provisions endpoint."""
        response = client.get("/api/v1/constitution/")
        
        assert response.status_code == 200
        data = response.json()
        assert "provisions" in data
        assert "total_count" in data
        assert isinstance(data["provisions"], list)
    
    def test_get_chapters(self, client: TestClient):
        """Test get chapters endpoint."""
        response = client.get("/api/v1/constitution/chapters")
        
        assert response.status_code == 200
        data = response.json()
        assert "chapters" in data
        assert "count" in data
    
    def test_get_fundamental_rights(self, client: TestClient):
        """Test get fundamental rights endpoint."""
        response = client.get("/api/v1/constitution/fundamental-rights")
        
        assert response.status_code == 200
        data = response.json()
        assert "chapter" in data
        assert "rights" in data
    
    def test_search_constitution(self, client: TestClient):
        """Test search constitution endpoint."""
        response = client.get(
            "/api/v1/constitution/search",
            params={"query": "rights", "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data


class TestFeesEndpoints:
    """Test fees API endpoints."""
    
    def test_get_fee_schedules(self, client: TestClient):
        """Test get fee schedules endpoint."""
        response = client.get("/api/v1/fees/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_service_types(self, client: TestClient):
        """Test get service types endpoint."""
        response = client.get("/api/v1/fees/service-types")
        
        assert response.status_code == 200
        data = response.json()
        assert "service_types" in data
        assert "count" in data
    
    def test_calculate_fees(self, client: TestClient):
        """Test calculate fees endpoint."""
        response = client.post(
            "/api/v1/fees/calculate",
            json={
                "service_type": "Appeal Filing",
                "case_category": "Civil Appeal"
            }
        )
        
        # May return 404 if no matching fee schedule
        assert response.status_code in [200, 404]


class TestProceduresEndpoints:
    """Test procedures API endpoints."""
    
    def test_get_procedures(self, client: TestClient):
        """Test get procedures endpoint."""
        response = client.get("/api/v1/procedures/")
        
        assert response.status_code == 200
        data = response.json()
        assert "procedures" in data
        assert "count" in data
    
    def test_get_procedure_categories(self, client: TestClient):
        """Test get procedure categories endpoint."""
        response = client.get("/api/v1/procedures/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "count" in data
    
    def test_get_required_forms(self, client: TestClient):
        """Test get required forms endpoint."""
        response = client.get("/api/v1/procedures/forms/")
        
        assert response.status_code == 200
        data = response.json()
        assert "forms" in data
        assert "count" in data


class TestCasesEndpoints:
    """Test cases API endpoints."""
    
    def test_get_cases(self, client: TestClient):
        """Test get cases endpoint."""
        response = client.get("/api/v1/cases/")
        
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "count" in data
        assert "total_count" in data
    
    def test_get_landmark_cases(self, client: TestClient):
        """Test get landmark cases endpoint."""
        response = client.get("/api/v1/cases/landmark/cases")
        
        assert response.status_code == 200
        data = response.json()
        assert "landmark_cases" in data
        assert "count" in data
    
    def test_get_recent_judgments(self, client: TestClient):
        """Test get recent judgments endpoint."""
        response = client.get("/api/v1/cases/recent/judgments")
        
        assert response.status_code == 200
        data = response.json()
        assert "recent_judgments" in data
        assert "count" in data
        assert "period_days" in data
    
    def test_search_by_case_number(self, client: TestClient):
        """Test search by case number endpoint."""
        response = client.get(
            "/api/v1/cases/search/by-number",
            params={"case_number": "TEST/2024/001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "case_number" in data
        assert "found" in data


class TestAdminEndpoints:
    """Test admin API endpoints."""
    
    def test_get_processed_documents_unauthorized(self, client: TestClient):
        """Test get processed documents without authorization."""
        response = client.get("/api/v1/admin/documents")
        
        assert response.status_code == 401
    
    def test_get_processed_documents_authorized(self, client: TestClient, admin_headers):
        """Test get processed documents with authorization."""
        response = client.get("/api/v1/admin/documents", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "count" in data
    
    def test_get_system_status(self, client: TestClient, admin_headers):
        """Test get system status endpoint."""
        response = client.get("/api/v1/admin/system/status", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_query_analytics(self, client: TestClient, admin_headers):
        """Test get query analytics endpoint."""
        response = client.get("/api/v1/admin/analytics/queries", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "period_days" in data


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_404_endpoint(self, client: TestClient):
        """Test non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_invalid_json(self, client: TestClient):
        """Test invalid JSON in request."""
        response = client.post(
            "/api/v1/chat/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test missing required fields in request."""
        response = client.post(
            "/api/v1/chat/",
            json={}  # Missing required 'query' field
        )
        
        assert response.status_code == 422
