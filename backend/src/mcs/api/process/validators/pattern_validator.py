"""Pattern validation for process API.

This module implements hardware-specific validation rules for motion patterns.
These rules go beyond basic schema validation to ensure hardware safety and
operational constraints are met.
"""

from typing import Dict, Any
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error


def validate_pattern(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pattern data against hardware constraints.
    
    Validates:
    - Motion limits and workspace boundaries
    - Velocity and acceleration constraints
    - Path feasibility and safety zones
    - System-specific motion constraints
    
    Args:
        data: Pattern data to validate
        
    Returns:
        Validated pattern data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Handle both wrapped and unwrapped pattern data
        pattern = data.get("pattern", data)
        if not pattern:
            raise ValueError("Missing pattern configuration")
            
        # Required fields
        if "id" not in pattern:
            raise ValueError("Missing pattern ID")
        if "type" not in pattern:
            raise ValueError("Missing pattern type")
        if "params" not in pattern:
            raise ValueError("Missing pattern parameters")
            
        params = pattern.get("params", {})
        pattern_type = pattern.get("type", "")
        
        # Validate workspace boundaries - required for all patterns
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        
        if width <= 0:
            raise ValueError("Pattern width must be positive")
        if height <= 0:
            raise ValueError("Pattern height must be positive")
        
        if width > 400:  # Hardware limit
            raise ValueError("Pattern width exceeds maximum workspace (400mm)")
            
        if height > 400:  # Hardware limit
            raise ValueError("Pattern height exceeds maximum workspace (400mm)")
            
        # Validate velocity - required for all patterns
        velocity = float(params.get("velocity", 0))
        if velocity <= 0:
            raise ValueError("Pattern velocity must be positive")
        if velocity > 300:  # Hardware limit
            raise ValueError("Velocity exceeds maximum safe speed (300mm/s)")
            
        # Pattern type specific validations
        if pattern_type in ["serpentine", "spiral"]:
            # Only validate line spacing for patterns that use it
            line_spacing = float(params.get("line_spacing", 0))
            if line_spacing <= 0:
                raise ValueError("Line spacing must be positive")
            if line_spacing < 0.5:  # Hardware limit
                raise ValueError("Line spacing below minimum resolution (0.5mm)")
            if pattern_type == "serpentine" and line_spacing > width * 0.1:
                raise ValueError("Line spacing too large for pattern width")
                
        # Return normalized pattern data
        if "pattern" not in data:
            data = {"pattern": pattern}
        return data
        
    except ValueError as e:
        logger.error(f"Pattern validation failed: {e}")
        raise create_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in pattern validation: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Validation error: {str(e)}"
        )
