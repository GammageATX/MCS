"""Action Service

This module implements the Action service for managing process actions.
"""

import os
from datetime import datetime
import json
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ComponentHealth
)
from mcs.api.process.models.process_models import ProcessStatus


class ActionService:
    """Service for managing process actions."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize action service."""
        self._service_name = "action"
        self._version = version
        self._is_running = False
        self._is_initialized = False
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
            
            # Load config
            config_path = os.path.join("backend", "config", "process.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "action" in config:
                        self._version = config["action"].get("version", self._version)
            
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

            self._is_initialized = False
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

    async def health(self) -> ComponentHealth:
        """Get service health status."""
        try:
            if not self.is_running:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=f"{self.service_name} service not running"
                )

            # Map process status to health status
            if self._action_status == ProcessStatus.ERROR:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error="Action system in error state",
                    details={
                        "current_action": self._current_action,
                        "status": self._action_status.value
                    }
                )
            elif self._action_status == ProcessStatus.PAUSED:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Action system paused",
                    details={
                        "current_action": self._current_action,
                        "status": self._action_status.value
                    }
                )

            return ComponentHealth(
                status=HealthStatus.OK,
                error=None,
                details={
                    "current_action": self._current_action,
                    "status": self._action_status.value,
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
