"""Motion control endpoints."""

from fastapi import APIRouter, Request, status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.communication.models.motion import (
    MotionState,
    Position,
    MoveRequest,
    MotionStatus
)


router = APIRouter(prefix="/motion", tags=["motion"])


@router.get("/state", response_model=MotionState)
async def get_motion_state(request: Request) -> MotionState:
    """Get current motion state."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )
            
        state = await service.motion.get_motion_state()
        return state
        
    except Exception as e:
        error_msg = "Failed to get motion state"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )


@router.get("/position", response_model=Position)
async def get_position(request: Request) -> Position:
    """Get current position."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )
            
        position = await service.motion.get_position()
        return position
        
    except Exception as e:
        error_msg = "Failed to get position"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )


@router.get("/status", response_model=MotionStatus)
async def get_status(request: Request) -> MotionStatus:
    """Get motion system status."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )
            
        motion_status = await service.motion.get_status()
        return motion_status
        
    except Exception as e:
        error_msg = "Failed to get motion status"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )


@router.post("/move", response_model=None)
async def move_to_position(request: Request, move_request: MoveRequest) -> None:
    """Move to position."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )
            
        await service.motion.move_to_position(move_request)
        
    except Exception as e:
        error_msg = "Failed to move to position"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )
