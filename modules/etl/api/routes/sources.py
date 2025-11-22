"""Data sources API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from modules.etl.models import DataSource
from modules.etl.schemas import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from modules.etl.core.tasks import test_connection_task
from shared.database import get_db

router = APIRouter()


@router.post("/", response_model=DataSourceResponse, status_code=201)
def create_data_source(source: DataSourceCreate, db: Session = Depends(get_db)):
    """Create a new data source."""
    # Check if name already exists
    existing = db.query(DataSource).filter(DataSource.name == source.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Data source with this name already exists")

    db_source = DataSource(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.get("/", response_model=List[DataSourceResponse])
def list_data_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all data sources."""
    sources = db.query(DataSource).offset(skip).limit(limit).all()
    return sources


@router.get("/{source_id}", response_model=DataSourceResponse)
def get_data_source(source_id: str, db: Session = Depends(get_db)):
    """Get a specific data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.put("/{source_id}", response_model=DataSourceResponse)
def update_data_source(source_id: str, source_update: DataSourceUpdate, db: Session = Depends(get_db)):
    """Update a data source."""
    db_source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Data source not found")

    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_source, field, value)

    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/{source_id}", status_code=204)
def delete_data_source(source_id: str, db: Session = Depends(get_db)):
    """Delete a data source."""
    db_source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Data source not found")

    db.delete(db_source)
    db.commit()
    return None


@router.post("/{source_id}/test")
def test_connection(source_id: str, db: Session = Depends(get_db)):
    """Test connection to data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    # Trigger async task
    task = test_connection_task.delay(source_id)
    return {"task_id": task.id, "status": "testing"}
