import os
from pathlib import Path

from dotenv import load_dotenv


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if it exists
load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME = "Biodiversity Intelligence AI"
    APP_VERSION = "1.0.0"

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'biodiversity.db'}"
    )

    # AI / LLM
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_BASE_URL = os.getenv(
        "LLM_BASE_URL",
        "https://api.openai.com/v1"
    )

    # Local retrieval
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "tfidf-local"
    )

    # Data directories
    DATA_DIR = BASE_DIR / "data"
    DOCUMENTS_DIR = DATA_DIR / "documents"
    DATASETS_DIR = DATA_DIR / "datasets"
    FRONTEND_DIR = BASE_DIR / "frontend"


settings = Settings()