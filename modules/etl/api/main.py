"""Main FastAPI application for ETL module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from modules.etl.api.routes import sources, pipelines, transformations, jobs, executions
from shared.utils.logger import setup_logger

# Setup logging
setup_logger()

# Create FastAPI app
app = FastAPI(
    title="NEXUS ETL API",
    description="ETL (Extract, Transform, Load) module for NEXUS platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Data Sources"])
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
app.include_router(transformations.router, prefix="/api/v1/transformations", tags=["Transformations"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(executions.router, prefix="/api/v1/executions", tags=["Executions"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NEXUS ETL API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
