"""Data transfer models and validation schemas using Pydantic v2."""

from typing import List, Union

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    service: str = Field(
        default="procurement-tender-analysis-assistant",
        json_schema_extra={"example": "procurement-tender-analysis-assistant"},
    )
    gemini_configured: bool = Field(..., json_schema_extra={"example": True})
    documents_count: int = Field(..., json_schema_extra={"example": 3})
    indexed: bool = Field(..., json_schema_extra={"example": True})
    chroma_status: str = Field(..., json_schema_extra={"example": "ready"})


class DocumentInfo(BaseModel):
    filename: str = Field(..., json_schema_extra={"example": "GeM bid.pdf"})
    size_bytes: int = Field(..., json_schema_extra={"example": 119381})
    modified_at: str = Field(..., json_schema_extra={"example": "2026-09-18T14:00:00Z"})


class DocumentUploadResponse(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Uploaded 1 document(s) successfully."})
    uploaded_files: List[DocumentInfo]


class DocumentListResponse(BaseModel):
    total: int = Field(..., json_schema_extra={"example": 2})
    documents: List[DocumentInfo]


class IndexResponse(BaseModel):
    success: bool = Field(..., json_schema_extra={"example": True})
    message: str = Field(
        ...,
        json_schema_extra={"example": "Ingestion completed successfully. 120 chunks indexed."},
    )
    documents_indexed: int = Field(..., json_schema_extra={"example": 2})
    chunks_indexed: int = Field(..., json_schema_extra={"example": 120})


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="The procurement/tender question to ask",
        json_schema_extra={"example": "What is the minimum annual turnover required?"},
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or solely whitespace.")
        return v.strip()


class SourceItem(BaseModel):
    document: str = Field(..., json_schema_extra={"example": "GeM bid.pdf"})
    page: Union[int, str] = Field(..., json_schema_extra={"example": 6})


class ContextChunk(BaseModel):
    document: str = Field(..., json_schema_extra={"example": "GeM bid.pdf"})
    page: Union[int, str] = Field(..., json_schema_extra={"example": 6})
    content: str = Field(
        ...,
        json_schema_extra={"example": "The bidder must have minimum average annual turnover..."},
    )


class QueryResponse(BaseModel):
    answer: str = Field(
        ...,
        json_schema_extra={
            "example": "The minimum average annual turnover required is INR 25 Lakhs."
        },
    )
    sources: List[SourceItem] = Field(
        default_factory=list,
        json_schema_extra={"example": [{"document": "GeM bid.pdf", "page": 6}]},
    )
    context: List[ContextChunk] = Field(
        default_factory=list,
        description="Retrieved chunk snippets for user inspection",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        json_schema_extra={"example": "Invalid file format. Only PDF files are supported."},
    )
