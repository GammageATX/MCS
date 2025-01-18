"""Data Collection API package."""

from fastapi import Request
from mcs.api.data_collection.data_collection_service import DataCollectionService
from mcs.api.data_collection.data_collection_app import create_data_collection_service
from mcs.api.data_collection.data_collection_router import router as data_collection_router
from mcs.api.data_collection.data_collection_models import (
    SprayEvent,
    CollectionSession,
    CollectionResponse,
    SprayEventResponse,
    SprayEventListResponse
)


async def get_data_collection_service(request: Request) -> DataCollectionService:
    """Get data collection service instance from app state."""
    return request.app.state.service

__all__ = [
    "DataCollectionService",
    "get_data_collection_service",
    "create_data_collection_service",
    "data_collection_router",
    "SprayEvent",
    "CollectionSession",
    "CollectionResponse",
    "SprayEventResponse",
    "SprayEventListResponse"
]
