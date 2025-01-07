"""Action service implementation."""

import os
import yaml
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ComponentHealth, HealthStatus, create_error_health, get_uptime  # noqa: F401
from mcs.api.process.models import ProcessStatus


class ActionService:
    """Service for managing process actions."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize action service."""
        self._service_name = "action"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
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
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return get_uptime(self._start_time)

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Load config
            config_path = os.path.join("backend", "config", "process.yaml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if "action" in config:
                        self._version = config["action"].get("version", self._version)
            
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
            
            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.service_name} service started")
            
        except Exception as e:
            self._is_running = False
            self._start_time = None
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"Failed to start service: {str(e)}"
            )

    async def stop(self) -> None:
        """Stop service."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )
            
            # 1. Stop active actions
            if self._current_action:
                await self.stop_action(self._current_action)
            
            # 2. Clear action state
            self._current_action = None
            self._action_status = ProcessStatus.IDLE
            
            # 3. Reset service state
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
        """Get action service health status."""
        try:
            # Check critical components
            config_path = os.path.join("backend", "config", "process.yaml")
            config_exists = os.path.exists(config_path)
            config_readable = config_exists and os.access(config_path, os.R_OK)
            
            # Determine status based on critical checks
            status = HealthStatus.OK if (
                self.is_running and
                config_exists and
                config_readable
            ) else HealthStatus.ERROR

            return ComponentHealth(
                status=status,
                error=None if status == HealthStatus.OK else "Action system not operational",
                details={
                    "is_running": self.is_running,
                    "uptime": self.uptime,
                    "config": {
                        "exists": config_exists,
                        "readable": config_readable
                    },
                    "execution": {
                        "current_action": self._current_action,
                        "status": self._action_status.value if self._action_status else None
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

    async def start_action(self, action_id: str) -> ProcessStatus:
        """Start action execution."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if self._current_action:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"Action {self._current_action} already in progress"
                )
                
            self._current_action = action_id
            self._action_status = ProcessStatus.RUNNING
            logger.info(f"Started action {action_id}")
            
            return self._action_status
            
        except Exception as e:
            error_msg = f"Failed to start action {action_id}: {str(e)}"
            logger.error(error_msg)
            self._action_status = ProcessStatus.ERROR
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop_action(self, action_id: str) -> ProcessStatus:
        """Stop action execution."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if not self._current_action:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No action in progress"
                )
                
            if action_id != self._current_action:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Action {action_id} not in progress"
                )
                
            self._current_action = None
            self._action_status = ProcessStatus.IDLE
            logger.info(f"Stopped action {action_id}")
            
            return self._action_status
            
        except Exception as e:
            error_msg = f"Failed to stop action {action_id}: {str(e)}"
            logger.error(error_msg)
            self._action_status = ProcessStatus.ERROR
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
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
