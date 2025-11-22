from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from modules.api_gateway.config import settings
from modules.api_gateway.database import init_db, redis_client
from modules.api_gateway.middleware import AuthMiddleware, RateLimitMiddleware, MetricsMiddleware
from modules.api_gateway.routes import routes_router, api_keys_router, metrics_router, auth_router
from modules.api_gateway.app.gateway import GatewayRouter

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Add custom middleware (order matters!)
app.add_middleware(MetricsMiddleware)  # Metrics collection (outermost)
app.add_middleware(RateLimitMiddleware)  # Rate limiting
app.add_middleware(AuthMiddleware)  # Authentication

# Include API routers
app.include_router(auth_router)
app.include_router(routes_router)
app.include_router(api_keys_router)
app.include_router(metrics_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

    # Connect to Redis
    redis_client.connect()

    print(f"Server ready on {settings.HOST}:{settings.PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down...")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "redis_connected": redis_client.is_connected(),
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "admin_ui": "/admin" if settings.ADMIN_UI_ENABLED else None,
    }


# Gateway router (handles proxying to backend services)
gateway_router = GatewayRouter()
app.include_router(gateway_router.router)


def start():
    """Start the server"""
    uvicorn.run(
        "modules.api_gateway.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    start()
