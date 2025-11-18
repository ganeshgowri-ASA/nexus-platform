# Attribution Module Documentation

## Overview

The NEXUS Attribution Module provides comprehensive multi-touch attribution analysis for marketing campaigns, enabling data-driven decision making through advanced attribution models, AI-powered insights, and detailed journey visualization.

## Architecture

### Components

1. **Attribution Service**: Core business logic for attribution calculations
2. **AI Attribution Service**: Claude AI-powered data-driven attribution
3. **Journey Service**: Customer journey mapping and visualization
4. **Analytics Service**: Channel ROI and performance analysis
5. **Integrations Service**: Platform integrations (GA, Facebook Ads, etc.)

### Database Schema

#### Core Tables

**channels**: Marketing channels configuration
- id, name, channel_type, description
- cost_per_click, cost_per_impression, monthly_budget
- is_active, metadata

**journeys**: Customer journeys
- id, user_id, session_id
- start_time, end_time, total_touchpoints
- conversion_value, has_conversion, journey_duration_minutes

**touchpoints**: Individual interactions
- id, journey_id, channel_id
- touchpoint_type, timestamp, position_in_journey
- time_spent_seconds, pages_viewed, engagement_score, cost
- campaign data, device/browser info

**conversions**: Conversion events
- id, journey_id, conversion_type
- timestamp, revenue, quantity
- product details

**attribution_models**: Model configurations
- id, name, model_type, description
- time_decay_halflife_days, position_weights, custom_rules
- ml_model_type, ml_parameters

**attribution_results**: Attribution calculations
- id, journey_id, attribution_model_id, channel_id
- credit, attributed_revenue, attributed_conversions
- channel_cost, roi, roas

## Attribution Models

### 1. First-Touch Attribution

**Algorithm**:
```python
def first_touch(touchpoints, conversion_value):
    first_touchpoint = touchpoints[0]
    return {first_touchpoint.channel_id: conversion_value}
```

**Use Case**: Understanding top-of-funnel channel effectiveness

**Pros**:
- Simple to understand
- Highlights discovery channels
- Good for brand awareness analysis

**Cons**:
- Ignores mid-funnel and conversion touchpoints
- May overvalue initial interactions

### 2. Last-Touch Attribution

**Algorithm**:
```python
def last_touch(touchpoints, conversion_value):
    last_touchpoint = touchpoints[-1]
    return {last_touchpoint.channel_id: conversion_value}
```

**Use Case**: Direct conversion channel identification

**Pros**:
- Simple implementation
- Focuses on conversion driver
- Traditional default model

**Cons**:
- Ignores customer journey complexity
- May overvalue closing channels

### 3. Linear Attribution

**Algorithm**:
```python
def linear(touchpoints, conversion_value):
    credit_per_touchpoint = conversion_value / len(touchpoints)
    return aggregate_by_channel(touchpoints, credit_per_touchpoint)
```

**Use Case**: Equal credit distribution across journey

**Pros**:
- Fair to all touchpoints
- Simple to explain
- Considers full journey

**Cons**:
- Doesn't account for touchpoint importance
- May undervalue key interactions

### 4. Time-Decay Attribution

**Algorithm**:
```python
def time_decay(touchpoints, conversion_value, halflife_days=7):
    decay_rate = ln(2) / halflife_days
    weights = []
    for tp in touchpoints:
        time_diff_days = (conversion_time - tp.timestamp).days
        weight = exp(-decay_rate * time_diff_days)
        weights.append(weight)

    normalized_weights = [w / sum(weights) for w in weights]
    return distribute_credit(touchpoints, normalized_weights, conversion_value)
```

**Use Case**: Recent interactions more valuable

**Pros**:
- Values recency appropriately
- Configurable half-life
- Balances journey consideration

**Cons**:
- Requires tuning half-life parameter
- May undervalue early touchpoints

**Configuration**:
- `time_decay_halflife_days`: Days for weight to halve (default: 7)

### 5. Position-Based (U-Shaped) Attribution

**Algorithm**:
```python
def position_based(touchpoints, conversion_value, weights={"first": 0.4, "middle": 0.2, "last": 0.4}):
    first_credit = conversion_value * weights["first"]
    last_credit = conversion_value * weights["last"]
    middle_total = conversion_value * weights["middle"]
    middle_credit_each = middle_total / len(middle_touchpoints)

    return {
        first_touchpoint.channel_id: first_credit,
        last_touchpoint.channel_id: last_credit,
        **{tp.channel_id: middle_credit_each for tp in middle_touchpoints}
    }
```

**Use Case**: Valuing discovery and conversion equally

**Pros**:
- Recognizes both awareness and conversion
- Configurable weight distribution
- Balances journey importance

**Cons**:
- Middle touchpoints may be undervalued
- Requires position weight tuning

**Configuration**:
```json
{
  "first": 0.4,
  "middle": 0.2,
  "last": 0.4
}
```

### 6. Data-Driven (AI-Powered) Attribution

**Algorithm**:
Uses Claude AI to analyze:
- Touchpoint position and sequence
- Engagement metrics (time spent, pages viewed)
- Channel characteristics
- Campaign context
- Timing patterns

**Process**:
1. Prepare journey data with all touchpoint details
2. Send to Claude AI with analysis prompt
3. Receive intelligent attribution weights
4. Normalize and distribute credit

**Use Case**: Complex journeys requiring intelligent analysis

**Pros**:
- Considers multiple factors simultaneously
- Adapts to journey complexity
- Provides reasoning for attribution

**Cons**:
- Requires API calls (latency)
- Less deterministic than algorithmic models
- API costs

**Configuration**:
- `ml_model_type`: "claude-sonnet-4-5-20250929"
- `training_data_window_days`: Historical data window (default: 90)

## API Usage Examples

### Creating a Journey

```python
import requests

# Create journey
response = requests.post(
    "http://localhost:8000/api/v1/attribution/journeys",
    json={
        "user_id": "user_123",
        "session_id": "session_456",
        "start_time": "2025-01-01T10:00:00Z"
    }
)
journey = response.json()

# Add touchpoints
touchpoint1 = requests.post(
    "http://localhost:8000/api/v1/attribution/touchpoints",
    json={
        "journey_id": journey["id"],
        "channel_id": 1,
        "touchpoint_type": "click",
        "timestamp": "2025-01-01T10:00:00Z",
        "position_in_journey": 1,
        "engagement_score": 0.8,
        "cost": 1.50
    }
)

# Add conversion
conversion = requests.post(
    "http://localhost:8000/api/v1/attribution/conversions",
    json={
        "journey_id": journey["id"],
        "conversion_type": "purchase",
        "timestamp": "2025-01-01T12:00:00Z",
        "revenue": 99.99
    }
)
```

### Calculating Attribution

```python
# Calculate with specific model
results = requests.post(
    f"http://localhost:8000/api/v1/attribution/calculate/{journey_id}/{model_id}"
)

# Bulk calculation
bulk_results = requests.post(
    "http://localhost:8000/api/v1/attribution/calculate/bulk",
    json={
        "journey_ids": [1, 2, 3, 4, 5],
        "model_ids": [1, 2, 3],
        "use_cache": True
    }
)
```

### Getting AI Insights

```python
# Get performance insights
insights = requests.post(
    "http://localhost:8000/api/v1/attribution/ai/insights",
    json={
        "journey_ids": [1, 2, 3, 4, 5],
        "analysis_type": "performance"  # or "optimization", "trends"
    }
)

print(insights.json()["insights"])
```

### Analyzing Channel ROI

```python
roi_data = requests.post(
    "http://localhost:8000/api/v1/attribution/analytics/channel-roi",
    json={
        "channel_ids": [1, 2, 3],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "attribution_model_id": 1
    }
)

for channel in roi_data.json():
    print(f"{channel['channel_name']}: ROI={channel['roi']:.2f}%")
```

## Performance Optimization

### Caching Strategy

- **Attribution Results**: Cached for 1 hour (configurable via `ATTRIBUTION_CACHE_TTL`)
- **Journey Visualizations**: Cached per journey-model combination
- **Analytics Reports**: Cached based on date range and parameters

Cache keys pattern: `attribution:*`

### Database Indexes

Critical indexes for performance:
- `idx_touchpoint_journey` on touchpoints(journey_id)
- `idx_touchpoint_timestamp` on touchpoints(timestamp)
- `idx_journey_user` on journeys(user_id)
- `idx_journey_conversion` on journeys(has_conversion)

### Batch Operations

Use bulk endpoints for multiple journeys:
```python
# Better
bulk_calculate(journey_ids=[1,2,3,4,5], model_ids=[1,2])

# Avoid
for journey_id in journey_ids:
    for model_id in model_ids:
        calculate(journey_id, model_id)
```

## Platform Integrations

### Google Analytics

```python
from backend.app.services.integrations_service import (
    GoogleAnalyticsIntegration,
    IntegrationsService
)

# Setup integration
ga_integration = GoogleAnalyticsIntegration(
    api_key="your_ga_key",
    property_id="GA4_PROPERTY_ID"
)

# Register with service
integrations_service = IntegrationsService(db)
integrations_service.register_integration("google_analytics", ga_integration)

# Import data
result = integrations_service.import_from_platform(
    platform="google_analytics",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    user_id="user_123"
)
```

### Facebook Ads

Similar pattern with `FacebookAdsIntegration`

### Custom Integrations

Extend `PlatformIntegration` base class:

```python
class CustomPlatformIntegration(PlatformIntegration):
    def fetch_touchpoints(self, start_date, end_date):
        # Implement touchpoint fetching
        pass

    def fetch_conversions(self, start_date, end_date):
        # Implement conversion fetching
        pass

    def push_attribution_data(self, attribution_results):
        # Implement data export
        pass
```

## Best Practices

### Model Selection

1. **First-Touch**: Use for brand awareness campaigns
2. **Last-Touch**: Use for direct response campaigns
3. **Linear**: Use when all touchpoints equally important
4. **Time-Decay**: Use for typical e-commerce journeys
5. **Position-Based**: Use for balanced view of discovery and conversion
6. **Data-Driven**: Use for complex, high-value journeys

### Journey Tracking

- Track all meaningful interactions
- Use consistent user_id and session_id
- Include campaign context (campaign_id, campaign_name)
- Record engagement metrics (time_spent, pages_viewed)
- Set accurate costs for ROI calculations

### Performance Tips

- Enable caching for production (`use_cache=True`)
- Use bulk operations for multiple journeys
- Limit date ranges for large datasets
- Pre-calculate attribution during off-peak hours
- Monitor Redis memory usage

## Troubleshooting

### Common Issues

**Issue**: Attribution calculation fails
- Check journey has conversion
- Verify touchpoints exist
- Ensure model is active

**Issue**: Slow API responses
- Check cache hit rate
- Review database query performance
- Consider date range limits
- Monitor Redis connection

**Issue**: Incorrect attribution values
- Verify touchpoint timestamps
- Check model configuration
- Validate touchpoint positions
- Review conversion value

## Monitoring

### Key Metrics

- Attribution calculation latency
- Cache hit rate
- API error rate
- Database query time
- Journey processing rate

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Cache health
curl http://localhost:8000/api/v1/attribution/cache/health
```

## Future Enhancements

- Shapley value attribution
- Markov chain models
- Real-time attribution updates
- Advanced ML model support
- Enhanced platform integrations
- Multi-tenant support
