# Procurement & Tender Analysis Assistant

A simple **Retrieval-Augmented Generation (RAG)** application that helps procurement consultants review real tender/RFP PDF documents and quickly find information such as eligibility criteria, submission deadlines, required qualifications, evaluation criteria, and more.

Built as an MVP for an AI/ML internship project.

---

## Why RAG?

Tender and RFP documents can be very long (50–200+ pages) and contain critical information scattered across different sections. Reading them end-to-end is time-consuming.

**RAG** solves this by:

1. **Indexing** the document into searchable chunks.
2. **Retrieving** only the most relevant chunks for a given question.
3. **Generating** a focused answer using only the retrieved context — so the LLM does not hallucinate.

---

## Architecture

```
Tender/RFP PDF
      ↓
PyPDFLoader          ← extracts text page-by-page
      ↓
Text Splitter        ← splits pages into ~1000-char overlapping chunks
      ↓
Embeddings           ← OpenAI text-embedding-3-small
      ↓
ChromaDB             ← persistent local vector database
      ↓
Retriever            ← similarity search, top-4 chunks
      ↓
LLM                  ← OpenAI gpt-4o-mini
      ↓
Answer + Sources     ← grounded answer with page references
```

---

## Project Structure

```
procurement-rag-mvp/
│
├── data/
│   └── tenders/         ← place your PDF files here
│       └── .gitkeep
│
├── chroma_db/           ← created automatically by ingest.py
│
├── app.py               ← Streamlit UI
├── ingest.py            ← document ingestion pipeline
├── rag.py               ← RAG query logic
├── config.py            ← configuration (reads .env)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup (Windows)

### 1. Create and activate a virtual environment

```bash
cd procurement-rag-mvp
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

Copy the example and add your OpenAI API key:

```bash
copy .env.example .env
```

Then open `.env` and replace `your_api_key_here` with your real OpenAI API key:

```
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Add tender PDFs

Place one or more real tender/RFP PDF files into:

```
data/tenders/
```

### 5. Run document ingestion

```bash
python ingest.py
```

You should see output like:

```
Loading documents...
Found 2 PDF file(s).
  Loading: Tender_2026.pdf
    → 45 page(s) loaded.
Creating chunks...
Created 120 chunk(s) from 45 page(s).
Creating embeddings and saving to Chroma...
✓ Ingestion completed successfully.
```

### 6. Start the application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Example Questions

Try asking:

- What are the eligibility criteria?
- What is the submission deadline?
- What documents are required from the bidder?
- What minimum experience is required?
- Is there a minimum annual turnover requirement?
- What are the evaluation criteria?
- What is the scope of work?
- What are the technical requirements?

---

## Testing

### With real tender PDFs

1. Place one or more public tender/RFP PDFs in `data/tenders/`.
2. Run `python ingest.py` — verify it completes without errors.
3. Run `streamlit run app.py` — verify the UI loads.
4. Ask a question whose answer **is** in the document (e.g., "What is the submission deadline?").
5. Verify the answer references the correct source and page.
6. Ask a question whose answer is **not** in the document (e.g., "What is the CEO's phone number?").
7. Verify the system says *"I could not find this information in the provided tender documents"* rather than making something up.

### Quick import check

```bash
python -c "from config import *; from rag import get_vector_store; print('All imports OK')"
```

---

## Technology Stack

| Component       | Library / Service          |
| --------------- | -------------------------- |
| PDF loading     | PyPDFLoader (LangChain)    |
| Text splitting  | RecursiveCharacterTextSplitter |
| Embeddings      | OpenAI text-embedding-3-small |
| Vector store    | ChromaDB                   |
| LLM             | OpenAI gpt-4o-mini         |
| RAG framework   | LangChain (LCEL)           |
| UI              | Streamlit                  |
| Configuration   | python-dotenv              |

---

## Limitations (MVP)

This is a minimal viable product. It does **not** include:

- Agents or multi-agent systems
- Hybrid search or reranking
- Authentication or user accounts
- Cloud deployment or Docker
- Vendor proposal comparison
- Automated procurement decision-making

These can be added as future enhancements.
