"""
Main FastAPI application for NEXUS platform.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from cache import cache
from config import get_settings
from modules.lead_generation.routers import (
    forms, leads, landing_pages, chatbot
)
from modules.advertising.routers import (
    campaigns, ads, creatives, performance
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting NEXUS platform...")
    await cache.connect()
    logger.info("NEXUS platform started successfully")

    yield

    # Shutdown
    logger.info("Shutting down NEXUS platform...")
    await cache.disconnect()
    logger.info("NEXUS platform shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="NEXUS Platform API",
    description="Unified AI-powered productivity platform with lead generation and advertising modules",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Lead Generation
app.include_router(
    forms.router,
    prefix="/api/lead-generation/forms",
    tags=["Lead Generation - Forms"]
)
app.include_router(
    landing_pages.router,
    prefix="/api/lead-generation/landing-pages",
    tags=["Lead Generation - Landing Pages"]
)
app.include_router(
    leads.router,
    prefix="/api/lead-generation/leads",
    tags=["Lead Generation - Leads"]
)
app.include_router(
    chatbot.router,
    prefix="/api/lead-generation/chatbot",
    tags=["Lead Generation - Chatbot"]
)

# Include routers - Advertising
app.include_router(
    campaigns.router,
    prefix="/api/advertising/campaigns",
    tags=["Advertising - Campaigns"]
)
app.include_router(
    ads.router,
    prefix="/api/advertising/ads",
    tags=["Advertising - Ads"]
)
app.include_router(
    creatives.router,
    prefix="/api/advertising/creatives",
    tags=["Advertising - Creatives"]
)
app.include_router(
    performance.router,
    prefix="/api/advertising/performance",
    tags=["Advertising - Performance"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NEXUS Platform API",
        "version": "1.0.0",
        "modules": ["Lead Generation", "Advertising"]
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
