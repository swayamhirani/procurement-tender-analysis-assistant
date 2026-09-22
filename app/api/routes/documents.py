"""Document upload and indexing endpoints."""

import datetime
import logging
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.schemas import (
    DocumentInfo,
    DocumentListResponse,
    DocumentUploadResponse,
    IndexResponse,
)
from app.services.ingestion import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    """List all tender PDFs currently saved in the data directory."""
    tender_dir = settings.resolved_tender_dir
    if not tender_dir.exists():
        return DocumentListResponse(total=0, documents=[])

    docs: List[DocumentInfo] = []
    for entry in tender_dir.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            stat = entry.stat()
            mod_time = datetime.datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).isoformat()
            docs.append(
                DocumentInfo(
                    filename=entry.name,
                    size_bytes=stat.st_size,
                    modified_at=mod_time,
                )
            )

    docs.sort(key=lambda d: d.filename.lower())
    return DocumentListResponse(total=len(docs), documents=docs)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(files: List[UploadFile] = File(...)) -> DocumentUploadResponse:
    """Upload one or more tender/RFP PDF files."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided in the upload request.",
        )

    tender_dir = settings.resolved_tender_dir
    tender_dir.mkdir(parents=True, exist_ok=True)

    uploaded: List[DocumentInfo] = []

    for file in files:
        safe_filename = Path(file.filename or "").name
        if not safe_filename or not safe_filename.lower().endswith(".pdf"):
            logger.warning("Rejected non-PDF upload attempt: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is not a PDF. Only PDF files are accepted.",
            )

        destination = tender_dir / safe_filename

        try:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            stat = destination.stat()
            mod_time = datetime.datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).isoformat()

            uploaded.append(
                DocumentInfo(
                    filename=safe_filename,
                    size_bytes=stat.st_size,
                    modified_at=mod_time,
                )
            )
            logger.info("Saved uploaded document: %s (%d bytes)", safe_filename, stat.st_size)

        except Exception as err:
            logger.error("Failed to save uploaded file %s: %s", safe_filename, err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not save file '{safe_filename}': {str(err)}",
            )
        finally:
            await file.close()

    return DocumentUploadResponse(
        message=f"Successfully uploaded {len(uploaded)} document(s).",
        uploaded_files=uploaded,
    )


@router.post("/index", response_model=IndexResponse)
def index_documents() -> IndexResponse:
    """Run the ingestion and indexing pipeline on all stored tender PDFs."""
    logger.info("Triggered document indexing pipeline via API")
    success, message, doc_count, chunk_count = run_ingestion()

    if not success:
        logger.error("Indexing failed: %s", message)
        if "No PDF files found" in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )

    return IndexResponse(
        success=True,
        message=message,
        documents_indexed=doc_count,
        chunks_indexed=chunk_count,
    )
