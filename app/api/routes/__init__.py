"""API Route definitions."""

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router

__all__ = ["health_router", "documents_router", "query_router"]
