"""Process API endpoints."""

from fastapi import APIRouter, Depends, Request, status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth
from mcs.api.process.process_service import ProcessService

router = APIRouter(tags=["process"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/health",
    response_model=ServiceHealth,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service not available"}
    }
)
async def health(
    service: ProcessService = Depends(get_process_service)
) -> ServiceHealth:
    """Get service health status."""
    try:
        return await service.health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=str(e)
        )


@router.get("/version")
async def version(
    service: ProcessService = Depends(get_process_service)
):
    """Get service version."""
    return {"version": service.version}
