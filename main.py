<<<<<<< HEAD
"""
<<<<<<< HEAD
NEXUS Platform - Main Application

Example FastAPI application with WebSocket server integration.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from websocket import WebSocketServer
from websocket.events import NotificationEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global WebSocket server instance
ws_server: Optional[WebSocketServer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ws_server

    logger.info("Starting NEXUS Platform...")

    # Initialize WebSocket server
    ws_server = WebSocketServer(
        heartbeat_interval=30,
        heartbeat_timeout=60,
        enable_auto_ping=True
    )

    # Start background tasks
    await ws_server.start_background_tasks()

    logger.info("NEXUS Platform started successfully")

    yield

    # Shutdown
    logger.info("Shutting down NEXUS Platform...")
    if ws_server:
        await ws_server.shutdown()
    logger.info("NEXUS Platform shut down")


# Create FastAPI app
app = FastAPI(
    title="NEXUS Platform",
    description="Real-time collaboration platform with WebSocket support",
    version="1.0.0",
    lifespan=lifespan
=======
"""Main application entry point.

This module sets up and runs the NEXUS platform FastAPI application
with all modules integrated.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from config import settings
from shared.database import init_db
from modules.contracts.api import router as contracts_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NEXUS: Unified AI-powered productivity platform with integrated modules",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


<<<<<<< HEAD
# Dependency for authentication (example - implement your own)
async def get_current_user(token: Optional[str] = Query(None)):
    """
    Authentication dependency
    Replace with your actual authentication logic
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Example: decode JWT token and get user info
    # For demo purposes, we'll use a simple format
    try:
        # This is just a placeholder - implement real authentication
        user_id = token  # In real app, extract from JWT
        return {"user_id": user_id, "username": f"user_{user_id}"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
=======
@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting NEXUS platform", version=settings.APP_VERSION)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down NEXUS platform")
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9


@app.get("/")
async def root():
<<<<<<< HEAD
    """Root endpoint"""
    return {
        "message": "NEXUS Platform API",
        "version": "1.0.0",
        "websocket_endpoint": "/ws",
        "status": "online"
=======
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
    }


@app.get("/health")
async def health_check():
<<<<<<< HEAD
    """Health check endpoint"""
    return {
        "status": "healthy",
        "websocket_server": "active" if ws_server else "inactive"
    }


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID"),
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    Main WebSocket endpoint for real-time communication

    Query Parameters:
    - user_id: Authenticated user ID
    - token: Optional authentication token

    Example connection:
    ws://localhost:8000/ws?user_id=user123&token=your_token_here
    """
    if ws_server:
        await ws_server.handle_websocket(websocket, user_id, token)


# REST API endpoints for WebSocket management

@app.get("/api/ws/stats")
async def get_websocket_stats():
    """Get WebSocket server statistics"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    return ws_server.connection_manager.get_stats()


@app.get("/api/ws/online")
async def get_online_users():
    """Get list of currently online users"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    return {
        "online_users": ws_server.connection_manager.get_online_users(),
        "count": len(ws_server.connection_manager.get_online_users())
    }


@app.get("/api/ws/rooms/{room_id}")
async def get_room_members(room_id: str):
    """Get members of a specific room"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    members = ws_server.connection_manager.get_room_members(room_id)
    return {
        "room_id": room_id,
        "members": members,
        "count": len(members)
    }


@app.get("/api/presence/{user_id}")
async def get_user_presence(user_id: str):
    """Get presence information for a specific user"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    presence = ws_server.presence_handler.get_user_presence(user_id)
    if not presence:
        raise HTTPException(status_code=404, detail="User presence not found")

    return presence


@app.get("/api/presence/status/{status}")
async def get_users_by_status(status: str):
    """Get users with specific status (online, offline, away, busy)"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    if status not in ["online", "offline", "away", "busy"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    users = ws_server.presence_handler.get_users_by_status(status)
    return {
        "status": status,
        "users": users,
        "count": len(users)
    }


@app.post("/api/notifications/send")
async def send_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    priority: str = "normal",
    current_user: dict = Depends(get_current_user)
):
    """
    Send a notification to a specific user

    Requires authentication.
    """
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    notification = NotificationEvent(
        notification_id=f"notif_{user_id}_{int(asyncio.get_event_loop().time())}",
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority
    )

    await ws_server.send_notification(user_id, notification)

    return {
        "status": "sent",
        "notification_id": notification.notification_id,
        "user_id": user_id
    }


@app.post("/api/notifications/broadcast")
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    priority: str = "normal",
    current_user: dict = Depends(get_current_user)
):
    """
    Broadcast a notification to all online users

    Requires authentication.
    """
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    online_users = ws_server.connection_manager.get_online_users()

    notification_template = {
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "priority": priority
    }

    await ws_server.notification_handler.send_bulk_notifications(
        online_users,
        notification_template
    )

    return {
        "status": "broadcast",
        "recipients": len(online_users),
        "users": online_users
    }


@app.get("/api/documents/active")
async def get_active_documents():
    """Get list of documents with active editing sessions"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    documents = ws_server.document_handler.get_active_documents()

    return {
        "active_documents": documents,
        "count": len(documents)
    }


@app.get("/api/documents/{document_id}/session")
async def get_document_session(document_id: str):
    """Get active editing session info for a document"""
    if not ws_server:
        raise HTTPException(status_code=503, detail="WebSocket server not available")

    session = ws_server.document_handler.get_document_session(document_id)

    if not session:
        raise HTTPException(status_code=404, detail="No active session for this document")

    return {
        "document_id": document_id,
        "version": session.version,
        "active_users": list(session.active_users),
        "created_at": session.created_at.isoformat(),
        "user_count": len(session.active_users)
    }
=======
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(contracts_router)
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
<<<<<<< HEAD
        reload=True,
        log_level="info"
    )
=======
NEXUS Platform - Main Streamlit Application Entry Point
"""

import streamlit as st
from config.settings import settings
from config.database import init_db
from core.utils import setup_logging, get_logger
from modules import get_available_modules

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main application entry point."""

    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Configure Streamlit page
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .module-card {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("# 🚀 NEXUS Platform")
        st.markdown("---")

        # Get available modules
        available_modules = get_available_modules()

        # Module selection
        st.markdown("### 📦 Modules")

        module_names = list(available_modules.keys())
        module_display_names = {
            "pipeline": "⚙️ Pipeline Builder"
        }

        selected_module = st.radio(
            "Select Module",
            module_names,
            format_func=lambda x: module_display_names.get(x, x)
        )

        st.markdown("---")

        # System info
        st.markdown("### ℹ️ System Info")
        st.markdown(f"**Environment:** {settings.ENVIRONMENT}")
        st.markdown(f"**Debug Mode:** {'On' if settings.DEBUG else 'Off'}")

        # Footer
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Build:** Pipeline Module")

    # Main content area
    if selected_module:
        # Get module class
        module_class = available_modules.get(selected_module)

        if module_class:
            try:
                # Instantiate and render module
                module_instance = module_class()
                module_instance.render_ui()

            except Exception as e:
                logger.error(f"Error rendering module {selected_module}: {e}")
                st.error(f"Error loading module: {e}")

                # Show error details in debug mode
                if settings.DEBUG:
                    import traceback
                    st.code(traceback.format_exc())

        else:
            st.error(f"Module '{selected_module}' not found")

    else:
        # Welcome screen
        st.markdown('<h1 class="main-header">Welcome to NEXUS</h1>', unsafe_allow_html=True)

        st.markdown("""
        ### 🎯 AI-Powered Productivity Platform

        NEXUS is a unified platform that combines multiple productivity tools with AI capabilities.

        #### 🚀 Getting Started

        Select a module from the sidebar to begin:

        - **⚙️ Pipeline Builder**: Create and manage data pipelines with visual workflow builder
        """)

        # Feature highlights
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            #### 📊 Visual Pipeline Builder
            - Drag-and-drop interface
            - 10+ source connectors
            - Advanced transformations
            - Real-time monitoring
            """)

        with col2:
            st.markdown("""
            #### 🔄 ETL & Stream Processing
            - Batch & real-time processing
            - Data validation
            - Error handling
            - Backfill support
            """)

        with col3:
            st.markdown("""
            #### 📈 Monitoring & Scheduling
            - Cron-based scheduling
            - Apache Airflow integration
            - Execution metrics
            - Alert notifications
            """)

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Platform Status")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Modules", len(available_modules))

        with col2:
            st.metric("Status", "🟢 Running")

        with col3:
            st.metric("Environment", settings.ENVIRONMENT.upper())

        with col4:
            st.metric("Version", "1.0.0")


if __name__ == "__main__":
    main()
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
