"""
ingest.py — Document ingestion pipeline.

Reads tender/RFP PDFs from data/tenders/, splits them into chunks,
generates embeddings with Google Gemini, and stores everything in a
persistent ChromaDB vector database.

Usage (command line):
    python ingest.py

Usage (from other modules):
    from ingest import run_ingestion
    success, message = run_ingestion()
"""

import os
import glob
import sys
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from config import GOOGLE_API_KEY, GEMINI_EMBEDDING_MODEL, CHROMA_DB_DIR, TENDER_DIR

# ── Chunking parameters (easy to tune later) ────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_documents():
    """
    Find every PDF in TENDER_DIR and load it with PyPDFLoader.
    Returns a flat list of Document objects (one per page).
    Raises ValueError if no PDFs found or no pages extracted.
    """
    pdf_pattern = os.path.join(TENDER_DIR, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        raise ValueError(f"No PDF files found in {TENDER_DIR}")

    print(f"Found {len(pdf_files)} PDF file(s).")

    all_documents = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"  Loading: {filename}")
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            if not pages:
                print(f"  WARNING: {filename} appears to be empty -- skipping.")
                continue

            # Store just the filename (not the full path) for cleaner display
            for page in pages:
                page.metadata["source"] = filename

            all_documents.extend(pages)
            print(f"    => {len(pages)} page(s) loaded.")
        except Exception as e:
            print(f"  WARNING: Failed to load {filename}: {e}")

    if not all_documents:
        raise ValueError("No pages could be extracted from the PDFs.")

    return all_documents


def split_documents(documents):
    """
    Split pages into smaller, overlapping chunks so that each chunk
    fits within the embedding model's context and retrieval is precise.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunk(s) from {len(documents)} page(s).")
    return chunks


def create_vector_store(chunks):
    """
    Embed every chunk with Google Gemini and persist the vectors in ChromaDB.
    Clears any existing collection first so the index always reflects
    the current set of PDFs.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set. Create a .env file with your key.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )

    # If the database already exists, delete the old collection to avoid stale data
    # (We use the Chroma API instead of deleting files, to avoid lock errors)
    if os.path.exists(CHROMA_DB_DIR):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
            try:
                client.delete_collection("tender_docs")
                print("Cleared old collection.")
            except Exception:
                pass  # Collection may not exist yet
        except Exception:
            pass

    # Create the Chroma collection with new documents
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
        collection_name="tender_docs",
    )

    print(f"Saved {len(chunks)} chunk(s) to Chroma at: {CHROMA_DB_DIR}")
    return vector_store


def run_ingestion():
    """
    Run the full ingestion pipeline.
    Returns (success: bool, message: str).
    Can be called from Streamlit or from the command line.
    """
    try:
        if not GOOGLE_API_KEY:
            return False, "GOOGLE_API_KEY is not set. Add it to your .env file."

        # Step 1 -- Load PDFs
        print("Loading documents...")
        documents = load_documents()

        # Step 2 -- Split into chunks
        print("Creating chunks...")
        chunks = split_documents(documents)

        # Step 3 -- Embed and store
        print("Creating embeddings and saving to Chroma...")
        create_vector_store(chunks)

        msg = f"Ingestion completed successfully. {len(chunks)} chunks indexed."
        print(msg)
        return True, msg

    except Exception as e:
        return False, str(e)


# ── CLI entry point ──────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Procurement RAG MVP -- Document Ingestion")
    print("=" * 55)

    success, message = run_ingestion()
    if success:
        print(f"\n{message}")
        print("You can now run:  streamlit run app.py")
    else:
        print(f"\nERROR: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
