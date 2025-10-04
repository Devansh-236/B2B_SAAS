"""
FastAPI server for the Policy Bot.

This module provides REST API endpoints for interacting with the Policy Bot.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from policy_agent import policy_bot
from config import API_TITLE, API_DESCRIPTION, API_HOST, API_PORT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., description="The policy question to ask", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user identifier")


class QuestionResponse(BaseModel):
    """Response model for question answers."""
    answer: str
    status: str
    timestamp: str
    user_id: Optional[str] = None
    question: Optional[str] = None
    sources: Optional[list] = None
    num_sources: Optional[int] = None
    error: Optional[str] = None


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
    vector_db_path: Optional[str] = None
    error: Optional[str] = None


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Policy Bot API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a policy question to the bot.
    
    Args:
        request: QuestionRequest containing the question and optional user_id
        
    Returns:
        QuestionResponse with the answer and metadata
    """
    try:
        logger.info(f"Received question from user {request.user_id}: {request.question}")
        
        # Get answer from policy bot
        response = policy_bot.ask_question(
            question=request.question,
            user_id=request.user_id
        )
        
        return QuestionResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Perform a health check on the Policy Bot.
    
    Returns:
        HealthResponse with system status
    """
    try:
        health_info = policy_bot.health_check()
        return HealthResponse(**health_info)
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return HealthResponse(
            status="unhealthy",
            knowledge_base={"total_documents": 0, "status": "error"},
            llm_available=False,
            vectorstore_available=False,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get knowledge base statistics.
    
    Returns:
        StatsResponse with knowledge base information
    """
    try:
        stats = policy_bot.get_knowledge_base_stats()
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )


@app.get("/docs/info")
async def get_docs_info():
    """
    Get information about the documents in the knowledge base.
    
    Returns:
        Dictionary with document information
    """
    try:
        # This would require access to the document processor
        # For now, return basic info
        stats = policy_bot.get_knowledge_base_stats()
        return {
            "total_documents": stats.get("total_documents", 0),
            "status": stats.get("status", "unknown"),
            "vector_db_path": stats.get("vector_db_path", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting docs info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document information: {str(e)}"
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {"error": "Endpoint not found", "status": 404}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "status": 500}


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Policy Bot API server...")
    logger.info(f"API will be available at: http://{API_HOST}:{API_PORT}")
    logger.info(f"API documentation at: http://{API_HOST}:{API_PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down Policy Bot API server...")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Policy Bot API server...")
    uvicorn.run(
        "api_server:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
