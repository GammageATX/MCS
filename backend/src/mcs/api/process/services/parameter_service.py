"""Parameter Service

This module implements the Parameter service for managing process parameters.
"""

import os
from pathlib import Path
from datetime import datetime

import yaml
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ComponentHealth
)
from mcs.api.process.models.process_models import ProcessStatus


class ParameterService:
    """Service for managing process parameters."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize parameter service."""
        self._service_name = "parameter"
        self._version = version
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        
        # Initialize components to None
        self._parameters = None
        self._failed_parameters = {}
        self._parameter_status = ProcessStatus.IDLE
        
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
    def is_initialized(self) -> bool:
        """Get service initialization state."""
        return self._is_initialized

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
            
            # Initialize parameters
            self._parameters = {}
            
            # Load parameters from config
            await self._load_parameters()
            
            self._is_initialized = True
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            if not self.is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            self._is_running = True
            self._start_time = datetime.now()
            self._parameter_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._parameter_status = ProcessStatus.ERROR
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

            self._is_initialized = False
            self._is_running = False
            self._start_time = None
            self._parameter_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service stopped")

        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ComponentHealth:
        """Get service health status."""
        try:
            if not self.is_running:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=f"{self.service_name} service not running"
                )

            # Check critical components
            parameters_loaded = self._parameters is not None and len(self._parameters) > 0
            parameter_dir = Path("backend/data/parameters")
            dir_exists = parameter_dir.exists()
            dir_writable = dir_exists and os.access(parameter_dir, os.W_OK)

            # Map process status to health status
            if self._parameter_status == ProcessStatus.ERROR:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error="Parameter system in error state",
                    details={
                        "parameters": {
                            "total": len(self._parameters or {}),
                            "loaded": list(self._parameters.keys()) if self._parameters else [],
                            "failed": list(self._failed_parameters.keys()),
                            "recovery_attempts": len(self._failed_parameters)
                        },
                        "storage": {
                            "path": str(parameter_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )
            elif self._parameter_status == ProcessStatus.PAUSED:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Parameter system paused",
                    details={
                        "parameters": {
                            "total": len(self._parameters or {}),
                            "loaded": list(self._parameters.keys()) if self._parameters else [],
                            "failed": list(self._failed_parameters.keys()),
                            "recovery_attempts": len(self._failed_parameters)
                        },
                        "storage": {
                            "path": str(parameter_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            # Check if any critical components are missing
            if not (parameters_loaded and dir_exists and dir_writable):
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Parameter system partially operational",
                    details={
                        "parameters": {
                            "total": len(self._parameters or {}),
                            "loaded": list(self._parameters.keys()) if self._parameters else [],
                            "failed": list(self._failed_parameters.keys()),
                            "recovery_attempts": len(self._failed_parameters)
                        },
                        "storage": {
                            "path": str(parameter_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            return ComponentHealth(
                status=HealthStatus.OK,
                error=None,
                details={
                    "parameters": {
                        "total": len(self._parameters or {}),
                        "loaded": list(self._parameters.keys()) if self._parameters else [],
                        "failed": list(self._failed_parameters.keys()),
                        "recovery_attempts": len(self._failed_parameters)
                    },
                    "storage": {
                        "path": str(parameter_dir),
                        "exists": dir_exists,
                        "writable": dir_writable
                    },
                    "uptime": self.uptime
                }
            )

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ComponentHealth(
                status=HealthStatus.ERROR,
                error=error_msg
            )

    async def _load_parameters(self) -> None:
        """Load parameters from configuration."""
        try:
            # Load service config
            config_path = os.path.join("backend", "config", "process.yaml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if "parameter" in config:
                        self._version = config["parameter"].get("version", self._version)
            
            # Load parameter files from data directory
            parameter_dir = Path("backend/data/parameters")
            if parameter_dir.exists():
                for file_path in parameter_dir.glob("*.yaml"):
                    try:
                        with open(file_path, "r") as f:
                            parameter_data = yaml.safe_load(f)
                            parameter_id = file_path.stem
                            self._parameters[parameter_id] = parameter_data
                            logger.info(f"Loaded parameter file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load parameter file {file_path.name}: {str(e)}")
                        self._failed_parameters[file_path.stem] = str(e)
                        
            logger.info(f"Loaded {len(self._parameters)} parameters from configuration")
            
        except Exception as e:
            error_msg = f"Failed to load parameters: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
