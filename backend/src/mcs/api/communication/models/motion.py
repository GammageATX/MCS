"""Motion control models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position model."""
    x: float = Field(0.0, description="X position in mm")
    y: float = Field(0.0, description="Y position in mm")
    z: float = Field(0.0, description="Z position in mm")


class JogRequest(BaseModel):
    """Jog request model."""
    axis: str = Field(..., description="Axis to jog (x, y, or z)")
    direction: int = Field(..., ge=-1, le=1, description="Jog direction (-1, 0, 1)")
    distance: float = Field(..., description="Jog distance in mm")


class MoveRequest(BaseModel):
    """Move request model."""
    x: float = Field(..., description="X position in mm")
    y: float = Field(..., description="Y position in mm")
    z: float = Field(..., description="Z position in mm")
    velocity: float = Field(..., gt=0, description="Move velocity in mm/s")


class MotionStatus(BaseModel):
    """Motion system status model."""
    is_enabled: bool = Field(False, description="Whether motion system is enabled")
    is_homed: bool = Field(False, description="Whether all axes are homed")
    is_moving: bool = Field(False, description="Whether any axis is moving")
    error: Optional[str] = Field(None, description="Current motion error if any")
    status: Dict[str, Any] = Field(default_factory=dict, description="Additional status information")


class MotionState(BaseModel):
    """Motion state model."""
    position: Position = Field(default_factory=Position, description="Current position")
    status: MotionStatus = Field(default_factory=MotionStatus, description="Motion system status")
