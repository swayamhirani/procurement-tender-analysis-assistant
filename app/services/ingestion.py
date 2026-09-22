"""Document ingestion service for the Procurement & Tender Analysis Assistant.

Reads tender/RFP PDFs from data/tenders/, splits them into chunks, creates Gemini
embeddings with retry logic, and persists them in ChromaDB.
"""

import glob
import logging
import os
import time
from pathlib import Path
from typing import List, Tuple

import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)


def load_documents(tender_dir: Path) -> List[Document]:
    """Find all PDF files in the tender directory and load them page by page."""
    pdf_pattern = str(tender_dir / "*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        raise ValueError(f"No PDF files found in {tender_dir}")

    logger.info("Found %d PDF file(s) in %s", len(pdf_files), tender_dir)
    all_documents: List[Document] = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        logger.info("Loading PDF document: %s", filename)

        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            if not pages:
                logger.warning("Document %s is empty. Skipping.", filename)
                continue

            for page in pages:
                page.metadata["source"] = filename

            all_documents.extend(pages)
            logger.info("Successfully loaded %d page(s) from %s", len(pages), filename)

        except Exception as error:
            logger.error("Failed to load %s: %s", filename, error, exc_info=True)

    if not all_documents:
        raise ValueError("No pages could be extracted from the provided PDF files.")

    return all_documents


def split_documents(
    documents: List[Document],
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> List[Document]:
    """Split extracted pages into overlapping text chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = splitter.split_documents(documents)
    logger.info("Created %d chunk(s) from %d page(s)", len(chunks), len(documents))
    return chunks


def create_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Instantiate Google Generative AI embeddings using application settings."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not configured in settings or environment.")

    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
    )


def delete_old_collection(chroma_dir: Path, collection_name: str = "tender_docs") -> None:
    """Delete the previous Chroma collection so the index reflects current PDFs."""
    if not chroma_dir.exists():
        return

    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        try:
            client.delete_collection(collection_name)
            logger.info("Cleared existing Chroma collection: %s", collection_name)
        except Exception:
            # Collection may not exist yet
            pass
    except Exception as error:
        logger.warning("Could not clear old Chroma collection: %s", error)


def create_vector_store(
    chunks: List[Document],
    chroma_dir: Path,
    collection_name: str = "tender_docs",
) -> Chroma:
    """Embed document chunks in batches with exponential backoff and store in Chroma."""
    embeddings = create_embeddings()
    chroma_dir.mkdir(parents=True, exist_ok=True)
    delete_old_collection(chroma_dir, collection_name)

    logger.info("Creating embeddings for %d chunk(s)...", len(chunks))
    vector_store = None

    for start in range(0, len(chunks), settings.EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + settings.EMBEDDING_BATCH_SIZE]
        batch_num = (start // settings.EMBEDDING_BATCH_SIZE) + 1
        total_batches = (
            len(chunks) + settings.EMBEDDING_BATCH_SIZE - 1
        ) // settings.EMBEDDING_BATCH_SIZE

        logger.info("Embedding batch %d/%d (size: %d)...", batch_num, total_batches, len(batch))
        success = False

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                if vector_store is None:
                    vector_store = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=str(chroma_dir),
                        collection_name=collection_name,
                    )
                else:
                    vector_store.add_documents(batch)

                success = True
                logger.info("Batch %d completed successfully.", batch_num)
                break

            except Exception as error:
                error_text = str(error)
                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "rate" in error_text.lower()
                ):
                    wait_time = 2**attempt
                    logger.warning(
                        "Rate limit encountered. Retrying batch %d (attempt %d/%d) in %d seconds...",
                        batch_num,
                        attempt,
                        settings.MAX_RETRIES,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "Non-retryable error during embedding batch %d: %s", batch_num, error
                    )
                    raise error

        if not success:
            raise RuntimeError(
                f"Embedding generation failed after {settings.MAX_RETRIES} attempts for batch {batch_num}."
            )

        if start + settings.EMBEDDING_BATCH_SIZE < len(chunks):
            time.sleep(2)

    if vector_store is None:
        raise RuntimeError("No documents were added to Chroma.")

    logger.info("Successfully persisted %d chunks to ChromaDB at %s", len(chunks), chroma_dir)
    return vector_store


def run_ingestion() -> Tuple[bool, str, int, int]:
    """Execute complete ingestion pipeline.

    Returns:
        Tuple of (success: bool, message: str, doc_count: int, chunk_count: int)
    """
    tender_dir = settings.resolved_tender_dir
    chroma_dir = settings.resolved_chroma_dir

    if not settings.GOOGLE_API_KEY:
        msg = "GOOGLE_API_KEY is not set. Please configure it in your .env file."
        logger.error(msg)
        return False, msg, 0, 0

    try:
        documents = load_documents(tender_dir)
        unique_docs = {doc.metadata.get("source") for doc in documents}
        chunks = split_documents(documents)
        create_vector_store(chunks, chroma_dir)

        msg = f"Ingestion completed successfully. {len(chunks)} chunks indexed from {len(unique_docs)} documents."
        logger.info(msg)
        return True, msg, len(unique_docs), len(chunks)

    except Exception as error:
        logger.error("Ingestion pipeline failed: %s", error, exc_info=True)
        return False, str(error), 0, 0
