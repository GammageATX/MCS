"""Process API package."""

from fastapi import Request
from mcs.api.process.process_service import ProcessService
from mcs.api.process.process_app import create_process_service


async def get_process_service(request: Request) -> ProcessService:
    """Get process service instance from app state."""
    return request.app.state.service


__all__ = [
    "ProcessService",
    "get_process_service",
    "create_process_service"
]
