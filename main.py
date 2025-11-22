"""
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
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS Platform API",
        "version": "1.0.0",
        "websocket_endpoint": "/ws",
        "status": "online"
    }


@app.get("/health")
async def health_check():
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
