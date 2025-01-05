"""Process service implementation."""

from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.process.services import (
    PatternService,
    ParameterService,
    SequenceService,
    SchemaService
)


class ProcessService:
    """Service for managing process execution."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize process service."""
        self._service_name = "process"
        self._version = version
        self._is_running = False
        self._start_time = None

        # Initialize sub-services
        self.pattern_service = PatternService()
        self.parameter_service = ParameterService()
        self.sequence_service = SequenceService()
        self.schema_service = SchemaService()

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            logger.info("Initializing process service...")
            
            # Initialize sub-services
            await self.pattern_service.initialize()
            await self.parameter_service.initialize()
            await self.sequence_service.initialize()
            await self.schema_service.initialize()
            
            logger.info("Process service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize process service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service."""
        try:
            logger.info("Starting process service...")
            
            # Start sub-services
            await self.pattern_service.start()
            await self.parameter_service.start()
            await self.sequence_service.start()
            await self.schema_service.start()
            
            self._is_running = True
            self._start_time = datetime.now()
            logger.info("Process service started")
            
        except Exception as e:
            error_msg = f"Failed to start process service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    async def stop(self) -> None:
        """Stop service."""
        try:
            logger.info("Stopping process service...")
            
            # Stop sub-services
            if self.pattern_service.is_running:
                await self.pattern_service.stop()
            if self.parameter_service.is_running:
                await self.parameter_service.stop()
            if self.sequence_service.is_running:
                await self.sequence_service.stop()
            if self.schema_service.is_running:
                await self.schema_service.stop()
            
            self._is_running = False
            self._start_time = None
            logger.info("Process service stopped")
            
        except Exception as e:
            error_msg = f"Failed to stop process service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def shutdown(self) -> None:
        """Shutdown service (alias for stop)."""
        await self.stop()

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Check critical components
            components = {}
            
            # Pattern service (critical for process execution)
            pattern_health = await self.pattern_service.health()
            pattern_ok = pattern_health and pattern_health.status == HealthStatus.OK
            components["pattern"] = ComponentHealth(
                status=HealthStatus.OK if pattern_ok else HealthStatus.ERROR,
                error=pattern_health.error if pattern_health else "Pattern service not available",
                details=pattern_health.components if pattern_health else None
            )
            
            # Parameter service (critical for process configuration)
            param_health = await self.parameter_service.health()
            param_ok = param_health and param_health.status == HealthStatus.OK
            components["parameter"] = ComponentHealth(
                status=HealthStatus.OK if param_ok else HealthStatus.ERROR,
                error=param_health.error if param_health else "Parameter service not available",
                details=param_health.components if param_health else None
            )
            
            # Sequence service (critical for process flow)
            seq_health = await self.sequence_service.health()
            seq_ok = seq_health and seq_health.status == HealthStatus.OK
            components["sequence"] = ComponentHealth(
                status=HealthStatus.OK if seq_ok else HealthStatus.ERROR,
                error=seq_health.error if seq_health else "Sequence service not available",
                details=seq_health.components if seq_health else None
            )
            
            # Schema service (critical for validation)
            schema_health = await self.schema_service.health()
            schema_ok = schema_health and schema_health.status == HealthStatus.OK
            components["schema"] = ComponentHealth(
                status=HealthStatus.OK if schema_ok else HealthStatus.ERROR,
                error=schema_health.error if schema_health else "Schema service not available",
                details=schema_health.components if schema_health else None
            )
            
            # Overall status is ERROR if any critical component is in error
            overall_status = HealthStatus.ERROR if any(
                c.status == HealthStatus.ERROR for c in components.values()
            ) else HealthStatus.OK

            return ServiceHealth(
                status=overall_status,
                service=self._service_name,
                version=self._version,
                is_running=self.is_running,
                uptime=self.uptime,
                error="Critical component failure" if overall_status == HealthStatus.ERROR else None,
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self._service_name, self._version, error_msg)

    @property
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0
