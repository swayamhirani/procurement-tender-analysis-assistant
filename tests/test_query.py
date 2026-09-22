"""Tests for query endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_query_validation_empty_body():
    """Test POST /api/query with missing body returns 422."""
    response = client.post("/api/query", json={})
    assert response.status_code == 422


def test_query_validation_blank_question():
    """Test POST /api/query with whitespace-only question returns 422."""
    response = client.post("/api/query", json={"question": "   "})
    assert response.status_code == 422


def test_query_successful_with_mock():
    """Test POST /api/query returns expected response structure when RAG executes."""
    mock_rag_result = {
        "answer": "The minimum average annual turnover required is INR 25 Lakhs.",
        "sources": [{"document": "GeM bid.pdf", "page": 6}],
        "context": [
            {
                "document": "GeM bid.pdf",
                "page": 6,
                "content": "Average Annual Turnover of bidder: Minimum 25 Lakhs",
            }
        ],
    }

    with patch("app.api.routes.query.ask_question", return_value=mock_rag_result):
        response = client.post(
            "/api/query",
            json={"question": "What is the turnover required?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == mock_rag_result["answer"]
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document"] == "GeM bid.pdf"
        assert data["sources"][0]["page"] == 6
        assert len(data["context"]) == 1
        assert "Turnover" in data["context"][0]["content"]
