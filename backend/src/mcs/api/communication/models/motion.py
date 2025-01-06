"""Motion request models."""

from typing import Optional
from pydantic import BaseModel, Field


class JogRequest(BaseModel):
    """Jog motion request."""
    axis: str = Field(..., description="Axis to jog (x, y, z)")
    direction: int = Field(..., ge=-1, le=1, description="Jog direction (-1, 0, 1)")
    velocity: float = Field(..., gt=0, description="Jog velocity in mm/s")


class MoveRequest(BaseModel):
    """Move request."""
    x: Optional[float] = Field(None, description="X target position in mm")
    y: Optional[float] = Field(None, description="Y target position in mm")
    z: Optional[float] = Field(None, description="Z target position in mm")
    velocity: float = Field(..., gt=0, description="Move velocity in mm/s")
    wait_complete: bool = Field(True, description="Wait for move to complete")
