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


@router.post(
    "/initialize",
    responses={
        status.HTTP_409_CONFLICT: {"description": "Service already initialized"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service failed to initialize"}
    }
)
async def initialize(
    service: ProcessService = Depends(get_process_service)
):
    """Initialize service and prepare for operations."""
    try:
        # Initialize service
        await service.initialize()
        
        # Prepare service after initialization
        await service.prepare()
        
        return {"status": "initialized"}
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=str(e)
        )


@router.post(
    "/start",
    responses={
        status.HTTP_409_CONFLICT: {"description": "Service already running"},
        status.HTTP_400_BAD_REQUEST: {"description": "Service not initialized"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service failed to start"}
    }
)
async def start(
    service: ProcessService = Depends(get_process_service)
):
    """Start service operations.
    
    If the service is not initialized, it will be initialized and prepared first.
    """
    try:
        # Initialize and prepare if needed
        if not service.is_initialized:
            logger.info("Service needs initialization, initializing first...")
            await service.initialize()
            await service.prepare()
            
        # Start service operations
        await service.start()
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=str(e)
        )


@router.post(
    "/stop",
    responses={
        status.HTTP_409_CONFLICT: {"description": "Service not running"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service failed to stop"}
    }
)
async def stop(
    service: ProcessService = Depends(get_process_service)
):
    """Stop service operations and cleanup resources."""
    try:
        await service.shutdown()
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=str(e)
        )
