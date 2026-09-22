"""FastAPI Application entry point for Procurement & Tender Analysis Assistant."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.core.config import settings
from app.utils.logging import setup_logging

# Configure structured application logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown routines."""
    logger.info("Initializing %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    settings.resolved_tender_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_chroma_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Tender directory: %s", settings.resolved_tender_dir)
    logger.info("ChromaDB storage: %s", settings.resolved_chroma_dir)
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade FastAPI backend for the Procurement & Tender Analysis Assistant. "
        "Provides PDF document ingestion, Chroma vector store indexing, and LangChain RAG "
        "question-answering powered by Google Gemini."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
cors_origins = (
    settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions without leaking sensitive internal details."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


# Register routes
app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(query_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint pointing to interactive documentation."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
