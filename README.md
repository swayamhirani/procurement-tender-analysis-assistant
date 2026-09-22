# Procurement & Tender Analysis Assistant

## Overview

The **Procurement & Tender Analysis Assistant** is a production-grade Retrieval-Augmented Generation (RAG) application designed to assist procurement consultants, bidders, and evaluators in reviewing lengthy, complex government tender and RFP (Request for Proposal) PDF documents (often 50–200+ pages).

Instead of manually searching through hundreds of pages, users can upload tender PDFs and query specific operational requirements, financial eligibility thresholds, submission deadlines, and evaluation criteria. Answers are strictly grounded in retrieved document context, preventing hallucinations and providing verifiable citations with document names and page numbers.

## Features

- **Automated Document Ingestion & Chunking**: Extracts text from multi-page tender PDFs using `PyPDFLoader` and segments them using `RecursiveCharacterTextSplitter` (1000 characters with 200 character overlap).
- **Persistent Vector Database**: Embeds document chunks using Google Gemini embeddings (`models/gemini-embedding-001`) with automatic retry and exponential backoff, storing vectors in a local persistent ChromaDB instance (`storage/chroma`).
- **Strict Grounding & Hallucination Prevention**: Uses Google Gemini (`gemini-3.6-flash`) with a strict procurement prompt ensuring answers rely strictly on retrieved context. If information is not present, it explicitly reports that the information could not be found.
- **Traceable Evidence & Citations**: Every response returns exact source document names and page numbers alongside full chunk text for complete auditability.
- **RESTful API Service**: Built on FastAPI with Pydantic v2 schemas, type hints, CORS support, and comprehensive error handling.
- **Modern Business Frontend**: A responsive, clean React + TypeScript + Vite interface providing dashboard metrics, document upload/indexing, interactive Q&A, and collapsible evidence viewer.
- **Production Tooling**: Managed with Astral UV for lightning-fast dependency resolution and virtual environments, Ruff for linting and formatting, and Pytest for automated unit testing.

## Architecture

```
Frontend (React + TypeScript + Vite)
      ↓ HTTP / JSON
FastAPI REST API (app.main)
      ↓
Application & Service Layer (app.services)
      ↓
LangChain RAG Pipeline
      ↓
ChromaDB (storage/chroma) + Google Gemini
```

## Project Structure

```
procurement-rag-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entrypoint & lifecycle
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py           # GET /health & /api/health
│   │       ├── documents.py        # Document upload, listing, and indexing
│   │       └── query.py            # POST /api/query RAG question answering
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py               # Pydantic Settings & environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic v2 request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ingestion.py            # PDF loading, splitting, and vector indexing
│   │   ├── retrieval.py            # ChromaDB connection & similarity retriever
│   │   └── rag.py                  # LangChain LCEL RAG chain & Gemini prompt
│   └── utils/
│       ├── __init__.py
│       └── logging.py              # Structured application logger
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DashboardHeader.tsx # Health status badge & metric summary
│   │   │   ├── DocumentManager.tsx # PDF upload & document indexing UI
│   │   │   ├── QuerySection.tsx    # Question input & quick example pills
│   │   │   └── AnswerCard.tsx      # Answer display, citations & evidence inspector
│   │   ├── services/
│   │   │   └── api.ts              # Frontend API client layer
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript data transfer interfaces
│   │   ├── App.tsx                 # Main application layout
│   │   ├── main.tsx                # React DOM render entrypoint
│   │   └── index.css               # Clean enterprise styling
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── data/
│   └── tenders/                    # Storage directory for uploaded tender PDFs
│
├── storage/
│   └── chroma/                     # Persistent Chroma vector database
│
├── tests/
│   ├── __init__.py
│   ├── test_health.py              # Health check endpoint unit tests
│   ├── test_documents.py           # Document listing & upload validation tests
│   └── test_query.py               # Query validation & mocked RAG tests
│
├── .env.example                    # Template environment variables
├── .gitignore                      # Git ignore rules for secrets, venv, and builds
├── pyproject.toml                  # UV project configuration and Ruff rules
├── uv.lock                         # UV locked dependency tree
└── README.md                       # Project documentation
```

## Requirements

- **Python**: `>= 3.10, < 3.14`
- **UV**: `>= 0.4.0` (Fast Python package and environment manager)
- **Node.js & npm**: Node `>= 18.0.0`, npm `>= 9.0.0`
- **Google Gemini API Key**: Free tier or standard key from [Google AI Studio](https://aistudio.google.com/apikey)

## Backend Setup

1. Install project dependencies using UV:

```bash
uv sync
```

## Environment Setup

1. Copy the example configuration to create your local `.env`:

```bash
copy .env.example .env
```

2. Edit `.env` and provide your Google AI Studio API key:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_CHAT_MODEL=gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
CHROMA_DB_DIR=storage/chroma
FRONTEND_ORIGIN=http://localhost:5173
```

## Run Backend

Start the FastAPI application with auto-reload:

```bash
uv run uvicorn app.main:app --reload
```

- **Backend API URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc**: `http://127.0.0.1:8000/redoc`

## Run Frontend

In a separate terminal, start the React + Vite frontend:

```bash
cd frontend
npm install
npm run dev
```

- **Frontend Application URL**: `http://localhost:5173`

## Workflow

```
PDF Document
     ↓
Upload to data/tenders/ via POST /api/documents/upload
     ↓
Index via POST /api/documents/index
     ↓
PyPDFLoader page extraction
     ↓
RecursiveCharacterTextSplitter (chunk size: 1000, overlap: 200)
     ↓
Google Generative AI Embeddings (with rate-limit backoff)
     ↓
ChromaDB persistent store (storage/chroma)
     ↓
Query via POST /api/query
     ↓
Similarity Search Retriever (top-10 chunks)
     ↓
Gemini 3.6 Flash inference with strictly grounded prompt
     ↓
Answer + Source Document Citations + Page Numbers
```

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Application health, Gemini configuration, and vector store readiness |
| `GET` | `/api/documents` | List stored tender PDF documents and metadata |
| `POST` | `/api/documents/upload` | Upload one or more tender/RFP PDF files |
| `POST` | `/api/documents/index` | Run the document ingestion and embedding pipeline into ChromaDB |
| `POST` | `/api/query` | Ask a question and receive grounded answers with citations |

### Example Query Request

```json
POST /api/query
Content-Type: application/json

{
  "question": "According to GeM bid.pdf, what is the minimum average annual turnover required for the bidder?"
}
```

### Example Query Response

```json
{
  "answer": "According to GeM bid.pdf, the bidder must have a minimum average annual turnover of INR 25 Lakhs across the specified financial years.",
  "sources": [
    {
      "document": "GeM bid.pdf",
      "page": 6
    }
  ],
  "context": [
    {
      "document": "GeM bid.pdf",
      "page": 6,
      "content": "Average Annual Turnover of the bidder: Minimum 25 Lakhs..."
    }
  ]
}
```

## Example Questions

- According to GeM bid.pdf, what is the minimum average annual turnover required for the bidder?
- What are the eligibility criteria?
- What is the contract period?
- What is the bid submission deadline?
- What is the evaluation method?

## Testing

Run automated tests using UV and Pytest:

```bash
uv run pytest
```

## Code Quality

Check and format code using Ruff:

```bash
# Check code for lint errors
uv run ruff check .

# Automatically apply fixes
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Current Limitations

- Only document-based Q&A is currently supported (no vendor proposal evaluation or scoring).
- PDF is the only supported document format.

## Future Improvements

- Support for comparing multiple vendor bids side-by-side in structured tables.
- Optical Character Recognition (OCR) integration for scanned or image-only tender PDFs.
- Export analysis reports to PDF / Excel.
