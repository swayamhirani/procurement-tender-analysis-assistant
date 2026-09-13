"""
ingest.py - Document ingestion pipeline.

Reads tender/RFP PDFs from data/tenders/,
splits them into chunks, creates Gemini embeddings,
and stores them in ChromaDB.
"""

import os
import glob
import sys
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from config import (
    GOOGLE_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    CHROMA_DB_DIR,
    TENDER_DIR,
)


# Chunking settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Number of documents embedded in one request/batch
EMBEDDING_BATCH_SIZE = 10

# Maximum retry attempts for temporary API errors
MAX_RETRIES = 5


def load_documents():
    """
    Find all PDF files in the tender directory
    and load them page by page.
    """

    pdf_pattern = os.path.join(TENDER_DIR, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        raise ValueError(
            f"No PDF files found in {TENDER_DIR}"
        )

    print(f"Found {len(pdf_files)} PDF file(s).")

    all_documents = []

    for pdf_path in pdf_files:

        filename = os.path.basename(pdf_path)

        print(f"  Loading: {filename}")

        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            if not pages:
                print(
                    f"  WARNING: {filename} is empty. Skipping."
                )
                continue

            # Store only filename as source metadata
            for page in pages:
                page.metadata["source"] = filename

            all_documents.extend(pages)

            print(
                f"    => {len(pages)} page(s) loaded."
            )

        except Exception as error:
            print(
                f"  WARNING: Failed to load "
                f"{filename}: {error}"
            )

    if not all_documents:
        raise ValueError(
            "No pages could be extracted from the PDFs."
        )

    return all_documents


def split_documents(documents):
    """
    Split pages into smaller overlapping chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    print(
        f"Created {len(chunks)} chunk(s) "
        f"from {len(documents)} page(s)."
    )

    return chunks


def create_embeddings():
    """
    Create the Gemini embedding model.
    """

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Add it to your .env file."
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )

    return embeddings


def delete_old_collection():
    """
    Delete the previous Chroma collection so that
    the database contains only the current PDFs.
    """

    if not os.path.exists(CHROMA_DB_DIR):
        return

    try:

        import chromadb

        client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR
        )

        try:
            client.delete_collection("tender_docs")
            print("Cleared old collection.")

        except Exception:
            # Collection may not exist
            pass

    except Exception as error:

        print(
            f"Warning: Could not clear old collection: "
            f"{error}"
        )


def create_vector_store(chunks):
    """
    Create embeddings and store chunks in ChromaDB.

    Embeddings are created in small batches to reduce
    the chance of Gemini API rate-limit errors.
    """

    embeddings = create_embeddings()

    delete_old_collection()

    print(
        f"Creating embeddings for {len(chunks)} chunks..."
    )

    vector_store = None

    # Process chunks in small batches
    for start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE
    ):

        batch = chunks[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        batch_number = (
            start // EMBEDDING_BATCH_SIZE
        ) + 1

        total_batches = (
            (len(chunks) + EMBEDDING_BATCH_SIZE - 1)
            // EMBEDDING_BATCH_SIZE
        )

        print(
            f"Embedding batch "
            f"{batch_number}/{total_batches}..."
        )

        success = False

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                if vector_store is None:

                    vector_store = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=CHROMA_DB_DIR,
                        collection_name="tender_docs",
                    )

                else:

                    vector_store.add_documents(batch)

                success = True

                print(
                    f"  Batch {batch_number} completed."
                )

                break

            except Exception as error:

                error_text = str(error)

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED"
                    in error_text
                    or "rate" in error_text.lower()
                ):

                    wait_time = 2 ** attempt

                    print(
                        f"  Rate limit reached. "
                        f"Retry {attempt}/{MAX_RETRIES} "
                        f"after {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:

                    raise error

        if not success:

            raise RuntimeError(
                "Gemini embedding failed after "
                f"{MAX_RETRIES} retries for "
                f"batch {batch_number}."
            )

        # Small pause between batches
        # to reduce API pressure.
        if start + EMBEDDING_BATCH_SIZE < len(chunks):
            time.sleep(2)

    if vector_store is None:
        raise RuntimeError(
            "No documents were added to Chroma."
        )

    print(
        f"Saved {len(chunks)} chunk(s) to Chroma "
        f"at: {CHROMA_DB_DIR}"
    )

    return vector_store


def run_ingestion():
    """
    Run the complete ingestion pipeline.

    Returns:
        (success, message)
    """

    try:

        if not GOOGLE_API_KEY:

            return (
                False,
                "GOOGLE_API_KEY is not set. "
                "Add it to your .env file."
            )

        # Step 1
        print("Loading documents...")
        documents = load_documents()

        # Step 2
        print("Creating chunks...")
        chunks = split_documents(documents)

        # Step 3
        print(
            "Creating embeddings and "
            "saving to Chroma..."
        )

        create_vector_store(chunks)

        message = (
            f"Ingestion completed successfully. "
            f"{len(chunks)} chunks indexed."
        )

        print(message)

        return True, message

    except Exception as error:

        return False, str(error)


def main():

    print("=" * 55)
    print("  Procurement RAG MVP - Document Ingestion")
    print("=" * 55)

    success, message = run_ingestion()

    if success:

        print(f"\n{message}")

        print(
            "\nYou can now run:"
        )

        print(
            "streamlit run app.py"
        )

    else:

        print(
            f"\nERROR: {message}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()