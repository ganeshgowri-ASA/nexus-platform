"""FastAPI routers for A/B testing module."""

from modules.ab_testing.api.experiments import router as experiments_router
from modules.ab_testing.api.metrics import router as metrics_router
from modules.ab_testing.api.variants import router as variants_router

__all__ = ["experiments_router", "metrics_router", "variants_router"]
