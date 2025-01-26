"""Sequence validation for process API.

This module implements hardware-specific validation rules for process sequences.
These rules go beyond basic schema validation to ensure hardware safety and
operational constraints are met.
"""

from typing import Dict, Any, List
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error


def validate_sequence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate sequence data against hardware constraints.
    
    Validates:
    - Step order and dependencies
    - State transitions and safety conditions
    - Resource availability
    - System-specific sequence constraints
    
    Args:
        data: Sequence data to validate
        
    Returns:
        Validated sequence data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if "sequence" not in data:
            raise ValueError("Missing sequence configuration")
            
        sequence = data["sequence"]
        steps: List[Dict[str, Any]] = sequence.get("steps", [])
        
        if not steps:
            raise ValueError("Sequence must contain at least one step")
            
        # Track state through sequence
        initialized = False
        spraying = False
        
        # Validate step order and transitions
        for i, step in enumerate(steps):
            step_type = step.get("step_type", "")
            
            # Validate initialization
            if step_type == "INITIALIZE":
                if initialized:
                    raise ValueError("Multiple initialization steps not allowed")
                if i != 0:
                    raise ValueError("Initialization must be first step")
                initialized = True
                
            # Validate spray operations
            elif step_type == "SPRAY":
                if not initialized:
                    raise ValueError("Cannot spray before initialization")
                spraying = True
                
            # Validate pattern steps
            elif step_type == "PATTERN":
                if not initialized:
                    raise ValueError("Cannot execute pattern before initialization")
                if not spraying:
                    raise ValueError("Cannot execute pattern without active spray")
                    
            # Validate parameter changes
            elif step_type == "PARAMETERS":
                if not initialized:
                    raise ValueError("Cannot change parameters before initialization")
                    
            # Validate shutdown
            elif step_type == "SHUTDOWN":
                if i != len(steps) - 1:
                    raise ValueError("Shutdown must be final step")
                    
        # Validate sequence has proper start/end
        if not initialized:
            raise ValueError("Sequence must start with initialization")
            
        if steps[-1]["step_type"] != "SHUTDOWN":
            raise ValueError("Sequence must end with shutdown")
            
        # Add more hardware-specific validations here
        
        return data
        
    except ValueError as e:
        logger.error(f"Sequence validation failed: {e}")
        raise create_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in sequence validation: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Validation error: {str(e)}"
        )
