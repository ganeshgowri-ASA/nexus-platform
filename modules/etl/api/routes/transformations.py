"""Transformations API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from modules.etl.models import Transformation
from modules.etl.schemas import TransformationCreate, TransformationUpdate, TransformationResponse
from shared.database import get_db

router = APIRouter()


@router.post("/", response_model=TransformationResponse, status_code=201)
def create_transformation(transformation: TransformationCreate, db: Session = Depends(get_db)):
    """Create a new transformation template."""
    # Check if name already exists
    existing = db.query(Transformation).filter(Transformation.name == transformation.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Transformation with this name already exists")

    db_transformation = Transformation(**transformation.model_dump())
    db.add(db_transformation)
    db.commit()
    db.refresh(db_transformation)
    return db_transformation


@router.get("/", response_model=List[TransformationResponse])
def list_transformations(
    skip: int = 0, limit: int = 100, public_only: bool = False, db: Session = Depends(get_db)
):
    """List all transformation templates."""
    query = db.query(Transformation)
    if public_only:
        query = query.filter(Transformation.is_public == True)

    transformations = query.offset(skip).limit(limit).all()
    return transformations


@router.get("/{transformation_id}", response_model=TransformationResponse)
def get_transformation(transformation_id: str, db: Session = Depends(get_db)):
    """Get a specific transformation template."""
    transformation = db.query(Transformation).filter(Transformation.id == transformation_id).first()
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    return transformation


@router.put("/{transformation_id}", response_model=TransformationResponse)
def update_transformation(
    transformation_id: str, transformation_update: TransformationUpdate, db: Session = Depends(get_db)
):
    """Update a transformation template."""
    db_transformation = db.query(Transformation).filter(Transformation.id == transformation_id).first()
    if not db_transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")

    update_data = transformation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transformation, field, value)

    db.commit()
    db.refresh(db_transformation)
    return db_transformation


@router.delete("/{transformation_id}", status_code=204)
def delete_transformation(transformation_id: str, db: Session = Depends(get_db)):
    """Delete a transformation template."""
    db_transformation = db.query(Transformation).filter(Transformation.id == transformation_id).first()
    if not db_transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")

    db.delete(db_transformation)
    db.commit()
    return None


@router.get("/categories/list")
def list_categories(db: Session = Depends(get_db)):
    """List all transformation categories."""
    categories = db.query(Transformation.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}
