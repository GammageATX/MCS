"""Pattern API endpoints."""

from fastapi import APIRouter, Depends, Request, status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.process.process_service import ProcessService
from mcs.api.process.models.process_models import PatternResponse, PatternListResponse, BaseResponse, Pattern

router = APIRouter(tags=["patterns"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/",
    response_model=PatternListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list patterns"}
    }
)
async def list_patterns(
    service: ProcessService = Depends(get_process_service)
) -> PatternListResponse:
    """List available patterns."""
    try:
        patterns = await service.pattern_service.list_patterns()
        return PatternListResponse(patterns=patterns)
    except Exception as e:
        logger.error(f"Failed to list patterns: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list patterns: {str(e)}"
        )


@router.post(
    "/",
    response_model=BaseResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to create pattern"}
    }
)
async def create_pattern(
    pattern: Pattern,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Create new pattern."""
    try:
        pattern_id = await service.pattern_service.create_pattern(pattern)
        return BaseResponse(message=f"Pattern {pattern_id} created successfully")
    except Exception as e:
        logger.error(f"Failed to create pattern: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create pattern: {str(e)}"
        )


@router.get(
    "/{pattern_id}",
    response_model=PatternResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Pattern not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get pattern"}
    }
)
async def get_pattern(
    pattern_id: str,
    service: ProcessService = Depends(get_process_service)
) -> PatternResponse:
    """Get pattern by ID."""
    try:
        pattern = await service.pattern_service.get_pattern(pattern_id)
        return PatternResponse(pattern=pattern)
    except Exception as e:
        logger.error(f"Failed to get pattern {pattern_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get pattern: {str(e)}"
        )


@router.put(
    "/{pattern_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Pattern not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update pattern"}
    }
)
async def update_pattern(
    pattern_id: str,
    pattern: Pattern,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Update pattern."""
    try:
        await service.pattern_service.update_pattern(pattern_id, pattern)
        return BaseResponse(message=f"Pattern {pattern_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update pattern {pattern_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update pattern: {str(e)}"
        )


@router.delete(
    "/{pattern_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Pattern not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to delete pattern"}
    }
)
async def delete_pattern(
    pattern_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Delete pattern."""
    try:
        await service.pattern_service.delete_pattern(pattern_id)
        return BaseResponse(message=f"Pattern {pattern_id} deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete pattern {pattern_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete pattern: {str(e)}"
        )
