"""Equipment state and request models."""

from pydantic import BaseModel, Field


# Request Models
class GasFlowRequest(BaseModel):
    """Request model for setting gas flow setpoint."""
    flow_setpoint: float = Field(..., description="Gas flow setpoint in SLPM")


class GasValveRequest(BaseModel):
    """Request model for setting gas valve state."""
    open: bool = Field(..., description="True to open valve, False to close")


class VacuumPumpRequest(BaseModel):
    """Request model for setting vacuum pump state."""
    start: bool = Field(..., description="True to start pump, False to stop")


class GateValveRequest(BaseModel):
    """Request model for setting gate valve state."""
    position: str = Field(..., description="Valve position: 'open' or 'closed'")


class ShutterRequest(BaseModel):
    """Request model for setting shutter state."""
    open: bool = Field(..., description="True to open shutter, False to close")


class NozzleSelectRequest(BaseModel):
    """Request model for setting active nozzle state."""
    nozzle_id: int = Field(..., description="ID of nozzle to select (1 or 2)")


class FeederRequest(BaseModel):
    """Feeder control request."""
    frequency: float = Field(..., ge=0, le=1000, description="Operating frequency in Hz")


class FeederStateRequest(BaseModel):
    """Request model for setting feeder state."""
    running: bool = Field(..., description="True to start feeder, False to stop")


class DeagglomeratorRequest(BaseModel):
    """Deagglomerator control request."""
    duty_cycle: float = Field(..., ge=20, le=35, description="Duty cycle percentage")
    # Frequency is fixed at 500Hz, so removed from state updates
