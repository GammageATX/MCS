"""Configuration API package."""

from fastapi import Request
from mcs.api.config.config_service import ConfigService
from mcs.api.config.config_app import create_config_service
from mcs.api.config.endpoints.config_endpoints import router as config_router


async def get_config_service(request: Request) -> ConfigService:
    """Get config service instance from app state."""
    return request.app.state.service

__all__ = [
    "ConfigService",
    "get_config_service",
    "create_config_service",
    "config_router"
]
