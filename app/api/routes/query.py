"""Tender Q&A Query endpoint."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ContextChunk, QueryRequest, QueryResponse, SourceItem
from app.services.rag import ask_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
def query_tender(request: QueryRequest) -> QueryResponse:
    """Query the tender analysis assistant using RAG."""
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        result = ask_question(question)

        sources = [
            SourceItem(document=src["document"], page=src["page"])
            for src in result.get("sources", [])
        ]
        context = [
            ContextChunk(
                document=ctx["document"],
                page=ctx["page"],
                content=ctx["content"],
            )
            for ctx in result.get("context", [])
        ]

        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            context=context,
        )

    except FileNotFoundError as fnf_err:
        logger.warning("Query rejected because vector database is missing: %s", fnf_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents have been indexed yet. Please upload PDFs and run indexing first.",
        )
    except ValueError as val_err:
        logger.error("Configuration error during query processing: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(val_err),
        )
    except Exception as err:
        logger.error("Error executing RAG query: %s", err, exc_info=True)
        err_msg = str(err)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini rate limit exceeded. Please wait a moment and try again.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing the tender documents. Please try again.",
        )
