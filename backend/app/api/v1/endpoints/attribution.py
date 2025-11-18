"""
NEXUS Platform - Attribution API Endpoints
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.redis_client import redis_client
from backend.app.services.attribution_service import AttributionService
from backend.app.services.ai_attribution_service import AIAttributionService
from backend.app.services.journey_service import JourneyVisualizationService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.attribution import (
    # Channel schemas
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    # Journey schemas
    JourneyCreate,
    JourneyUpdate,
    JourneyResponse,
    # Touchpoint schemas
    TouchpointCreate,
    TouchpointUpdate,
    TouchpointResponse,
    # Conversion schemas
    ConversionCreate,
    ConversionUpdate,
    ConversionResponse,
    # Attribution Model schemas
    AttributionModelCreate,
    AttributionModelUpdate,
    AttributionModelResponse,
    # Attribution Result schemas
    AttributionResultResponse,
    # Analysis schemas
    AttributionAnalysisRequest,
    AttributionAnalysisResponse,
    JourneyVisualizationRequest,
    JourneyVisualizationResponse,
    ChannelROIRequest,
    ChannelROIResponse,
    # Pagination
    PaginationParams,
)
from backend.app.core.config import settings


router = APIRouter()


# ============================================================================
# Channel Endpoints
# ============================================================================

@router.post(
    "/channels",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a marketing channel",
)
def create_channel(
    channel: ChannelCreate,
    db: Session = Depends(get_db),
):
    """Create a new marketing channel."""
    service = AttributionService(db)
    result = service.create_channel(**channel.dict())
    return result


@router.get(
    "/channels/{channel_id}",
    response_model=ChannelResponse,
    summary="Get channel by ID",
)
def get_channel(
    channel_id: int = Path(..., description="Channel ID"),
    db: Session = Depends(get_db),
):
    """Get a specific channel by ID."""
    service = AttributionService(db)
    return service.get_channel(channel_id)


@router.get(
    "/channels",
    response_model=List[ChannelResponse],
    summary="List all channels",
)
def list_channels(
    active_only: bool = Query(True, description="Only active channels"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all marketing channels."""
    service = AttributionService(db)
    return service.list_channels(active_only=active_only, skip=skip, limit=limit)


@router.put(
    "/channels/{channel_id}",
    response_model=ChannelResponse,
    summary="Update channel",
)
def update_channel(
    channel_id: int = Path(..., description="Channel ID"),
    channel_update: ChannelUpdate = Body(...),
    db: Session = Depends(get_db),
):
    """Update a marketing channel."""
    service = AttributionService(db)
    channel = service.get_channel(channel_id)

    # Update fields
    for field, value in channel_update.dict(exclude_unset=True).items():
        setattr(channel, field, value)

    db.commit()
    db.refresh(channel)
    return channel


# ============================================================================
# Journey Endpoints
# ============================================================================

@router.post(
    "/journeys",
    response_model=JourneyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer journey",
)
def create_journey(
    journey: JourneyCreate,
    db: Session = Depends(get_db),
):
    """Create a new customer journey."""
    service = AttributionService(db)
    return service.create_journey(**journey.dict())


@router.get(
    "/journeys/{journey_id}",
    response_model=JourneyResponse,
    summary="Get journey by ID",
)
def get_journey(
    journey_id: int = Path(..., description="Journey ID"),
    db: Session = Depends(get_db),
):
    """Get a specific journey by ID."""
    service = AttributionService(db)
    return service.get_journey(journey_id)


@router.get(
    "/journeys/{journey_id}/visualization",
    response_model=JourneyVisualizationResponse,
    summary="Get journey visualization data",
)
def get_journey_visualization(
    journey_id: int = Path(..., description="Journey ID"),
    attribution_model_id: Optional[int] = Query(
        None, description="Attribution model ID for credit display"
    ),
    db: Session = Depends(get_db),
):
    """Get complete journey visualization with touchpoints and attribution."""
    service = JourneyVisualizationService(db)
    cache_key = f"journey:viz:{journey_id}:{attribution_model_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Calculate and cache
    result = service.get_journey_visualization(journey_id, attribution_model_id)
    redis_client.set(cache_key, result, ttl=settings.ATTRIBUTION_CACHE_TTL)

    return result


# ============================================================================
# Touchpoint Endpoints
# ============================================================================

@router.post(
    "/touchpoints",
    response_model=TouchpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a touchpoint",
)
def create_touchpoint(
    touchpoint: TouchpointCreate,
    db: Session = Depends(get_db),
):
    """Add a touchpoint to a journey."""
    service = AttributionService(db)
    return service.add_touchpoint(**touchpoint.dict())


# ============================================================================
# Conversion Endpoints
# ============================================================================

@router.post(
    "/conversions",
    response_model=ConversionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversion",
)
def create_conversion(
    conversion: ConversionCreate,
    db: Session = Depends(get_db),
):
    """Add a conversion to a journey."""
    service = AttributionService(db)
    return service.add_conversion(**conversion.dict())


# ============================================================================
# Attribution Model Endpoints
# ============================================================================

@router.post(
    "/models",
    response_model=AttributionModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create attribution model",
)
def create_attribution_model(
    model: AttributionModelCreate,
    db: Session = Depends(get_db),
):
    """Create a new attribution model configuration."""
    service = AttributionService(db)
    return service.create_attribution_model(**model.dict())


@router.get(
    "/models/{model_id}",
    response_model=AttributionModelResponse,
    summary="Get attribution model",
)
def get_attribution_model(
    model_id: int = Path(..., description="Model ID"),
    db: Session = Depends(get_db),
):
    """Get attribution model by ID."""
    service = AttributionService(db)
    return service.get_attribution_model(model_id)


@router.get(
    "/models",
    response_model=List[AttributionModelResponse],
    summary="List attribution models",
)
def list_attribution_models(
    active_only: bool = Query(True, description="Only active models"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all attribution models."""
    service = AttributionService(db)
    return service.list_attribution_models(active_only=active_only, skip=skip, limit=limit)


# ============================================================================
# Attribution Calculation Endpoints
# ============================================================================

@router.post(
    "/calculate/{journey_id}/{model_id}",
    response_model=List[AttributionResultResponse],
    summary="Calculate attribution for journey",
)
def calculate_attribution(
    journey_id: int = Path(..., description="Journey ID"),
    model_id: int = Path(..., description="Attribution model ID"),
    db: Session = Depends(get_db),
):
    """Calculate attribution for a specific journey using a model."""
    service = AttributionService(db)
    return service.calculate_attribution(journey_id, model_id)


@router.post(
    "/calculate/bulk",
    summary="Calculate attribution for multiple journeys",
)
def calculate_bulk_attribution(
    request: AttributionAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Calculate attribution for multiple journeys and models."""
    service = AttributionService(db)
    cache_key = f"attribution:bulk:{hash(str(request.dict()))}"

    # Try cache if enabled
    if request.use_cache:
        cached = redis_client.get(cache_key)
        if cached:
            return cached

    # Calculate
    results = service.calculate_bulk_attribution(
        request.journey_ids, request.model_ids
    )

    # Cache results
    if request.use_cache:
        redis_client.set(cache_key, results, ttl=settings.ATTRIBUTION_CACHE_TTL)

    return results


# ============================================================================
# AI-Powered Attribution Endpoints
# ============================================================================

@router.post(
    "/ai/calculate/{journey_id}/{model_id}",
    summary="Calculate data-driven attribution using AI",
)
def calculate_ai_attribution(
    journey_id: int = Path(..., description="Journey ID"),
    model_id: int = Path(..., description="Attribution model ID"),
    context: Optional[dict] = Body(None, description="Additional context"),
    db: Session = Depends(get_db),
):
    """Calculate data-driven attribution using AI/LLM."""
    service = AIAttributionService(db)
    return service.calculate_data_driven_attribution(journey_id, model_id, context)


@router.post(
    "/ai/insights",
    summary="Get AI-powered insights",
)
def get_ai_insights(
    journey_ids: List[int] = Body(..., description="Journey IDs"),
    analysis_type: str = Body("performance", description="Analysis type"),
    db: Session = Depends(get_db),
):
    """Get AI-powered insights for journeys."""
    service = AIAttributionService(db)
    cache_key = f"ai:insights:{hash(str(journey_ids))}:{analysis_type}"

    # Try cache
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Generate insights
    result = service.get_ai_insights(journey_ids, analysis_type)

    # Cache for 1 hour
    redis_client.set(cache_key, result, ttl=3600)

    return result


@router.post(
    "/ai/compare-models",
    summary="Compare attribution models with AI analysis",
)
def compare_models_ai(
    journey_ids: List[int] = Body(..., description="Journey IDs"),
    model_ids: List[int] = Body(..., description="Model IDs"),
    db: Session = Depends(get_db),
):
    """Use AI to compare attribution models and provide recommendations."""
    service = AIAttributionService(db)
    return service.compare_attribution_models(journey_ids, model_ids)


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.post(
    "/analytics/channel-roi",
    response_model=List[ChannelROIResponse],
    summary="Calculate channel ROI",
)
def calculate_channel_roi(
    request: ChannelROIRequest,
    db: Session = Depends(get_db),
):
    """Calculate ROI for marketing channels."""
    service = AnalyticsService(db)
    cache_key = f"analytics:roi:{hash(str(request.dict()))}"

    # Try cache
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Calculate
    result = service.calculate_channel_roi(
        channel_ids=request.channel_ids,
        start_date=request.start_date,
        end_date=request.end_date,
        attribution_model_id=request.attribution_model_id,
    )

    # Cache
    redis_client.set(cache_key, result, ttl=settings.ATTRIBUTION_CACHE_TTL)

    return result


@router.get(
    "/analytics/touchpoint-performance",
    summary="Analyze touchpoint performance",
)
def analyze_touchpoint_performance(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    group_by: str = Query("channel", description="Grouping: channel, type, position"),
    db: Session = Depends(get_db),
):
    """Analyze touchpoint performance by different dimensions."""
    service = AnalyticsService(db)
    return service.analyze_touchpoint_performance(start_date, end_date, group_by)


@router.post(
    "/analytics/channel-comparison",
    summary="Compare multiple channels",
)
def compare_channels(
    channel_ids: List[int] = Body(..., description="Channels to compare"),
    start_date: Optional[datetime] = Body(None),
    end_date: Optional[datetime] = Body(None),
    attribution_model_id: Optional[int] = Body(None),
    db: Session = Depends(get_db),
):
    """Compare multiple channels across key metrics."""
    service = AnalyticsService(db)
    return service.get_channel_comparison(
        channel_ids, start_date, end_date, attribution_model_id
    )


@router.get(
    "/analytics/trends",
    summary="Get trend analysis",
)
def get_trend_analysis(
    metric: str = Query(..., description="Metric: touchpoints, conversions, revenue, cost"),
    channel_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interval: str = Query("day", description="Interval: day, week, month"),
    db: Session = Depends(get_db),
):
    """Get trend analysis for a metric over time."""
    service = AnalyticsService(db)
    return service.get_trend_analysis(metric, channel_id, start_date, end_date, interval)


# ============================================================================
# Journey Analysis Endpoints
# ============================================================================

@router.get(
    "/journeys/conversion-paths",
    summary="Get common conversion paths",
)
def get_conversion_paths(
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_touchpoints: int = Query(1, ge=1),
    converted_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get common conversion path patterns."""
    service = JourneyVisualizationService(db)
    return service.get_conversion_paths(
        limit, start_date, end_date, min_touchpoints, converted_only
    )


@router.get(
    "/journeys/touchpoint-patterns",
    summary="Analyze touchpoint patterns",
)
def analyze_touchpoint_patterns(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Analyze touchpoint patterns and sequences."""
    service = JourneyVisualizationService(db)
    cache_key = f"patterns:{start_date}:{end_date}"

    # Try cache
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Analyze
    result = service.analyze_touchpoint_patterns(start_date, end_date)

    # Cache
    redis_client.set(cache_key, result, ttl=settings.ATTRIBUTION_CACHE_TTL)

    return result


@router.get(
    "/journeys/metrics",
    summary="Get journey metrics",
)
def get_journey_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Get aggregated journey metrics."""
    service = JourneyVisualizationService(db)
    return service.get_journey_metrics(start_date, end_date)


@router.get(
    "/journeys/{journey_id}/similar",
    summary="Find similar journeys",
)
def find_similar_journeys(
    journey_id: int = Path(..., description="Journey ID"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find journeys similar to the given journey."""
    service = JourneyVisualizationService(db)
    return service.find_similar_journeys(journey_id, limit)


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@router.delete(
    "/cache/clear",
    summary="Clear attribution cache",
)
def clear_cache(
    pattern: str = Query("attribution:*", description="Cache key pattern"),
):
    """Clear cached attribution data."""
    count = redis_client.clear_pattern(pattern)
    return {"cleared_keys": count, "pattern": pattern}


@router.get(
    "/cache/health",
    summary="Check cache health",
)
def check_cache_health():
    """Check Redis cache connection health."""
    try:
        redis_client.ping()
        return {"status": "healthy", "cache": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
