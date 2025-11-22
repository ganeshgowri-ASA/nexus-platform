"""
FastAPI application for NEXUS Content Calendar.

Provides RESTful API endpoints and WebSocket support for:
- Content management
- Calendar operations
- Workflow management
- Analytics
- Real-time collaboration
"""
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from loguru import logger

from config import settings
from database import get_db, init_db
from modules.content_calendar import (
    ContentPlanner,
    ContentManager,
    ContentScheduler,
    WorkflowManager,
    CollaborationManager,
    AnalyticsManager,
    IntegrationManager,
)
from modules.content_calendar.calendar_types import (
    CalendarEvent,
    ContentPlan,
    ScheduleConfig,
    RecurringPattern,
    Comment,
    Workflow,
)

# Initialize FastAPI app
app = FastAPI(
    title="NEXUS Content Calendar API",
    description="API for content calendar management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections manager
class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a new websocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a websocket."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")


manager = ConnectionManager()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    logger.info("Starting NEXUS Content Calendar API")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down NEXUS Content Calendar API")


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Calendar endpoints
@app.get("/api/calendar/events")
async def get_calendar_events(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    channels: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[CalendarEvent]:
    """Get calendar events for date range."""
    try:
        planner = ContentPlanner(db)
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        channel_list = channels.split(",") if channels else None
        status_list = status.split(",") if status else None

        events = planner.get_calendar_view(
            start_date=start,
            end_date=end,
            user_id=user_id,
            channels=channel_list,
            status=status_list,
        )

        return events

    except Exception as e:
        logger.error(f"Error getting calendar events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calendar/events")
async def create_event(
    event: CalendarEvent,
    user_id: int,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Create new calendar event."""
    try:
        planner = ContentPlanner(db)
        created_event = planner.create_event(event, user_id)

        # Broadcast event creation
        await manager.broadcast(
            {
                "type": "event_created",
                "event_id": created_event.id,
                "title": created_event.title,
            }
        )

        return created_event

    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/calendar/events/{event_id}")
async def update_event(
    event_id: int,
    event_data: dict,
    user_id: int,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Update calendar event."""
    try:
        planner = ContentPlanner(db)
        updated_event = planner.update_event(event_id, event_data, user_id)

        await manager.broadcast(
            {
                "type": "event_updated",
                "event_id": event_id,
            }
        )

        return updated_event

    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/calendar/events/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete calendar event."""
    try:
        planner = ContentPlanner(db)
        success = planner.delete_event(event_id)

        await manager.broadcast(
            {
                "type": "event_deleted",
                "event_id": event_id,
            }
        )

        return {"success": success}

    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calendar/events/{event_id}/move")
async def move_event(
    event_id: int,
    new_datetime: str,
    timezone: Optional[str] = None,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Move event to new date/time (drag-and-drop)."""
    try:
        planner = ContentPlanner(db)
        new_dt = datetime.fromisoformat(new_datetime)
        moved_event = planner.move_event(event_id, new_dt, timezone)

        await manager.broadcast(
            {
                "type": "event_moved",
                "event_id": event_id,
                "new_datetime": new_datetime,
            }
        )

        return moved_event

    except Exception as e:
        logger.error(f"Error moving event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Content endpoints
@app.post("/api/content")
async def create_content(
    title: str,
    content: str,
    content_type: str,
    creator_id: int,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Create new content."""
    try:
        from modules.content_calendar.calendar_types import ContentFormat

        manager_obj = ContentManager(db)
        created_content = manager_obj.create_content(
            title=title,
            content=content,
            content_type=ContentFormat(content_type),
            creator_id=creator_id,
        )

        return created_content

    except Exception as e:
        logger.error(f"Error creating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content/{content_id}")
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Get content by ID."""
    try:
        manager_obj = ContentManager(db)
        content = manager_obj.get_content(content_id)

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        return content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content/search")
async def search_content(
    query: str,
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[CalendarEvent]:
    """Search content library."""
    try:
        from modules.content_calendar.calendar_types import ContentFormat

        manager_obj = ContentManager(db)
        tag_list = tags.split(",") if tags else None
        type_filter = ContentFormat(content_type) if content_type else None

        results = manager_obj.search_content(
            query=query,
            content_type=type_filter,
            tags=tag_list,
            limit=limit,
        )

        return results

    except Exception as e:
        logger.error(f"Error searching content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/content/generate-ideas")
async def generate_content_ideas(
    topic: str,
    content_type: str,
    target_audience: Optional[str] = None,
    tone: Optional[str] = None,
    count: int = 5,
    db: Session = Depends(get_db),
) -> List[dict]:
    """Generate AI-powered content ideas."""
    try:
        from modules.content_calendar.calendar_types import ContentFormat

        manager_obj = ContentManager(db)
        ideas = manager_obj.generate_content_ideas(
            topic=topic,
            content_type=ContentFormat(content_type),
            target_audience=target_audience,
            tone=tone,
            count=count,
        )

        return ideas

    except Exception as e:
        logger.error(f"Error generating content ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scheduling endpoints
@app.post("/api/scheduling/schedule")
async def schedule_content(
    content_id: int,
    schedule_config: ScheduleConfig,
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Schedule content for publication."""
    try:
        scheduler = ContentScheduler(db)
        scheduled = scheduler.schedule_content(content_id, schedule_config)

        return scheduled

    except Exception as e:
        logger.error(f"Error scheduling content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduling/auto-schedule")
async def auto_schedule_content(
    content_id: int,
    channel: str,
    timezone: str = "UTC",
    db: Session = Depends(get_db),
) -> CalendarEvent:
    """Auto-schedule content at optimal time."""
    try:
        scheduler = ContentScheduler(db)
        scheduled = scheduler.auto_schedule(
            content_id=content_id,
            channel=channel,
            timezone=timezone,
        )

        return scheduled

    except Exception as e:
        logger.error(f"Error auto-scheduling content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduling/optimal-times")
async def get_optimal_times(
    channel: str,
    days_ahead: int = 7,
    top_n: int = 5,
    db: Session = Depends(get_db),
) -> List[dict]:
    """Get optimal posting times for channel."""
    try:
        scheduler = ContentScheduler(db)
        optimal_times = scheduler.get_optimal_posting_times(
            channel=channel,
            days_ahead=days_ahead,
            top_n=top_n,
        )

        return [time.model_dump() for time in optimal_times]

    except Exception as e:
        logger.error(f"Error getting optimal times: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow endpoints
@app.post("/api/workflows")
async def create_workflow(
    content_id: int,
    workflow_name: str,
    steps: List[dict],
    description: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Workflow:
    """Create approval workflow."""
    try:
        workflow_mgr = WorkflowManager(db)
        workflow = workflow_mgr.create_workflow(
            content_id=content_id,
            workflow_name=workflow_name,
            steps=steps,
            description=description,
        )

        return workflow

    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{content_id}")
async def get_workflow(
    content_id: int,
    db: Session = Depends(get_db),
) -> Workflow:
    """Get workflow for content."""
    try:
        workflow_mgr = WorkflowManager(db)
        workflow = workflow_mgr.get_workflow(content_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Collaboration endpoints
@app.post("/api/collaboration/comments")
async def add_comment(
    content_id: int,
    author_id: int,
    text: str,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Comment:
    """Add comment to content."""
    try:
        collab_mgr = CollaborationManager(db)
        comment = collab_mgr.add_comment(
            content_id=content_id,
            author_id=author_id,
            text=text,
            parent_id=parent_id,
        )

        await manager.broadcast(
            {
                "type": "comment_added",
                "content_id": content_id,
                "comment_id": comment.id,
            }
        )

        return comment

    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collaboration/comments/{content_id}")
async def get_comments(
    content_id: int,
    include_resolved: bool = True,
    db: Session = Depends(get_db),
) -> List[Comment]:
    """Get comments for content."""
    try:
        collab_mgr = CollaborationManager(db)
        comments = collab_mgr.get_comments(
            content_id=content_id,
            include_resolved=include_resolved,
        )

        return comments

    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@app.get("/api/analytics/content/{content_id}")
async def get_content_performance(
    content_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Get performance report for content."""
    try:
        analytics_mgr = AnalyticsManager(db)

        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        report = analytics_mgr.get_content_performance(
            content_id=content_id,
            start_date=start,
            end_date=end,
        )

        return report.model_dump()

    except Exception as e:
        logger.error(f"Error getting content performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/top-content")
async def get_top_content(
    metric: str = "engagement_rate",
    limit: int = 10,
    days: int = 30,
    db: Session = Depends(get_db),
) -> List[dict]:
    """Get top performing content."""
    try:
        analytics_mgr = AnalyticsManager(db)
        top_content = analytics_mgr.get_top_performing_content(
            metric=metric,
            limit=limit,
            days=days,
        )

        return top_content

    except Exception as e:
        logger.error(f"Error getting top content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Integration endpoints
@app.post("/api/integrations/publish")
async def publish_content(
    content_id: int,
    channels: List[str],
    db: Session = Depends(get_db),
) -> dict:
    """Publish content to channels."""
    try:
        integration_mgr = IntegrationManager(db)
        results = integration_mgr.publish_content(
            content_id=content_id,
            channels=channels,
        )

        await manager.broadcast(
            {
                "type": "content_published",
                "content_id": content_id,
                "channels": channels,
            }
        )

        return results

    except Exception as e:
        logger.error(f"Error publishing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/integrations/sync-analytics/{content_id}")
async def sync_analytics(
    content_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Sync analytics from external platforms."""
    try:
        integration_mgr = IntegrationManager(db)
        results = integration_mgr.sync_analytics(content_id)

        return results

    except Exception as e:
        logger.error(f"Error syncing analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Process message and broadcast to others
            await manager.broadcast(
                {
                    "type": "user_action",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
