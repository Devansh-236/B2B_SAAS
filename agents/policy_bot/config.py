"""
Configuration settings for the Policy Bot agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve relative paths against this directory so the bot behaves the same
# no matter which working directory it is launched from.
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file next to this module
load_dotenv(BASE_DIR / ".env")


def _path_from_env(name: str, default: str) -> str:
    value = Path(os.getenv(name, default))
    if not value.is_absolute():
        value = BASE_DIR / value
    return str(value)


def _list_from_env(name: str, default: str) -> list:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# LLM API Configuration
LLM_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")

# Vector Database Configuration
VECTOR_DB_PATH = _path_from_env("VECTOR_DB_PATH", "knowledge_base/vector_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Document Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_CHUNKS_RETRIEVED = int(os.getenv("MAX_CHUNKS_RETRIEVED", "5"))

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
WEB_PORT = int(os.getenv("WEB_PORT", "8001"))
API_TITLE = "Policy Bot API"
API_DESCRIPTION = "HR Policy Bot for answering employee questions"
CORS_ORIGINS = _list_from_env("CORS_ORIGINS", "http://localhost:8001,http://127.0.0.1:8001")
# Optional shared secret. When set, clients must send it in the X-API-Key header.
API_KEY = os.getenv("POLICY_BOT_API_KEY", "")
MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "1000"))

# File Paths
KNOWLEDGE_BASE_DIR = _path_from_env("KNOWLEDGE_BASE_DIR", "knowledge_base/documents")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Policy Bot Specific Settings
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
BOT_NAME = "PolicyBot"
# Upper bound on generated tokens (thinking models count reasoning tokens here too)
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", os.getenv("MAX_ANSWER_LENGTH", "4096")))
