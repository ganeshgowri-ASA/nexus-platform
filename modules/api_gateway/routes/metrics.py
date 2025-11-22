from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from modules.api_gateway.database import get_db
from modules.api_gateway.models.metric import Metric

router = APIRouter(prefix="/admin/metrics", tags=["Metrics"])


@router.get("/summary")
def get_metrics_summary(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get metrics summary for the last N hours"""

    since = datetime.utcnow() - timedelta(hours=hours)

    # Total requests
    total_requests = db.query(func.count(Metric.id)).filter(
        Metric.timestamp >= since
    ).scalar()

    # Error count
    error_count = db.query(func.count(Metric.id)).filter(
        Metric.timestamp >= since,
        Metric.error == True
    ).scalar()

    # Average response time
    avg_response_time = db.query(func.avg(Metric.response_time)).filter(
        Metric.timestamp >= since
    ).scalar() or 0

    # Cache hit rate
    cache_hits = db.query(func.count(Metric.id)).filter(
        Metric.timestamp >= since,
        Metric.cache_hit == True
    ).scalar()

    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

    # Status code distribution
    status_codes = db.query(
        Metric.status_code,
        func.count(Metric.id).label("count")
    ).filter(
        Metric.timestamp >= since
    ).group_by(Metric.status_code).all()

    # Top routes
    top_routes = db.query(
        Metric.route_name,
        func.count(Metric.id).label("count"),
        func.avg(Metric.response_time).label("avg_response_time")
    ).filter(
        Metric.timestamp >= since,
        Metric.route_name.isnot(None)
    ).group_by(Metric.route_name).order_by(desc("count")).limit(10).all()

    return {
        "period_hours": hours,
        "total_requests": total_requests,
        "error_count": error_count,
        "error_rate": (error_count / total_requests * 100) if total_requests > 0 else 0,
        "avg_response_time_ms": round(avg_response_time, 2),
        "cache_hit_rate": round(cache_hit_rate, 2),
        "status_codes": {str(sc): count for sc, count in status_codes},
        "top_routes": [
            {
                "route": route,
                "requests": count,
                "avg_response_time_ms": round(avg_rt, 2)
            }
            for route, count, avg_rt in top_routes
        ]
    }


@router.get("/requests")
def get_request_metrics(
    skip: int = 0,
    limit: int = 100,
    route_name: Optional[str] = None,
    status_code: Optional[int] = None,
    error_only: bool = False,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get detailed request metrics"""

    since = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(Metric).filter(Metric.timestamp >= since)

    if route_name:
        query = query.filter(Metric.route_name == route_name)

    if status_code:
        query = query.filter(Metric.status_code == status_code)

    if error_only:
        query = query.filter(Metric.error == True)

    metrics = query.order_by(desc(Metric.timestamp)).offset(skip).limit(limit).all()

    return [
        {
            "id": m.id,
            "timestamp": m.timestamp,
            "method": m.method,
            "path": m.path,
            "route_name": m.route_name,
            "status_code": m.status_code,
            "response_time_ms": round(m.response_time, 2),
            "client_ip": m.client_ip,
            "error": m.error,
            "error_message": m.error_message if m.error else None,
            "cache_hit": m.cache_hit,
        }
        for m in metrics
    ]


@router.get("/timeseries")
def get_timeseries_metrics(
    interval_minutes: int = 60,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get time series metrics"""

    since = datetime.utcnow() - timedelta(hours=hours)

    # Group by time intervals
    metrics = db.query(
        func.date_trunc('hour', Metric.timestamp).label('time_bucket'),
        func.count(Metric.id).label('request_count'),
        func.avg(Metric.response_time).label('avg_response_time'),
        func.sum(func.cast(Metric.error, db.Integer)).label('error_count')
    ).filter(
        Metric.timestamp >= since
    ).group_by('time_bucket').order_by('time_bucket').all()

    return [
        {
            "timestamp": bucket,
            "requests": count,
            "avg_response_time_ms": round(avg_rt or 0, 2),
            "errors": error_count or 0
        }
        for bucket, count, avg_rt, error_count in metrics
    ]


@router.delete("/cleanup")
def cleanup_old_metrics(days: int = 30, db: Session = Depends(get_db)):
    """Delete metrics older than N days"""

    cutoff = datetime.utcnow() - timedelta(days=days)

    deleted = db.query(Metric).filter(Metric.timestamp < cutoff).delete()
    db.commit()

    return {"message": f"Deleted {deleted} metrics older than {days} days"}
