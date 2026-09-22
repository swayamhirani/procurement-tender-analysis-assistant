"""Tests for document upload and listing endpoints."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_documents():
    """Test GET /api/documents returns a valid list."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_upload_non_pdf_rejected():
    """Test POST /api/documents/upload rejects non-PDF files."""
    file_content = b"Not a real PDF file"
    files = [("files", ("sample.txt", io.BytesIO(file_content), "text/plain"))]

    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Only PDF files are accepted" in data["detail"]


def test_upload_valid_pdf(tmp_path, monkeypatch):
    """Test POST /api/documents/upload successfully accepts a PDF."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "TENDER_DIR", str(tmp_path))

    pdf_content = b"%PDF-1.4 sample pdf content %%EOF"
    files = [("files", ("test_tender.pdf", io.BytesIO(pdf_content), "application/pdf"))]

    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "uploaded_files" in data
    assert len(data["uploaded_files"]) == 1
    assert data["uploaded_files"][0]["filename"] == "test_tender.pdf"
    assert (tmp_path / "test_tender.pdf").exists()
