"""
rag.py - Retrieval-Augmented Generation logic.

Loads the persisted Chroma vector store, retrieves relevant
tender/RFP chunks, and asks Gemini to answer using the
retrieved context.
"""

import os
import sys

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import (
    GOOGLE_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_EMBEDDING_MODEL,
    CHROMA_DB_DIR,
)


# Number of document chunks to retrieve
RETRIEVER_K = 10


# Prompt used by the LLM
SYSTEM_PROMPT = """
You are a Procurement & Tender Analysis Assistant.

Answer the user's question using ONLY the information provided
in the retrieved tender/RFP context.

Do not invent or assume information.

If the answer cannot be found in the provided context, say:

"I could not find this information in the provided tender documents."

When possible, mention the relevant source document and page number.

Retrieved context:
{context}

Question:
{question}
"""


def get_vector_store():
    """
    Load the existing Chroma vector database.
    """

    if not os.path.exists(CHROMA_DB_DIR):
        print("ERROR: Chroma database not found.")
        print("Run 'python ingest.py' first.")
        sys.exit(1)

    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY is missing.")
        print("Add it to your .env file.")
        sys.exit(1)

    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="tender_docs",
    )

    return vector_store


def get_retriever():
    """
    Create a similarity-search retriever.
    """

    vector_store = get_vector_store()

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )

    return retriever


def format_docs(docs):
    """
    Convert retrieved documents into text for the LLM prompt.
    """

    formatted_docs = []

    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", 0)

        try:
            page_number = int(page) + 1
        except (ValueError, TypeError):
            page_number = "Unknown"

        formatted_docs.append(
            f"[Source: {source} | Page: {page_number}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(formatted_docs)


def build_rag_chain():
    """
    Build the basic RAG pipeline:

    Question
        ↓
    Retriever
        ↓
    Relevant documents
        ↓
    Prompt
        ↓
    Gemini
        ↓
    Answer
    """

    retriever = get_retriever()

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_CHAT_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def ask_question(question):
    """
    Ask a question using the RAG system.

    Returns:
        answer
        sources
        retrieved_docs
    """

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "retrieved_docs": [],
        }

    chain, retriever = build_rag_chain()

    # Retrieve relevant document chunks
    retrieved_docs = retriever.invoke(question)

    # Generate answer using retrieved context
    answer = chain.invoke(question)

    # Collect unique sources
    sources = []
    seen = set()

    for doc in retrieved_docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", 0)

        try:
            page_number = int(page) + 1
        except (ValueError, TypeError):
            page_number = "Unknown"

        key = (source, page_number)

        if key not in seen:
            seen.add(key)

            sources.append(
                {
                    "source": source,
                    "page": page_number,
                }
            )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_docs": retrieved_docs,
    }