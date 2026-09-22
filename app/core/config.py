"""Central configuration for Procurement & Tender Analysis Assistant.

Loads settings from environment variables and .env file using Pydantic Settings.
"""

from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Procurement & Tender Analysis Assistant"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # Google Gemini settings
    GOOGLE_API_KEY: str = Field(default="", description="Google AI Studio Gemini API Key")
    GEMINI_CHAT_MODEL: str = Field(
        default="gemini-3.6-flash", description="Gemini chat model identifier"
    )
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="models/gemini-embedding-001",
        description="Gemini embedding model identifier",
    )

    # Storage paths
    CHROMA_DB_DIR: str = Field(
        default="storage/chroma", description="Path for persistent ChromaDB store"
    )
    TENDER_DIR: str = Field(default="data/tenders", description="Directory containing tender PDFs")

    # CORS settings
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins",
    )

    # RAG hyperparameters (strictly preserved from prototype)
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVER_K: int = 10
    EMBEDDING_BATCH_SIZE: int = 10
    MAX_RETRIES: int = 5

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def resolved_chroma_dir(self) -> Path:
        p = Path(self.CHROMA_DB_DIR)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def resolved_tender_dir(self) -> Path:
        p = Path(self.TENDER_DIR)
        return p if p.is_absolute() else BASE_DIR / p


settings = Settings()
