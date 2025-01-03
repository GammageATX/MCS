"""Process API endpoints."""

from mcs.api.process.endpoints.process_endpoints import router as process_router
from mcs.api.process.endpoints.pattern_endpoints import router as pattern_router
from mcs.api.process.endpoints.parameter_endpoints import router as parameter_router
from mcs.api.process.endpoints.sequence_endpoints import router as sequence_router

__all__ = [
    "process_router",
    "pattern_router",
    "parameter_router",
    "sequence_router"
]
