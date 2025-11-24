import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self):
        """Health check should return 200 with status ok"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    def test_health_check_has_correct_fields(self):
        """Health check should return all required fields"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "app_name" in data


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root(self):
        """Root endpoint should return welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]

    def test_root_has_navigation_links(self):
        """Root should provide links to key endpoints"""
        response = client.get("/")
        data = response.json()
        assert "docs" in data
        assert "health" in data
        assert "api" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
        assert data["api"] == "/api/v1"


class TestAPIv1:
    """Test API v1 endpoints"""

    def test_api_v1_root(self):
        """API v1 root should return version and endpoints"""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"
        assert "endpoints" in data

    def test_api_v1_lists_future_endpoints(self):
        """API v1 should list planned endpoint paths"""
        response = client.get("/api/v1/")
        data = response.json()
        endpoints = data["endpoints"]
        assert "auth" in endpoints
        assert "users" in endpoints
        assert "challenges" in endpoints
        assert "habits" in endpoints


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers_present(self):
        """CORS headers should be present in responses"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:19006",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_configured_origin(self):
        """CORS should allow configured origins"""
        response = client.get("/health", headers={"Origin": "http://localhost:19006"})
        assert response.status_code == 200
        # CORS middleware should add the header
        assert "access-control-allow-origin" in response.headers


class TestMiddleware:
    """Test middleware functionality"""

    def test_request_logging_adds_process_time_header(self):
        """Request logging middleware should add X-Process-Time header"""
        response = client.get("/health")
        assert "x-process-time" in response.headers
        # Process time should be a valid float string
        process_time = float(response.headers["x-process-time"])
        assert process_time >= 0


class TestDocs:
    """Test API documentation endpoints"""

    def test_swagger_docs_accessible(self):
        """Swagger UI should be accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self):
        """ReDoc should be accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self):
        """OpenAPI schema should be accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        # Title comes from APP_NAME env var
        assert "DareZone" in data["info"]["title"]
