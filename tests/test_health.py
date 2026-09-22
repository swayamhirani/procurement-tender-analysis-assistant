"""Tests for health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_root_endpoint():
    """Test the GET /health endpoint returns valid status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "procurement-tender-analysis-assistant"
    assert "gemini_configured" in data
    assert "documents_count" in data
    assert "indexed" in data
    assert "chroma_status" in data


def test_health_api_prefix_endpoint():
    """Test the GET /api/health endpoint returns valid status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "procurement-tender-analysis-assistant"
