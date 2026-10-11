"""
Simple web interface for the Policy Bot.

This module provides a basic HTML interface for interacting with the Policy Bot.
"""

import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_server import app as api_app
from config import API_HOST, WEB_PORT, LOG_LEVEL

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Create a new FastAPI app for the web interface
web_app = FastAPI(title="Policy Bot Web Interface")

# Mount the API app
web_app.mount("/api", api_app)

# Set up templates
templates = Jinja2Templates(directory=templates_dir)


@web_app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse(request, "index.html")


if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Starting Policy Bot Web Interface...")
    print(f"Web interface will be available at: http://{API_HOST}:{WEB_PORT}")
    print(f"API endpoints available at: http://{API_HOST}:{WEB_PORT}/api")

    uvicorn.run(
        "web_interface:web_app",
        host=API_HOST,
        port=WEB_PORT,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=LOG_LEVEL.lower()
    )
