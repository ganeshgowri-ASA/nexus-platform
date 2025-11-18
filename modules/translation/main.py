"""
Main FastAPI application for NEXUS Translation Module
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import router
from .models.database import init_db
from .config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Starting NEXUS Translation Module...")
    print(f"Database URL: {config.database_url}")

    # Initialize database
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

    yield

    # Shutdown
    print("Shutting down NEXUS Translation Module...")


# Create FastAPI app
app = FastAPI(
    title="NEXUS Translation Module",
    description="Comprehensive translation service with 100+ languages support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS Translation Module API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/translation/health",
            "translate": "/api/translation/translate"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "translation",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "modules.translation.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.api_reload
    )
