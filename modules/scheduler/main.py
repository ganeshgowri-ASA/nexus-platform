"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from modules.scheduler.api import api_router
from modules.scheduler.services.scheduler_engine import SchedulerEngine
from modules.scheduler.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting NEXUS Scheduler...")

    # Initialize and start scheduler engine
    if settings.ENABLE_SCHEDULER:
        scheduler = SchedulerEngine()
        scheduler.start()
        print("✅ Scheduler engine started")

    yield

    # Shutdown
    print("Shutting down NEXUS Scheduler...")
    if settings.ENABLE_SCHEDULER:
        scheduler = SchedulerEngine()
        scheduler.shutdown()
        print("✅ Scheduler engine stopped")


# Create FastAPI app
app = FastAPI(
    title="NEXUS Scheduler API",
    description="Advanced task scheduling with cron, calendar-based scheduling, and timezone support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "NEXUS Scheduler API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "scheduler_enabled": settings.ENABLE_SCHEDULER
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
