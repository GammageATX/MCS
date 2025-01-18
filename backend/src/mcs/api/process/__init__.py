"""Process API package."""

from fastapi import Request
from mcs.api.process.process_service import ProcessService
from mcs.api.process.process_app import create_process_service
from mcs.api.process.endpoints.process_endpoints import router as process_router
from mcs.api.process.endpoints.pattern_endpoints import router as pattern_router
from mcs.api.process.endpoints.parameter_endpoints import router as parameter_router
from mcs.api.process.endpoints.sequence_endpoints import router as sequence_router


async def get_process_service(request: Request) -> ProcessService:
    """Get process service instance from app state."""
    return request.app.state.service

__all__ = [
    "ProcessService",
    "get_process_service",
    "create_process_service",
    "process_router",
    "pattern_router",
    "parameter_router",
    "sequence_router"
]
