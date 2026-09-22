"""Health check endpoint."""

import os

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import HealthResponse
from app.services.retrieval import is_vector_store_ready

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return the health status of the application and its storage."""
    tender_dir = settings.resolved_tender_dir
    pdf_count = 0
    if tender_dir.exists():
        pdf_count = len([f for f in os.listdir(tender_dir) if f.lower().endswith(".pdf")])

    vector_ready = is_vector_store_ready()

    return HealthResponse(
        status="ok",
        service="procurement-tender-analysis-assistant",
        gemini_configured=bool(settings.GOOGLE_API_KEY),
        documents_count=pdf_count,
        indexed=vector_ready,
        chroma_status="ready" if vector_ready else "unindexed",
    )
