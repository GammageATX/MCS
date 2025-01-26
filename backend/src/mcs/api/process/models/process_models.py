"""Process API models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from mcs.utils.health import HealthStatus


# Enums
class NozzleType(str, Enum):
    """Nozzle types."""
    CONVERGENT_DIVERGENT = "convergent-divergent"
    CONVERGENT = "convergent"
    VENTED = "vented"
    FLAT_PLATE = "flat-plate"
    DE_LAVAL = "de laval"


class PatternType(str, Enum):
    """Pattern types."""
    LINEAR = "linear"
    SERPENTINE = "serpentine"
    SPIRAL = "spiral"


# Add new enums
class StepType(str, Enum):
    """Sequence step types."""
    INITIALIZE = "INITIALIZE"
    TROUGH = "TROUGH"
    PATTERN = "PATTERN"
    PARAMETERS = "PARAMETERS"
    SPRAY = "SPRAY"
    SHUTDOWN = "SHUTDOWN"


# Base Models
class SizeRange(BaseModel):
    """Powder size range."""
    min: float = Field(gt=0, description="Minimum particle size (μm)")
    max: float = Field(gt=0, description="Maximum particle size (μm)")


class Nozzle(BaseModel):
    """Nozzle model."""
    name: str
    manufacturer: str
    type: NozzleType
    description: str


class Powder(BaseModel):
    """Powder definition."""
    name: str
    type: str
    size: str
    manufacturer: str
    lot: str


class Pattern(BaseModel):
    """Pattern definition."""
    id: str
    name: str
    description: str
    type: PatternType
    params: Dict[str, Any]


class Parameter(BaseModel):
    """Process parameter definition."""
    name: str
    created: str
    author: str
    description: str
    nozzle: str
    main_gas: float
    feeder_gas: float
    frequency: int
    deagglomerator_speed: int


class SequenceMetadata(BaseModel):
    """Sequence metadata."""
    name: str
    version: str
    created: str
    author: str
    description: str


class SequenceStep(BaseModel):
    """Sequence step."""
    name: str
    step_type: StepType
    description: Optional[str] = None
    pattern_id: Optional[str] = None
    parameters: Optional[str] = None
    origin: Optional[List[float]] = None


class Sequence(BaseModel):
    """Sequence definition."""
    id: str
    metadata: SequenceMetadata
    steps: List[SequenceStep]


# Response Models
class BaseResponse(BaseModel):
    """Base response model."""
    message: str


class PatternResponse(BaseModel):
    """Pattern response."""
    pattern: Pattern


class PatternListResponse(BaseModel):
    """Pattern list response."""
    patterns: List[str] = Field(description="List of pattern IDs")


class ParameterResponse(BaseModel):
    """Parameter response."""
    parameter: Parameter


class ParameterListResponse(BaseModel):
    """Parameter list response."""
    parameters: List[Parameter]


class SequenceResponse(BaseModel):
    """Sequence response."""
    sequence: Sequence


class SequenceListResponse(BaseModel):
    """Sequence list response."""
    sequences: List[str] = Field(description="List of sequence IDs")


class ProcessStatus(str, Enum):
    """Process-specific status types."""
    IDLE = "idle"                # System ready but not active
    INITIALIZING = "initializing"  # When process is starting up
    RUNNING = "running"            # Process is actively running
    PAUSED = "paused"             # Process temporarily suspended
    COMPLETED = "completed"        # Process finished successfully
    ABORTED = "aborted"           # Process stopped by user
    ERROR = "error"               # System encountered an error
    
    @property
    def health_status(self) -> HealthStatus:
        """Map process status to health status."""
        status_map = {
            self.IDLE: HealthStatus.OK,
            self.INITIALIZING: HealthStatus.STARTING,
            self.RUNNING: HealthStatus.OK,
            self.PAUSED: HealthStatus.DEGRADED,
            self.COMPLETED: HealthStatus.OK,
            self.ABORTED: HealthStatus.ERROR,
            self.ERROR: HealthStatus.ERROR
        }
        return status_map.get(self, HealthStatus.ERROR)


class StatusResponse(BaseModel):
    """Status response."""
    status: ProcessStatus
    details: Optional[Dict[str, Any]] = None


class NozzleResponse(BaseModel):
    """Nozzle response."""
    nozzle: Nozzle


class NozzleListResponse(BaseModel):
    """List of nozzles response."""
    nozzles: List[Nozzle]


class PowderResponse(BaseModel):
    """Powder response."""
    powder: Powder


class PowderListResponse(BaseModel):
    """List of powders response."""
    powders: List[Powder]
