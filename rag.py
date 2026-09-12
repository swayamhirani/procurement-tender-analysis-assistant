"""
rag.py — Retrieval-Augmented Generation logic.

Loads the persisted Chroma vector store, retrieves the most relevant
chunks for a user question, and asks Google Gemini to answer using only
the retrieved context.

Usage (from other modules):
    from rag import ask_question
    result = ask_question("What is the submission deadline?")
    print(result["answer"])
    print(result["sources"])
"""

import os
import sys

# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import Chroma
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
# pyrefly: ignore [missing-import]
from langchain_core.output_parsers import StrOutputParser
# pyrefly: ignore [missing-import]
from langchain_core.runnables import RunnablePassthrough

from config import (
    GOOGLE_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_EMBEDDING_MODEL,
    CHROMA_DB_DIR,
)

# Number of chunks to retrieve per question
RETRIEVER_K = 4

# ── System prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a Procurement & Tender Analysis Assistant.

Answer the user's question using ONLY the information provided in the retrieved tender/RFP context.

Do not invent or assume information.

If the answer cannot be found in the provided context, clearly say:
"I could not find this information in the provided tender documents."

When possible, mention the relevant source document name and page number in your answer.

Context:
{context}

Question:
{question}
"""


def get_vector_store():
    """
    Load the persisted Chroma database.
    Uses the same embedding model that was used during ingestion.
    """
    if not os.path.exists(CHROMA_DB_DIR):
        print("ERROR: Chroma database not found.")
        print("Run 'python ingest.py' first to index your tender PDFs.")
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
    Create a similarity-search retriever that returns the top-k
    most relevant chunks for a given query.
    """
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )
    return retriever


def format_docs(docs):
    """
    Combine retrieved Document objects into a single string
    that can be inserted into the prompt as context.
    """
    formatted = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        formatted.append(
            f"[Source: {source} | Page: {int(page) + 1}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(formatted)


def build_rag_chain():
    """
    Wire together: retriever -> prompt -> LLM -> string parser.
    This is the core RAG chain using LangChain Expression Language (LCEL).
    """
    retriever = get_retriever()

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_CHAT_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,  # deterministic answers for procurement use
    )

    # LCEL chain:
    #   1. Retrieve docs and pass-through the question
    #   2. Format docs into context string
    #   3. Fill prompt template
    #   4. Send to LLM
    #   5. Parse output to plain string
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def ask_question(question):
    """
    End-to-end RAG query.

    Returns a dict with:
        answer  — the LLM-generated answer
        sources — list of {"source": filename, "page": page_number} dicts
    """
    chain, retriever = build_rag_chain()

    # Retrieve the relevant chunks (we need them for source display)
    retrieved_docs = retriever.invoke(question)

    # Run the full chain to get the answer
    answer = chain.invoke(question)

    # Collect unique sources for display
    sources = []
    seen = set()
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "Unknown")
        page = int(doc.metadata.get("page", 0)) + 1  # 0-indexed -> 1-indexed
        key = (source, page)
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "page": page})

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_docs": retrieved_docs,
    }
