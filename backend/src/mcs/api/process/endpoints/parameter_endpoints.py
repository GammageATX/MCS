"""Parameter API endpoints."""

from fastapi import APIRouter, Depends, Request, status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.process.process_service import ProcessService
from mcs.api.process.models.process_models import (
    ParameterResponse,
    ParameterListResponse,
    BaseResponse,
    Parameter,
    NozzleResponse,
    NozzleListResponse,
    PowderResponse,
    PowderListResponse
)

router = APIRouter(tags=["parameters"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/nozzles",
    response_model=NozzleListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list nozzles"}
    }
)
async def list_nozzles(
    service: ProcessService = Depends(get_process_service)
) -> NozzleListResponse:
    """List available nozzles."""
    try:
        nozzles = await service.parameter_service.list_nozzles()
        return NozzleListResponse(nozzles=nozzles)
    except Exception as e:
        logger.error(f"Failed to list nozzles: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list nozzles: {str(e)}"
        )


@router.get(
    "/nozzles/{nozzle_id}",
    response_model=NozzleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Nozzle not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get nozzle"}
    }
)
async def get_nozzle(
    nozzle_id: str,
    service: ProcessService = Depends(get_process_service)
) -> NozzleResponse:
    """Get nozzle by ID."""
    try:
        nozzle = await service.parameter_service.get_nozzle(nozzle_id)
        return NozzleResponse(nozzle=nozzle)
    except Exception as e:
        logger.error(f"Failed to get nozzle {nozzle_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get nozzle: {str(e)}"
        )


@router.get(
    "/powders",
    response_model=PowderListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list powders"}
    }
)
async def list_powders(
    service: ProcessService = Depends(get_process_service)
) -> PowderListResponse:
    """List available powders."""
    try:
        powders = await service.parameter_service.list_powders()
        return PowderListResponse(powders=powders)
    except Exception as e:
        logger.error(f"Failed to list powders: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list powders: {str(e)}"
        )


@router.get(
    "/powders/{powder_id}",
    response_model=PowderResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Powder not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get powder"}
    }
)
async def get_powder(
    powder_id: str,
    service: ProcessService = Depends(get_process_service)
) -> PowderResponse:
    """Get powder by ID."""
    try:
        powder = await service.parameter_service.get_powder(powder_id)
        return PowderResponse(powder=powder)
    except Exception as e:
        logger.error(f"Failed to get powder {powder_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get powder: {str(e)}"
        )


@router.get(
    "/",
    response_model=ParameterListResponse,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list parameters"}
    }
)
async def list_parameters(
    service: ProcessService = Depends(get_process_service)
) -> ParameterListResponse:
    """List available parameters."""
    try:
        parameters = await service.parameter_service.list_parameters()
        return ParameterListResponse(parameters=parameters)
    except Exception as e:
        logger.error(f"Failed to list parameters: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list parameters: {str(e)}"
        )


@router.post(
    "/generate",
    response_model=BaseResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to generate parameter set"}
    }
)
async def generate_parameter_set(
    parameter: Parameter,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Generate new parameter set."""
    try:
        param_id = await service.parameter_service.generate_parameter(parameter)
        return BaseResponse(message=f"Parameter set {param_id} generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate parameter set: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to generate parameter set: {str(e)}"
        )


@router.get(
    "/{param_id}",
    response_model=ParameterResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Parameter set not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get parameter set"}
    }
)
async def get_parameter_set(
    param_id: str,
    service: ProcessService = Depends(get_process_service)
) -> ParameterResponse:
    """Get parameter set by ID."""
    try:
        parameter = await service.parameter_service.get_parameter(param_id)
        return ParameterResponse(parameter=parameter)
    except Exception as e:
        logger.error(f"Failed to get parameter set {param_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get parameter set: {str(e)}"
        )


@router.put(
    "/{param_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Parameter set not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update parameter set"}
    }
)
async def update_parameter_set(
    param_id: str,
    parameter: Parameter,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Update parameter set."""
    try:
        await service.parameter_service.update_parameter(param_id, parameter)
        return BaseResponse(message=f"Parameter set {param_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update parameter set {param_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update parameter set: {str(e)}"
        )
