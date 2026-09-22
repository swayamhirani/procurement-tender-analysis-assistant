"""Retrieval-Augmented Generation (RAG) service.

Answers tender questions using Gemini strictly grounded in context retrieved from ChromaDB.
"""

import logging
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.services.retrieval import get_retriever

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Procurement & Tender Analysis Assistant.

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


def format_docs(docs: List[Document]) -> str:
    """Format retrieved document chunks for inclusion in the LLM prompt."""
    formatted_docs = []

    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        raw_page = doc.metadata.get("page", 0)

        try:
            page_number = int(raw_page) + 1
        except (ValueError, TypeError):
            page_number = "Unknown"

        formatted_docs.append(f"[Source: {source} | Page: {page_number}]\n{doc.page_content}")

    return "\n\n---\n\n".join(formatted_docs)


def build_rag_chain():
    """Build the LangChain RAG pipeline: Retriever -> Prompt -> Gemini -> StrOutputParser."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing. Please set it in your .env file.")

    retriever = get_retriever(k=settings.RETRIEVER_K)
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
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


def ask_question(question: str) -> Dict[str, Any]:
    """Execute the RAG workflow for a user query.

    Args:
        question: User query string.

    Returns:
        Dict containing:
            - answer: The generated response
            - sources: Unique list of {"document": str, "page": int | str}
            - context: List of retrieved chunks with snippet content
    """
    clean_question = question.strip() if question else ""
    if not clean_question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "context": [],
        }

    logger.info("Processing RAG query: %s", clean_question)
    chain, retriever = build_rag_chain()

    # Retrieve relevant document chunks
    retrieved_docs: List[Document] = retriever.invoke(clean_question)
    logger.info("Retrieved %d relevant context chunk(s)", len(retrieved_docs))

    # Generate answer using LLM
    answer: str = chain.invoke(clean_question)

    # Deduplicate sources preserving order
    sources = []
    seen = set()
    context_chunks = []

    for doc in retrieved_docs:
        source_name = doc.metadata.get("source", "Unknown")
        raw_page = doc.metadata.get("page", 0)

        try:
            page_number = int(raw_page) + 1
        except (ValueError, TypeError):
            page_number = "Unknown"

        key = (source_name, page_number)
        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "document": source_name,
                    "page": page_number,
                }
            )

        context_chunks.append(
            {
                "document": source_name,
                "page": page_number,
                "content": doc.page_content,
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "context": context_chunks,
    }
