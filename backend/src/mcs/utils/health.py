"""Health check utilities."""

from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Standardized health status values."""
    OK = "ok"
    DEGRADED = "degraded"  # System functional but with reduced capabilities
    ERROR = "error"
    STARTING = "starting"
    STOPPED = "stopped"


def get_uptime(start_time: Optional[datetime]) -> float:
    """Get uptime in seconds since start time."""
    if start_time is None:
        return 0.0
    return (datetime.now() - start_time).total_seconds()


class ComponentHealth(BaseModel):
    """Component health status."""
    status: HealthStatus = Field(default=HealthStatus.OK)
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ServiceHealth(BaseModel):
    """Service health status."""
    status: HealthStatus = Field(default=HealthStatus.OK)
    service: str
    version: str
    is_running: bool = False
    uptime: float = 0.0
    mode: str = "normal"  # normal, mock, simulation
    error: Optional[str] = None
    components: Dict[str, ComponentHealth] = Field(default_factory=dict)


def create_error_health(service_name: str, version: str, error_msg: str) -> ServiceHealth:
    """Create an error health response."""
    return ServiceHealth(
        status=HealthStatus.ERROR,
        service=service_name,
        version=version,
        is_running=False,
        error=error_msg,
        components={"main": ComponentHealth(status=HealthStatus.ERROR, error=error_msg)}
    )


def create_simple_health(service_name: str, version: str, is_running: bool = True, uptime: float = 0.0) -> ServiceHealth:
    """Create a simple health response for basic services."""
    status = HealthStatus.OK if is_running else HealthStatus.STOPPED
    return ServiceHealth(
        status=status,
        service=service_name,
        version=version,
        is_running=is_running,
        uptime=uptime,
        components={"main": ComponentHealth(status=status)}
    )
