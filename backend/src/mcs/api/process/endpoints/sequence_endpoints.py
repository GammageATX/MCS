"""Sequence management endpoints."""

from fastapi import APIRouter, Depends, status, Request
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.process.process_service import ProcessService
from mcs.api.process.models import (
    BaseResponse,
    SequenceListResponse,
    SequenceResponse,
    StatusResponse
)

router = APIRouter(prefix="/sequences", tags=["sequences"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/",
    response_model=SequenceListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list sequences"}
    }
)
async def list_sequences(
    service: ProcessService = Depends(get_process_service)
) -> SequenceListResponse:
    """List available sequences."""
    try:
        sequences = await service.sequence_service.list_sequences()
        return SequenceListResponse(sequences=sequences)
    except Exception as e:
        logger.error(f"Failed to list sequences: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list sequences: {str(e)}"
        )


@router.post(
    "/{sequence_id}/start",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_409_CONFLICT: {"description": "Sequence already running"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to start sequence"}
    }
)
async def start_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Start sequence execution."""
    try:
        await service.sequence_service.start_sequence(sequence_id)
        return BaseResponse(message=f"Sequence {sequence_id} started")
    except Exception as e:
        logger.error(f"Failed to start sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to start sequence: {str(e)}"
        )


@router.post(
    "/{sequence_id}/stop",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to stop sequence"}
    }
)
async def stop_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Stop sequence execution."""
    try:
        await service.sequence_service.stop_sequence(sequence_id)
        return BaseResponse(message=f"Sequence {sequence_id} stopped")
    except Exception as e:
        logger.error(f"Failed to stop sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to stop sequence: {str(e)}"
        )


@router.get(
    "/{sequence_id}/status",
    response_model=StatusResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get status"}
    }
)
async def get_status(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> StatusResponse:
    """Get sequence status."""
    try:
        status = await service.sequence_service.get_sequence_status(sequence_id)
        return StatusResponse(status=status)
    except Exception as e:
        logger.error(f"Failed to get sequence status {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get sequence status: {str(e)}"
        )


@router.get(
    "/{sequence_id}",
    response_model=SequenceResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Sequence not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get sequence"}
    }
)
async def get_sequence(
    sequence_id: str,
    service: ProcessService = Depends(get_process_service)
) -> SequenceResponse:
    """Get sequence by ID."""
    try:
        return await service.sequence_service.get_sequence(sequence_id)
    except Exception as e:
        logger.error(f"Failed to get sequence {sequence_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get sequence: {str(e)}"
        )
