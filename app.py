"""
app.py — Streamlit UI for the Procurement & Tender Analysis Assistant.

Start with:
    streamlit run app.py
"""

import streamlit as st
import os

from config import CHROMA_DB_DIR, TENDER_DIR, GOOGLE_API_KEY

# ── Page configuration ───────────────────────────────────────────
st.set_page_config(
    page_title="Procurement & Tender Analysis Assistant",
    page_icon="📄",
    layout="centered",
)

# ── Title ────────────────────────────────────────────────────────
st.title("📄 Procurement & Tender Analysis Assistant")

# ── Information section ──────────────────────────────────────────
st.info(
    "Upload real tender or RFP PDF documents and ask questions about "
    "eligibility, deadlines, requirements, evaluation criteria and other "
    "important information."
)

# ── Check API key ────────────────────────────────────────────────
if not GOOGLE_API_KEY:
    st.error(
        "**GOOGLE_API_KEY is not set.** "
        "Create a `.env` file in the project folder with your key. "
        "Get a free key at https://aistudio.google.com/apikey"
    )
    st.stop()

# ── Sidebar — PDF Upload & Ingestion ────────────────────────────
st.sidebar.header("📁 Upload Tender PDFs")

uploaded_files = st.sidebar.file_uploader(
    "Choose one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    # Save uploaded files to data/tenders/
    os.makedirs(TENDER_DIR, exist_ok=True)
    saved_files = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(TENDER_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(uploaded_file.name)

    st.sidebar.success(f"Saved {len(saved_files)} file(s): {', '.join(saved_files)}")

# Show currently available PDFs
pdf_files = []
if os.path.exists(TENDER_DIR):
    pdf_files = [f for f in os.listdir(TENDER_DIR) if f.lower().endswith(".pdf")]

if pdf_files:
    st.sidebar.markdown("**Available PDFs:**")
    for f in pdf_files:
        st.sidebar.write(f"- {f}")
else:
    st.sidebar.warning("No PDF files found. Upload PDFs above.")

# Index / Re-index button
if pdf_files:
    if st.sidebar.button("🔄 Index Documents", type="primary"):
        with st.sidebar:
            with st.spinner("Indexing documents... This may take a minute."):
                from ingest import run_ingestion
                success, message = run_ingestion()

            if success:
                st.success(message)
                st.session_state["indexed"] = True
                st.rerun()
            else:
                st.error(f"Ingestion failed: {message}")

# ── Sidebar — Example Questions ─────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("💡 Example Questions")
example_questions = [
    "What are the eligibility criteria?",
    "What is the submission deadline?",
    "What documents are required from the bidder?",
    "What minimum experience is required?",
    "Is there a minimum annual turnover requirement?",
    "What are the evaluation criteria?",
    "What is the scope of work?",
    "What are the technical requirements?",
]
for q in example_questions:
    if st.sidebar.button(q, key=q):
        st.session_state["question"] = q

# ── Check if documents are indexed ───────────────────────────────
db_exists = os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR)

if not db_exists:
    st.warning(
        "📌 **No documents indexed yet.** "
        "Upload PDF files using the sidebar and click **Index Documents**."
    )
    st.stop()

# ── Question input ───────────────────────────────────────────────
st.subheader("Ask a Question")

question = st.text_input(
    "Ask a question about the tender...",
    value=st.session_state.get("question", ""),
    key="question_input",
)

ask_clicked = st.button("Ask", type="primary")

# ── Answer + Sources ─────────────────────────────────────────────
if ask_clicked and question.strip():
    with st.spinner("Searching tender documents..."):
        try:
            from rag import ask_question
            result = ask_question(question.strip())
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()

    # Display the answer
    st.subheader("Answer")
    st.markdown(result["answer"])

    # Display sources
    if result["sources"]:
        st.subheader("Sources")
        for i, src in enumerate(result["sources"], start=1):
            st.write(f"{i}. **{src['source']}** — Page {src['page']}")

    # Expandable section with retrieved text chunks
    if result.get("retrieved_docs"):
        with st.expander("📑 View Retrieved Context"):
            for i, doc in enumerate(result["retrieved_docs"], start=1):
                source = doc.metadata.get("source", "Unknown")
                page = int(doc.metadata.get("page", 0)) + 1
                st.markdown(f"**Chunk {i}** — {source}, Page {page}")
                st.text(doc.page_content[:500])
                st.divider()

elif ask_clicked:
    st.warning("Please enter a question.")
