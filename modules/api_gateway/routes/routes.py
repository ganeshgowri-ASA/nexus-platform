from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from modules.api_gateway.database import get_db
from modules.api_gateway.models.route import Route

router = APIRouter(prefix="/admin/routes", tags=["Routes"])


class RouteCreate(BaseModel):
    name: str
    path: str
    method: str
    target_url: str
    enabled: bool = True
    require_auth: bool = True
    rate_limit: int = 100
    rate_limit_window: int = 60
    load_balance_strategy: str = "round_robin"
    target_urls: List[str] = []
    cache_enabled: bool = False
    cache_ttl: int = 300
    request_transform: dict = None
    response_transform: dict = None
    headers_to_add: dict = {}
    headers_to_remove: List[str] = []
    timeout: float = 30.0
    description: str = None
    tags: List[str] = []


class RouteUpdate(BaseModel):
    name: str = None
    path: str = None
    method: str = None
    target_url: str = None
    enabled: bool = None
    require_auth: bool = None
    rate_limit: int = None
    rate_limit_window: int = None
    load_balance_strategy: str = None
    target_urls: List[str] = None
    cache_enabled: bool = None
    cache_ttl: int = None
    request_transform: dict = None
    response_transform: dict = None
    headers_to_add: dict = None
    headers_to_remove: List[str] = None
    timeout: float = None
    description: str = None
    tags: List[str] = None


@router.get("/", response_model=List[dict])
def list_routes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all routes"""
    routes = db.query(Route).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "path": r.path,
            "method": r.method,
            "target_url": r.target_url,
            "enabled": r.enabled,
            "require_auth": r.require_auth,
            "rate_limit": r.rate_limit,
            "cache_enabled": r.cache_enabled,
            "description": r.description,
            "created_at": r.created_at,
        }
        for r in routes
    ]


@router.get("/{route_id}")
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route"""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    return {
        "id": route.id,
        "name": route.name,
        "path": route.path,
        "method": route.method,
        "target_url": route.target_url,
        "enabled": route.enabled,
        "require_auth": route.require_auth,
        "rate_limit": route.rate_limit,
        "rate_limit_window": route.rate_limit_window,
        "load_balance_strategy": route.load_balance_strategy,
        "target_urls": route.target_urls,
        "cache_enabled": route.cache_enabled,
        "cache_ttl": route.cache_ttl,
        "request_transform": route.request_transform,
        "response_transform": route.response_transform,
        "headers_to_add": route.headers_to_add,
        "headers_to_remove": route.headers_to_remove,
        "timeout": route.timeout,
        "description": route.description,
        "tags": route.tags,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_route(route_data: RouteCreate, db: Session = Depends(get_db)):
    """Create a new route"""

    # Check if route with same name exists
    existing = db.query(Route).filter(Route.name == route_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Route with this name already exists")

    route = Route(**route_data.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)

    return {"id": route.id, "name": route.name, "message": "Route created successfully"}


@router.put("/{route_id}")
def update_route(route_id: int, route_data: RouteUpdate, db: Session = Depends(get_db)):
    """Update a route"""

    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Update fields
    update_data = route_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(route, field, value)

    db.commit()
    db.refresh(route)

    return {"id": route.id, "name": route.name, "message": "Route updated successfully"}


@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """Delete a route"""

    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    db.delete(route)
    db.commit()

    return {"message": "Route deleted successfully"}
