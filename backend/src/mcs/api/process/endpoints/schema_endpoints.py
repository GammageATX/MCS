"""Process schema endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Request, status, HTTPException
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.process.process_service import ProcessService

router = APIRouter(prefix="/schemas", tags=["schemas"])


def get_process_service(request: Request) -> ProcessService:
    """Get service instance from app state."""
    return request.app.state.service


@router.get(
    "/",
    response_model=List[str],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to list schemas"}
    }
)
async def list_schemas(
    service: ProcessService = Depends(get_process_service)
) -> List[str]:
    """List available schema types."""
    try:
        # Return list of available schema types
        return ["pattern", "parameter", "nozzle", "powder", "sequence"]
    except Exception as e:
        logger.error(f"Failed to list schemas: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list schemas: {str(e)}"
        )


@router.get(
    "/{entity_type}",
    response_model=Dict[str, Any],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Schema not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get schema"}
    }
)
async def get_schema(
    entity_type: str,
    service: ProcessService = Depends(get_process_service)
) -> Dict[str, Any]:
    """Get JSON Schema for entity type.
    
    Args:
        entity_type: Type of entity (pattern, parameter, nozzle, powder, sequence)
        service: Process service instance
        
    Returns:
        JSON Schema definition
    """
    try:
        schema = await service.schema_service.get_schema(entity_type)
        if not schema:
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Schema not found for type: {entity_type}"
            )
        return schema
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to get schema for {entity_type}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get schema: {str(e)}"
        )
