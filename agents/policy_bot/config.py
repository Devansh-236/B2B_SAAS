"""
Configuration settings for the Policy Bot agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM API Configuration
LLM_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")

# Vector Database Configuration
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./knowledge_base/vector_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Document Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_CHUNKS_RETRIEVED = int(os.getenv("MAX_CHUNKS_RETRIEVED", "5"))

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_TITLE = "Policy Bot API"
API_DESCRIPTION = "HR Policy Bot for answering employee questions"

# File Paths
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "./knowledge_base/documents")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./knowledge_base/output")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/policy_bot.log")

# Policy Bot Specific Settings
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
BOT_NAME = "PolicyBot"
MAX_ANSWER_LENGTH = int(os.getenv("MAX_ANSWER_LENGTH", "2000"))

# Create directories if they don't exist
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
