"""Main FastAPI application for Integration Hub module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.utils.logger import setup_logger

# Setup logging
setup_logger()

# Create FastAPI app
app = FastAPI(
    title="NEXUS Integration Hub API",
    description="Integration Hub for managing third-party integrations, OAuth, webhooks, and data sync",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NEXUS Integration Hub API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "OAuth 2.0 flows",
            "API key management",
            "Webhook handling",
            "Data synchronization",
            "Rate limiting",
            "Integration marketplace",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
