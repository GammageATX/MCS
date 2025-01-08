"""Schema Service

This module implements the Schema service for managing process schemas.
"""

from datetime import datetime

from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ComponentHealth
)
from mcs.api.process.models.process_models import ProcessStatus


class SchemaService:
    """Service for managing process schemas."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize schema service."""
        self._service_name = "schema"
        self._version = version
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        
        # Initialize components to None
        self._schemas = None
        self._failed_schemas = {}
        self._schema_status = ProcessStatus.IDLE
        
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
            
            # Initialize schemas
            self._schemas = {}
            
            # Load schemas from config
            await self._load_schemas()
            
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
            self._schema_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._schema_status = ProcessStatus.ERROR
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
            self._schema_status = ProcessStatus.IDLE
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
            schemas_loaded = self._schemas is not None and len(self._schemas) > 0

            # Map process status to health status
            if self._schema_status == ProcessStatus.ERROR:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error="Schema system in error state",
                    details={
                        "schemas": {
                            "total": len(self._schemas or {}),
                            "loaded": list(self._schemas.keys()) if self._schemas else [],
                            "failed": list(self._failed_schemas.keys()),
                            "recovery_attempts": len(self._failed_schemas)
                        }
                    }
                )
            elif self._schema_status == ProcessStatus.PAUSED:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Schema system paused",
                    details={
                        "schemas": {
                            "total": len(self._schemas or {}),
                            "loaded": list(self._schemas.keys()) if self._schemas else [],
                            "failed": list(self._failed_schemas.keys()),
                            "recovery_attempts": len(self._failed_schemas)
                        }
                    }
                )

            # Check if schemas are loaded
            if not schemas_loaded:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Schema system partially operational",
                    details={
                        "schemas": {
                            "total": len(self._schemas or {}),
                            "loaded": list(self._schemas.keys()) if self._schemas else [],
                            "failed": list(self._failed_schemas.keys()),
                            "recovery_attempts": len(self._failed_schemas)
                        }
                    }
                )

            return ComponentHealth(
                status=HealthStatus.OK,
                error=None,
                details={
                    "schemas": {
                        "total": len(self._schemas or {}),
                        "loaded": list(self._schemas.keys()) if self._schemas else [],
                        "failed": list(self._failed_schemas.keys()),
                        "recovery_attempts": len(self._failed_schemas)
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

    async def _load_schemas(self) -> None:
        """Load schema definitions."""
        try:
            # Import all schema definitions
            from mcs.api.process.schemas import (
                NozzleData, Nozzle, NozzleType,
                PatternData, Pattern, PatternParams, PatternType,
                ParameterData, ProcessParameters,
                PowderData, Powder, PowderMorphology, SizeRange,
                SequenceData, Sequence, SequenceMetadata, SequenceStep, StepType
            )
            
            # Store schema classes
            self._schemas = {
                "nozzle": {
                    "data": NozzleData,
                    "models": {
                        "nozzle": Nozzle,
                        "type": NozzleType
                    }
                },
                "pattern": {
                    "data": PatternData,
                    "models": {
                        "pattern": Pattern,
                        "params": PatternParams,
                        "type": PatternType
                    }
                },
                "parameter": {
                    "data": ParameterData,
                    "models": {
                        "parameters": ProcessParameters
                    }
                },
                "powder": {
                    "data": PowderData,
                    "models": {
                        "powder": Powder,
                        "morphology": PowderMorphology,
                        "size_range": SizeRange
                    }
                },
                "sequence": {
                    "data": SequenceData,
                    "models": {
                        "sequence": Sequence,
                        "metadata": SequenceMetadata,
                        "step": SequenceStep,
                        "step_type": StepType
                    }
                }
            }
            
            logger.info(f"Loaded {len(self._schemas)} schema definitions")
            
        except Exception as e:
            error_msg = f"Failed to load schemas: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
