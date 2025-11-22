"""
NEXUS Platform - Backend API
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.database import init_db
from backend.routers import notifications

# Create FastAPI app
app = FastAPI(
    title="NEXUS Platform API",
    description="Multi-channel notification system with email, SMS, push, and in-app notifications",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notifications.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✓ Database initialized")
    print("✓ NEXUS Platform API started")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS Platform API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Multi-channel notifications (email, SMS, push, in-app)",
            "Notification templates",
            "Scheduling",
            "Delivery tracking",
            "User preferences",
            "Unsubscribe management",
            "Firebase Cloud Messaging ready"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
