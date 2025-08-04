"""
FastAPI application entry-point.  Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables FIRST before importing modules that depend on them
# Find the backend .env file (same approach as in conftest.py)
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
load_dotenv(env_file)

from app.conversations import router as conversations_router  # noqa: E402

# Import modules that depend on environment variables after loading them
from app.sse import router as sse_router  # noqa: E402

# --------------------------------------------------------------------------- #
# Environment & Logging
# --------------------------------------------------------------------------- #


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger = logging.getLogger(__name__)
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)


# Set up logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Validate environment before starting
validate_environment()

# --------------------------------------------------------------------------- #
# FastAPI INIT
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="Hierarchical Expertise Router – Backend",
    description="AI-powered multi-expert analysis platform with real-time streaming",
    version="0.1.0",
    docs_url=None,  # Disable auto-generated docs
    redoc_url=None,  # Disable redoc docs
)

# Enhanced CORS for better frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        # "Authorization",  # No auth implemented yet
        "Cache-Control",
        "Last-Event-ID",  # Important for SSE resumption
    ],
    expose_headers=["X-Total-Count"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "agentic-ai-backend", "version": "0.1.0"}


# Root endpoint with basic info
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {"message": "Hierarchical Expertise Router API", "version": "0.1.0", "health": "/health"}


app.include_router(sse_router)
app.include_router(conversations_router)


# Global exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled error on {request.method} {request.url}: {str(exc)}")
    return HTTPException(
        status_code=500,
        detail={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "type": exc.__class__.__name__,
        },
    )
