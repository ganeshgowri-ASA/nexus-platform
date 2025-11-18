"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from config.database import init_db
from config.logging_config import get_logger
from .lead_routes import router as lead_router
from .ad_routes import router as ad_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting NEXUS Platform API")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down NEXUS Platform API")


app = FastAPI(
    title="NEXUS Platform API",
    description="Unified AI-powered productivity platform with Lead Generation and Advertising modules",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(lead_router, prefix="/api/leads", tags=["Lead Generation"])
app.include_router(ad_router, prefix="/api/advertising", tags=["Advertising"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to NEXUS Platform API",
        "version": "1.0.0",
        "modules": ["lead_generation", "advertising"],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-11-18"}
