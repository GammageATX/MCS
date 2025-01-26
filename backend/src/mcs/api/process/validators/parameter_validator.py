"""Parameter validation for process API.

This module implements hardware-specific validation rules for process parameters.
These rules go beyond basic schema validation to ensure hardware safety and
operational constraints are met.
"""

from typing import Dict, Any
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error


def validate_parameter(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameter data against hardware constraints.
    
    Validates:
    - Gas flow rates against hardware capabilities
    - Feeder settings against operational limits
    - Parameter combinations for safe operation
    - System-specific constraints
    
    Args:
        data: Parameter data to validate
        
    Returns:
        Validated parameter data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if "process" not in data:
            raise ValueError("Missing process configuration")
            
        process = data["process"]
        
        # Validate gas flow combinations
        main_gas = float(process.get("main_gas", 0))
        feeder_gas = float(process.get("feeder_gas", 0))
        
        if main_gas + feeder_gas > 110:  # Hardware limit
            raise ValueError("Total gas flow exceeds system capacity (110 L/min)")
            
        if main_gas < feeder_gas:
            raise ValueError("Main gas flow must be greater than feeder gas flow")
            
        # Validate feeder settings
        frequency = float(process.get("frequency", 0))
        deagg_speed = float(process.get("deagglomerator_speed", 0))
        
        if frequency > 0 and deagg_speed == 0:
            raise ValueError("Deagglomerator must be active when feeder is running")
            
        if frequency > 500 and deagg_speed < 50:
            raise ValueError("High frequency requires minimum 50% deagglomerator speed")
            
        # Add more hardware-specific validations here
        
        return data
        
    except ValueError as e:
        logger.error(f"Parameter validation failed: {e}")
        raise create_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in parameter validation: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Validation error: {str(e)}"
        )
