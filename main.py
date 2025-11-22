<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi


@asynccontextmanager
async def lifespan(app: FastAPI):
<<<<<<< HEAD
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
=======
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting NEXUS platform...")
    await cache.connect()
    logger.info("NEXUS platform started successfully")
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi

    yield

    # Shutdown
<<<<<<< HEAD
    logger.info("Shutting down NEXUS Platform...")
    if ws_server:
        await ws_server.shutdown()
    logger.info("NEXUS Platform shut down")
=======
    logger.info("Shutting down NEXUS platform...")
    await cache.disconnect()
    logger.info("NEXUS platform shutdown complete")
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi


# Create FastAPI app
app = FastAPI(
<<<<<<< HEAD
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
=======
    title="NEXUS Platform API",
    description="Unified AI-powered productivity platform with lead generation and advertising modules",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD

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
=======
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
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi


@app.get("/")
async def root():
<<<<<<< HEAD
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
=======
    """Root endpoint."""
    return {
        "name": "NEXUS Platform API",
        "version": "1.0.0",
        "modules": ["Lead Generation", "Advertising"]
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    }


@app.get("/health")
<<<<<<< HEAD
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
=======
async def health():
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    """Health check endpoint."""
    return {"status": "healthy"}


<<<<<<< HEAD
# Include routers
app.include_router(contracts_router)
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9


if __name__ == "__main__":
    import uvicorn

=======
"""Main application entry point."""

import uvicorn
from api.main import app

if __name__ == "__main__":
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
=======
if __name__ == "__main__":
    import uvicorn

>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
"""
Main entry point for NEXUS Content Calendar.

Run this script to start all services.
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_api():
    """Start FastAPI server."""
    print("Starting FastAPI server...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])


def run_streamlit():
    """Start Streamlit UI."""
    print("Starting Streamlit UI...")
    subprocess.run([
        sys.executable, "-m", "streamlit",
        "run",
        "modules/content_calendar/streamlit_ui.py",
        "--server.port", "8501"
    ])


def run_celery_worker():
    """Start Celery worker."""
    print("Starting Celery worker...")
    subprocess.run([
        "celery", "-A", "celery_app",
        "worker",
        "--loglevel=info"
    ])


def run_celery_beat():
    """Start Celery beat scheduler."""
    print("Starting Celery beat...")
    subprocess.run([
        "celery", "-A", "celery_app",
        "beat",
        "--loglevel=info"
    ])


def init_database():
    """Initialize database."""
    print("Initializing database...")
    from database import init_db
    init_db()
    print("Database initialized successfully!")


def run_tests():
    """Run test suite."""
    print("Running tests...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=modules",
        "--cov-report=html"
    ])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NEXUS Content Calendar - Management Tool"
    )

    parser.add_argument(
        "command",
        choices=[
            "api",
            "streamlit",
            "celery-worker",
            "celery-beat",
            "init-db",
            "test",
            "all"
        ],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "streamlit":
        run_streamlit()
    elif args.command == "celery-worker":
        run_celery_worker()
    elif args.command == "celery-beat":
        run_celery_beat()
    elif args.command == "init-db":
        init_database()
    elif args.command == "test":
        run_tests()
    elif args.command == "all":
        print("Starting all services...")
        print("Note: Use docker-compose for production deployment")
        print("Run each service in a separate terminal:")
        print("  python main.py api")
        print("  python main.py streamlit")
        print("  python main.py celery-worker")
        print("  python main.py celery-beat")
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq


if __name__ == "__main__":
    main()
<<<<<<< HEAD
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
>>>>>>> origin/claude/contracts-management-module-01FmzTmE3DeZrdwEsMYTdLB9
=======
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq
=======
"""
Streamlit UI for NEXUS Marketing Automation Platform.

This is the main entry point for the Streamlit user interface.
"""
import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="NEXUS Marketing Automation",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1/marketing"

# Sidebar navigation
st.sidebar.title("NEXUS Marketing Automation")
page = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard", "Campaigns", "Contacts", "Automations", "Analytics"]
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


def show_dashboard():
    """Display dashboard page."""
    st.markdown('<h1 class="main-header">Marketing Dashboard</h1>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Campaigns", "24", "+3")

    with col2:
        st.metric("Active Contacts", "1,234", "+56")

    with col3:
        st.metric("Open Rate", "28.5%", "+2.1%")

    with col4:
        st.metric("Click Rate", "12.3%", "+1.5%")

    st.markdown("---")

    # Recent campaigns
    st.subheader("📧 Recent Campaigns")

    campaigns_data = {
        "Campaign": ["Summer Sale 2024", "Product Launch", "Newsletter #42"],
        "Status": ["Completed", "Running", "Scheduled"],
        "Recipients": [1234, 856, 2100],
        "Open Rate": ["32.5%", "28.1%", "-"],
        "Created": ["2024-01-15", "2024-01-20", "2024-01-22"],
    }

    st.dataframe(campaigns_data, use_container_width=True)


def show_campaigns():
    """Display campaigns page."""
    st.markdown('<h1 class="main-header">📧 Email Campaigns</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["All Campaigns", "Create Campaign"])

    with tab1:
        st.subheader("Campaign List")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "Draft", "Running", "Completed"])
        with col2:
            sort_by = st.selectbox("Sort by", ["Created Date", "Name", "Status"])
        with col3:
            st.write("")  # Spacer

        # Mock campaigns list
        st.info("Connect to API to load campaigns")

    with tab2:
        st.subheader("Create New Campaign")

        with st.form("create_campaign_form"):
            campaign_name = st.text_input("Campaign Name*", placeholder="Summer Sale 2024")
            campaign_desc = st.text_area("Description", placeholder="Campaign description...")

            col1, col2 = st.columns(2)

            with col1:
                campaign_type = st.selectbox("Type", ["Email", "SMS", "Multi-Channel"])
                from_name = st.text_input("From Name", value="NEXUS Team")

            with col2:
                segment = st.selectbox("Target Segment", ["All Subscribers", "Engaged Users", "VIP Customers"])
                from_email = st.text_input("From Email", value="noreply@nexus.com")

            subject_line = st.text_input("Subject Line*", placeholder="Don't miss our summer sale!")

            # AI Content Generation
            st.subheader("✨ AI-Powered Content Generation")

            col1, col2 = st.columns(2)
            with col1:
                campaign_goal = st.text_input("Campaign Goal", placeholder="Drive summer sales")
            with col2:
                tone = st.selectbox("Tone", ["Professional", "Casual", "Friendly", "Urgent"])

            if st.button("🤖 Generate Content with AI"):
                with st.spinner("Generating AI content..."):
                    st.success("AI content generated! Review below.")

            email_content = st.text_area(
                "Email Content (HTML)*",
                height=300,
                placeholder="<h1>Hello {{first_name}}</h1>\n<p>Your content here...</p>"
            )

            scheduled_send = st.checkbox("Schedule for later")
            if scheduled_send:
                schedule_date = st.date_input("Schedule Date")
                schedule_time = st.time_input("Schedule Time")

            submitted = st.form_submit_button("Create Campaign", type="primary")

            if submitted:
                if campaign_name and email_content:
                    st.success(f"Campaign '{campaign_name}' created successfully!")
                else:
                    st.error("Please fill in all required fields")


def show_contacts():
    """Display contacts page."""
    st.markdown('<h1 class="main-header">👥 Contact Management</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Contacts", "Segments", "Import"])

    with tab1:
        st.subheader("Contact List")

        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search contacts", placeholder="Search by email, name...")
        with col2:
            status_filter = st.selectbox("Status", ["All", "Subscribed", "Unsubscribed"])
        with col3:
            score_filter = st.selectbox("Lead Score", ["All", "Cold", "Warm", "Hot"])

        st.info("Connect to API to load contacts")

    with tab2:
        st.subheader("Audience Segments")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Dynamic audience segmentation for targeted campaigns")
        with col2:
            if st.button("Create Segment", type="primary"):
                st.info("Segment creation form would appear here")

        # Mock segments
        segments = {
            "Segment Name": ["Engaged Users", "VIP Customers", "Inactive Users"],
            "Contact Count": [456, 89, 234],
            "Created": ["2024-01-10", "2024-01-15", "2024-01-18"],
        }
        st.dataframe(segments, use_container_width=True)

    with tab3:
        st.subheader("Import Contacts")

        uploaded_file = st.file_uploader("Upload CSV file", type=["csv", "xlsx"])

        if uploaded_file:
            st.success("File uploaded successfully!")
            st.info("Preview and map fields before importing")


def show_automations():
    """Display automations page."""
    st.markdown('<h1 class="main-header">⚙️ Marketing Automation</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Workflows", "Drip Campaigns"])

    with tab1:
        st.subheader("Automation Workflows")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Build powerful automation workflows with visual editor")
        with col2:
            if st.button("Create Workflow", type="primary"):
                st.info("Workflow builder would appear here")

        # Mock workflows
        workflows = {
            "Workflow": ["Welcome Series", "Abandoned Cart", "Re-engagement"],
            "Status": ["Active", "Active", "Paused"],
            "Trigger": ["Contact Subscribed", "Cart Abandoned", "30 Days Inactive"],
            "Executions": [234, 45, 12],
        }
        st.dataframe(workflows, use_container_width=True)

    with tab2:
        st.subheader("Drip Campaigns")

        st.write("Create multi-step nurture campaigns that guide leads through your funnel")

        if st.button("Create Drip Campaign", type="primary"):
            st.info("Drip campaign builder would appear here")


def show_analytics():
    """Display analytics page."""
    st.markdown('<h1 class="main-header">📊 Analytics & Reports</h1>', unsafe_allow_html=True)

    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("From")
    with col2:
        end_date = st.date_input("To")
    with col3:
        st.write("")  # Spacer

    st.markdown("---")

    # Key metrics
    st.subheader("📈 Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sent", "12,345", "+1,234")
    with col2:
        st.metric("Open Rate", "28.5%", "+2.1%")
    with col3:
        st.metric("Click Rate", "12.3%", "+1.5%")
    with col4:
        st.metric("Conversions", "456", "+23")

    st.markdown("---")

    # Charts
    st.subheader("Campaign Performance Over Time")
    st.line_chart({"Opens": [100, 120, 140, 160, 180], "Clicks": [30, 35, 42, 48, 54]})

    st.subheader("Top Performing Campaigns")
    st.bar_chart({"Campaign A": 85, "Campaign B": 72, "Campaign C": 68})


# Page routing
if page == "Dashboard":
    show_dashboard()
elif page == "Campaigns":
    show_campaigns()
elif page == "Contacts":
    show_contacts()
elif page == "Automations":
    show_automations()
elif page == "Analytics":
    show_analytics()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**NEXUS Marketing Automation**
Version 0.1.0
AI-powered marketing platform
""")
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
=======
        reload=True,
        log_level="info",
    )
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
=======
        reload=settings.environment == "development"
    )
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
