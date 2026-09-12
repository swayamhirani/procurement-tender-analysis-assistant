"""
config.py — Central configuration for the Procurement RAG MVP.

Loads settings from a .env file so that API keys and model names
are never hard-coded in the source.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Google Gemini settings (FREE tier available) ─────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

# ── Directory paths ──────────────────────────────────────────────
# Where the Chroma vector database is persisted
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Where the user places tender/RFP PDF files
TENDER_DIR = os.path.join(os.path.dirname(__file__), "data", "tenders")
