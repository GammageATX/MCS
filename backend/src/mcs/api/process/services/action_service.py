"""Action Service

This module implements the Action service for managing process actions.
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import HealthStatus, ComponentHealth
from mcs.api.process.models.process_models import ProcessStatus


class ActionService:
    """Service for managing process actions."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize action service.
        
        Args:
            config: Service configuration
        """
        # Basic properties
        self._service_name = "action"
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._is_initialized = False
        self._is_prepared = False
        self._start_time = None
        
        # State
        self._current_action = None
        self._action_status = ProcessStatus.IDLE
        
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
    def is_prepared(self) -> bool:
        """Get service preparation state."""
        return self._is_prepared

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
            
            # Actions are defined in config, no paths needed
            self._is_initialized = True
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def prepare(self) -> None:
        """Prepare service for operation."""
        try:
            if not self.is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Initialize state
            self._current_action = None
            self._action_status = ProcessStatus.IDLE

            self._is_prepared = True
            logger.info(f"{self.service_name} service prepared")

        except Exception as e:
            error_msg = f"Failed to prepare {self.service_name} service: {str(e)}"
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

            if not self.is_prepared:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not prepared"
                )

            self._is_running = True
            self._start_time = datetime.now()
            self._action_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._action_status = ProcessStatus.ERROR
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

            self._is_running = False
            self._start_time = None
            self._action_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service stopped")

        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        try:
            if self.is_running:
                await self.stop()
                
            self._is_initialized = False
            self._is_prepared = False
            self._current_action = None
            logger.info(f"{self.service_name} service shut down")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ComponentHealth:
        """Get service health."""
        status = HealthStatus.OK if self.is_running else HealthStatus.ERROR
        details = {
            "version": self._version,
            "uptime": self.uptime,
            "status": status,
            "initialized": self.is_initialized,
            "prepared": self.is_prepared,
            "current_action": self._current_action,
            "action_status": self._action_status
        }
        return ComponentHealth(
            name=self.service_name,
            status=status,
            details=details
        )

    async def get_action_status(self, action_id: str) -> ProcessStatus:
        """Get action execution status."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if not self._current_action:
                return ProcessStatus.IDLE
                
            if action_id != self._current_action:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Action {action_id} not found"
                )
                
            return self._action_status
            
        except Exception as e:
            error_msg = f"Failed to get status for action {action_id}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )
