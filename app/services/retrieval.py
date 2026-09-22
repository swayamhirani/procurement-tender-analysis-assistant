"""Vector database and document retrieval services."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


def _ensure_chroma_storage_exists() -> Path:
    """Ensure ChromaDB storage exists, seamlessly migrating legacy chroma_db if present."""
    target_dir = settings.resolved_chroma_dir

    if target_dir.exists() and any(target_dir.iterdir()):
        return target_dir

    # Check for legacy chroma_db in the root
    legacy_dir = settings.resolved_chroma_dir.parent.parent / "chroma_db"
    if legacy_dir.exists() and any(legacy_dir.iterdir()):
        logger.info("Migrating existing vector database from %s to %s", legacy_dir, target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(str(legacy_dir), str(target_dir), dirs_exist_ok=True)
            return target_dir
        except Exception as err:
            logger.warning("Could not auto-copy legacy chroma_db: %s", err)

    return target_dir


def is_vector_store_ready() -> bool:
    """Check whether a populated ChromaDB store is accessible."""
    target_dir = _ensure_chroma_storage_exists()
    if not target_dir.exists():
        return False

    # Check if there is an existing sqlite file or collection directory
    has_files = any(target_dir.glob("*.sqlite3")) or any(target_dir.iterdir())
    return has_files


def get_vector_store() -> Chroma:
    """Load the persisted Chroma vector database."""
    target_dir = _ensure_chroma_storage_exists()

    if not is_vector_store_ready():
        raise FileNotFoundError(
            "Vector database not found. Please upload tender PDFs and run indexing first."
        )

    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not configured. Please add it to your .env file.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
    )

    vector_store = Chroma(
        persist_directory=str(target_dir),
        embedding_function=embeddings,
        collection_name="tender_docs",
    )

    return vector_store


def get_retriever(k: Optional[int] = None) -> VectorStoreRetriever:
    """Create a similarity-search retriever configured with top-k chunks."""
    retrieval_k = k or settings.RETRIEVER_K
    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": retrieval_k},
    )
