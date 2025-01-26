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
    PowderListResponse,
    Nozzle,
    Powder
)

router = APIRouter(prefix="/parameters", tags=["parameters"])


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


@router.post(
    "/nozzles",
    response_model=BaseResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to create nozzle"}
    }
)
async def create_nozzle(
    nozzle: Nozzle,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Create new nozzle configuration."""
    try:
        nozzle_id = await service.parameter_service.create_nozzle(nozzle)
        return BaseResponse(message=f"Nozzle {nozzle_id} created successfully")
    except Exception as e:
        logger.error(f"Failed to create nozzle: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create nozzle: {str(e)}"
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


@router.put(
    "/nozzles/{nozzle_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Nozzle not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update nozzle"}
    }
)
async def update_nozzle(
    nozzle_id: str,
    nozzle: Nozzle,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Update nozzle configuration."""
    try:
        await service.parameter_service.update_nozzle(nozzle_id, nozzle)
        return BaseResponse(message=f"Nozzle {nozzle_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update nozzle {nozzle_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update nozzle: {str(e)}"
        )


@router.delete(
    "/nozzles/{nozzle_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Nozzle not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to delete nozzle"}
    }
)
async def delete_nozzle(
    nozzle_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Delete nozzle configuration."""
    try:
        await service.parameter_service.delete_nozzle(nozzle_id)
        return BaseResponse(message=f"Nozzle {nozzle_id} deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete nozzle {nozzle_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete nozzle: {str(e)}"
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


@router.post(
    "/powders",
    response_model=BaseResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to create powder"}
    }
)
async def create_powder(
    powder: Powder,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Create new powder configuration."""
    try:
        powder_id = await service.parameter_service.create_powder(powder)
        return BaseResponse(message=f"Powder {powder_id} created successfully")
    except Exception as e:
        logger.error(f"Failed to create powder: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create powder: {str(e)}"
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


@router.put(
    "/powders/{powder_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Powder not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to update powder"}
    }
)
async def update_powder(
    powder_id: str,
    powder: Powder,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Update powder configuration."""
    try:
        await service.parameter_service.update_powder(powder_id, powder)
        return BaseResponse(message=f"Powder {powder_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update powder {powder_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update powder: {str(e)}"
        )


@router.delete(
    "/powders/{powder_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Powder not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to delete powder"}
    }
)
async def delete_powder(
    powder_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Delete powder configuration."""
    try:
        await service.parameter_service.delete_powder(powder_id)
        return BaseResponse(message=f"Powder {powder_id} deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete powder {powder_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete powder: {str(e)}"
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
    "/",
    response_model=BaseResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation failed"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to create parameter set"}
    }
)
async def create_parameter(
    parameter: Parameter,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Create new parameter set."""
    try:
        param_id = await service.parameter_service.create_parameter(parameter)
        return BaseResponse(message=f"Parameter set {param_id} created successfully")
    except Exception as e:
        logger.error(f"Failed to create parameter set: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create parameter set: {str(e)}"
        )


@router.get(
    "/{param_id}",
    response_model=ParameterResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Parameter set not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get parameter set"}
    }
)
async def get_parameter(
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
async def update_parameter(
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


@router.delete(
    "/{param_id}",
    response_model=BaseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Parameter set not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to delete parameter set"}
    }
)
async def delete_parameter(
    param_id: str,
    service: ProcessService = Depends(get_process_service)
) -> BaseResponse:
    """Delete parameter set."""
    try:
        await service.parameter_service.delete_parameter(param_id)
        return BaseResponse(message=f"Parameter set {param_id} deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete parameter set {param_id}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete parameter set: {str(e)}"
        )
