"""Main FastAPI application for NEXUS Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import setup_logging
from database.connection import engine
from database.models import Base
from modules.batch_processing.routes import router as batch_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="NEXUS Platform - 24 Integrated Modules for Complete Productivity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("🚀 NEXUS Platform started successfully!")
    print(f"📊 API Documentation: http://localhost:8000/docs")
    print(f"🎨 Streamlit UI: http://localhost:8501")
    print(f"🌺 Flower (Celery): http://localhost:5555")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 NEXUS Platform shutting down...")


# Health check
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0"
    }


# Include routers
app.include_router(batch_router, prefix="", tags=["Batch Processing"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
