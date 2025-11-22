"""Main FastAPI application for webhooks module"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from modules.webhooks.api.webhooks import router as webhooks_router
from modules.webhooks.api.events import router as events_router
from modules.webhooks.api.deliveries import router as deliveries_router
from modules.webhooks.models.base import init_db

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="NEXUS Webhooks API",
    description="Webhook management, event subscriptions, and delivery system",
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

# Include routers
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(deliveries_router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "NEXUS Webhooks API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
