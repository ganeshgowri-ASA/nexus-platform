"""
Events API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.event import EventCreate, EventBatch, EventQuery, Event
from modules.analytics.storage.repositories import EventRepository

router = APIRouter()
event_repo = EventRepository()


@router.post("/", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db_session)):
    """Create a new event."""
    event_data = event.model_dump()
    return event_repo.create(db, **event_data)


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def create_events_batch(batch: EventBatch, db: Session = Depends(get_db_session)):
    """Create multiple events in batch."""
    items = [e.model_dump() for e in batch.events]
    events = event_repo.bulk_create(db, items)
    db.commit()
    return {"created": len(events)}


@router.get("/{event_id}", response_model=Event)
def get_event(event_id: str, db: Session = Depends(get_db_session)):
    """Get event by ID."""
    event = event_repo.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/query")
def query_events(query: EventQuery, db: Session = Depends(get_db_session)):
    """Query events with filters."""
    events = event_repo.get_by_filters(
        db,
        event_types=[et.value for et in query.event_types] if query.event_types else None,
        user_id=query.user_id,
        session_id=query.session_id,
        module=query.module,
        start_date=query.start_date,
        end_date=query.end_date,
        skip=(query.page - 1) * query.page_size,
        limit=query.page_size
    )
    return {"events": events, "total": len(events)}
