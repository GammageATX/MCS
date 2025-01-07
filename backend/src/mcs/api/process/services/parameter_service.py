"""Parameter service implementation."""

import yaml
from typing import Dict, Any, List
from datetime import datetime
from fastapi import status
from loguru import logger
from pathlib import Path
import os

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health  # noqa: F401
from mcs.api.process.models.process_models import (  # noqa: F401
    Parameter,
    Nozzle,  # noqa: F401 - used in type hints
    Powder,  # noqa: F401 - used in type hints
    NozzleType
)


class ParameterService:
    """Service for managing process parameters."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize parameter service."""
        self._service_name = "parameter"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._parameters = None
        self._failed_parameters = {}  # Track failed parameter sets
        
        logger.info(f"{self.service_name} service initialized")

    @property
    def version(self) -> str:
        """Get service version."""
        return self._version

    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._service_name

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    @property
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Initialize parameter sets
            self._parameters = {}
            
            # Load config and parameter sets
            await self._load_parameters()
            
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_parameters(self) -> None:
        """Load parameters from files."""
        try:
            parameter_dir = Path("data/parameters")
            if not parameter_dir.exists():
                return
            
            for param_file in parameter_dir.glob("*.yaml"):
                try:
                    with open(param_file, "r") as f:
                        data = yaml.safe_load(f)
                        
                    if "process" not in data:  # Check for "process" key
                        logger.error(f"Missing 'process' root key in {param_file}")
                        continue
                        
                    param_data = data["process"]  # Get data under "process" key
                    parameter = Parameter(**param_data)
                    self._parameters[parameter.name] = parameter  # Use name as key
                    logger.info(f"Loaded parameter: {parameter.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load parameter set {param_file}: {e}")
                    self._failed_parameters[param_file.stem] = str(e)
                    continue
                
        except Exception as e:
            logger.error(f"Failed to load parameters: {e}")

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed parameter sets."""
        if self._failed_parameters:
            logger.info(f"Attempting to recover {len(self._failed_parameters)} failed parameter sets...")
            await self._load_parameters()

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            if self._parameters is None:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )
            
            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.service_name} service started")
            
        except Exception as e:
            self._is_running = False
            self._start_time = None
            error_msg = f"Failed to start {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop(self) -> None:
        """Stop service."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )
            
            # 1. Clear parameter data
            self._parameters.clear()
            
            # 2. Reset service state
            self._is_running = False
            self._start_time = None
            
            logger.info(f"{self.service_name} service stopped")
            
        except Exception as e:
            error_msg = f"Failed to stop {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ComponentHealth:
        """Get parameter service health status."""
        try:
            # Check critical components
            params_loaded = self._parameters is not None and len(self._parameters) > 0
            param_dir = Path("data/parameters")
            dir_exists = param_dir.exists()
            dir_writable = dir_exists and os.access(param_dir, os.W_OK)
            
            # Determine status based on critical checks
            status = HealthStatus.OK if (
                self.is_running and
                params_loaded and
                dir_exists and
                dir_writable
            ) else HealthStatus.ERROR

            return ComponentHealth(
                status=status,
                error=None if status == HealthStatus.OK else "Parameter system not operational",
                details={
                    "is_running": self.is_running,
                    "uptime": self.uptime,
                    "parameters": {
                        "total": len(self._parameters or {}),
                        "loaded": list(self._parameters.keys()) if self._parameters else [],
                        "failed": list(self._failed_parameters.keys()),
                        "recovery_attempts": len(self._failed_parameters)
                    },
                    "storage": {
                        "path": str(param_dir),
                        "exists": dir_exists,
                        "writable": dir_writable
                    }
                }
            )
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ComponentHealth(
                status=HealthStatus.ERROR,
                error=error_msg
            )

    async def list_parameters(self) -> List[Parameter]:
        """List available parameters."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            return list(self._parameters.values())
            
        except Exception as e:
            error_msg = "Failed to list parameters"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def get_parameter(self, param_id: str) -> Parameter:
        """Get parameter by ID."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            # Case-insensitive lookup
            param_id = param_id.lower()
            for param in self._parameters.values():
                if param.name.lower().replace(" ", "_") == param_id:
                    return param
                    
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Parameter {param_id} not found"
            )
                
        except Exception as e:
            error_msg = f"Failed to get parameter {param_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def create_parameter(self, parameter: Parameter) -> Parameter:
        """Create new parameter."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if parameter.id in self._parameters:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"Parameter {parameter.id} already exists"
                )
                
            self._parameters[parameter.id] = parameter
            logger.info(f"Created parameter {parameter.id}")
            
            return parameter
            
        except Exception as e:
            error_msg = f"Failed to create parameter {parameter.id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def update_parameter(self, parameter: Parameter) -> Parameter:
        """Update existing parameter."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if parameter.id not in self._parameters:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Parameter {parameter.id} not found"
                )
                
            self._parameters[parameter.id] = parameter
            logger.info(f"Updated parameter {parameter.id}")
            
            return parameter
            
        except Exception as e:
            error_msg = f"Failed to update parameter {parameter.id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_nozzles(self) -> None:
        """Load nozzle configurations."""
        try:
            # Update path to data/nozzles
            nozzle_dir = Path("data/nozzles")
            if not nozzle_dir.exists():
                return
            
            for nozzle_file in nozzle_dir.glob("*.yaml"):
                try:
                    with open(nozzle_file, "r") as f:
                        data = yaml.safe_load(f)
                    
                    if "nozzle" not in data:
                        logger.error(f"Missing 'nozzle' root key in {nozzle_file}")
                        continue
                    
                    nozzle_data = data["nozzle"]
                    self._nozzles[nozzle_data["name"]] = nozzle_data
                    logger.info(f"Loaded nozzle: {nozzle_data['name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to load nozzle {nozzle_file}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Failed to load nozzles: {e}")

    async def list_nozzles(self) -> List[Dict[str, Any]]:
        """List available nozzles."""
        try:
            # Load from data/nozzles directory
            nozzles = []
            nozzle_dir = Path("data/nozzles")
            if nozzle_dir.exists():
                for nozzle_file in nozzle_dir.glob("*.yaml"):
                    try:
                        with open(nozzle_file) as f:
                            data = yaml.safe_load(f)
                        if "nozzle" in data:
                            nozzle_data = data["nozzle"]
                            # Convert type string to enum value
                            if "type" in nozzle_data:
                                nozzle_type = nozzle_data["type"].replace("_", "-")
                                nozzle_data["type"] = NozzleType(nozzle_type)
                            nozzles.append(nozzle_data)
                    except Exception as e:
                        logger.error(f"Failed to load nozzle {nozzle_file}: {e}")
            return nozzles
        except Exception as e:
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to list nozzles: {str(e)}"
            )

    async def list_powders(self) -> List[Dict[str, Any]]:
        """List available powders."""
        try:
            # Load from data/powders directory
            powders = []
            powder_dir = Path("data/powders")
            if powder_dir.exists():
                for powder_file in powder_dir.glob("*.yaml"):
                    try:
                        with open(powder_file) as f:
                            data = yaml.safe_load(f)
                        if "powder" in data:
                            powders.append(data["powder"])
                    except Exception as e:
                        logger.error(f"Failed to load powder {powder_file}: {e}")
            return powders
        except Exception as e:
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to list powders: {str(e)}"
            )
