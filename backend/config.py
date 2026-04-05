"""
Configuration module for the AI Sales Playbook Assistant.
Loads environment variables and provides configuration constants.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from backend directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)


class Config:
    """Application configuration loaded from environment variables."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Server
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    # RAG Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3

    @classmethod
    def validate(cls) -> list[str]:
        """Validate that all required configuration is set."""
        errors = []
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL is not set")
        if not cls.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY is not set")
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set")
        return errors


config = Config()
