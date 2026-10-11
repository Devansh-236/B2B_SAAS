"""
FastAPI server for the Policy Bot.

This module provides REST API endpoints for interacting with the Policy Bot.
"""

import os
import sys
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from policy_agent import get_policy_bot
from config import (
    API_TITLE, API_DESCRIPTION, API_HOST, API_PORT, API_KEY, CORS_ORIGINS,
    MAX_QUESTION_LENGTH, LOG_LEVEL
)

# Set up logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Policy Bot API server...")
    yield
    logger.info("Shutting down Policy Bot API server...")


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


def require_api_key(x_api_key: Optional[str] = Header(None)):
    """Enforce the shared API key when POLICY_BOT_API_KEY is configured."""
    if API_KEY and not (x_api_key and secrets.compare_digest(x_api_key, API_KEY)):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# Pydantic models for request/response
class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(
        ..., description="The policy question to ask", min_length=1, max_length=MAX_QUESTION_LENGTH
    )
    user_id: Optional[str] = Field(None, description="Optional user identifier", max_length=128)


class QuestionResponse(BaseModel):
    """Response model for question answers."""
    answer: str
    status: str
    timestamp: str
    user_id: Optional[str] = None
    question: Optional[str] = None
    sources: Optional[list] = None
    num_sources: Optional[int] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    knowledge_base: Dict[str, Any]
    llm_available: bool
    vectorstore_available: bool
    timestamp: str
    error: Optional[str] = None


class StatsResponse(BaseModel):
    """Response model for knowledge base statistics."""
    total_documents: int
    status: str


# API Endpoints
# Handlers that touch the bot are plain `def` so FastAPI runs them in a threadpool;
# embedding and LLM calls are blocking and would otherwise stall the event loop.

@app.get("/", response_model=Dict[str, str])
def root():
    """Root endpoint with basic information."""
    return {
        "message": "Policy Bot API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/ask", response_model=QuestionResponse, dependencies=[Depends(require_api_key)])
def ask_question(request: QuestionRequest):
    """Ask a policy question to the bot."""
    try:
        response = get_policy_bot().ask_question(
            question=request.question.strip(),
            user_id=request.user_id
        )
        return QuestionResponse(**response)

    except Exception:
        logger.exception("Error processing question")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Report whether the knowledge base and LLM client are ready."""
    try:
        return HealthResponse(**get_policy_bot().health_check())

    except Exception:
        logger.exception("Error during health check")
        return HealthResponse(
            status="unhealthy",
            knowledge_base={"total_documents": 0, "status": "error"},
            llm_available=False,
            vectorstore_available=False,
            timestamp=datetime.now().isoformat(),
            error="Policy Bot failed to initialize; check the server logs"
        )


@app.get("/stats", response_model=StatsResponse, dependencies=[Depends(require_api_key)])
def get_stats():
    """Get knowledge base statistics."""
    try:
        return StatsResponse(**get_policy_bot().get_knowledge_base_stats())

    except Exception:
        logger.exception("Error getting stats")
        raise HTTPException(status_code=500, detail="Error getting statistics")


@app.get("/docs/info", dependencies=[Depends(require_api_key)])
def get_docs_info():
    """Get information about the documents in the knowledge base."""
    try:
        stats = get_policy_bot().get_knowledge_base_stats()
        return {
            "total_documents": stats.get("total_documents", 0),
            "status": stats.get("status", "unknown")
        }

    except Exception:
        logger.exception("Error getting docs info")
        raise HTTPException(status_code=500, detail="Error getting document information")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"API will be available at: http://{API_HOST}:{API_PORT} (docs at /docs)")
    uvicorn.run(
        "api_server:app",
        host=API_HOST,
        port=API_PORT,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=LOG_LEVEL.lower()
    )
