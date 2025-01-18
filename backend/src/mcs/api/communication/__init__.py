"""Communication API package."""

from fastapi import Request
from mcs.api.communication.communication_service import CommunicationService
from mcs.api.communication.communication_app import create_communication_service
from mcs.api.communication.endpoints import router as state_router
from mcs.api.communication.endpoints.equipment import router as equipment_router
from mcs.api.communication.endpoints.motion import router as motion_router


async def get_communication_service(request: Request) -> CommunicationService:
    """Get communication service instance from app state."""
    return request.app.state.service

__all__ = [
    "CommunicationService",
    "get_communication_service",
    "create_communication_service",
    "state_router",
    "equipment_router",
    "motion_router"
]
