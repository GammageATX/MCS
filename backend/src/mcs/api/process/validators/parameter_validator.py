"""Parameter validation for process API."""

from typing import Dict, Any
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.process.schemas import ParameterData


def validate_parameter(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameter data."""
    try:
        param_data = ParameterData(**data)
        return param_data.model_dump()
    except Exception as e:
        logger.error(f"Parameter validation failed: {e}")
        raise create_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(e)
        )
