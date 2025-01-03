"""File service implementation."""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth


class FileService:
    """File service."""

    def __init__(self, base_path: str, version: str = "1.0.0"):
        """Initialize service."""
        self._service_name = "file"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._base_path = None
        self._failed_operations = {}  # Track failed file operations
        
        # Store constructor args for initialization
        self._init_base_path = base_path
        
        logger.info(f"{self.service_name} service initialized")

    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._service_name

    @property
    def version(self) -> str:
        """Get service version."""
        return self._version

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    @property
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    @property
    def base_path(self) -> str:
        """Get base path."""
        return self._base_path

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Initialize base path
            self._base_path = self._init_base_path
            
            # Create base directory if it doesn't exist
            try:
                os.makedirs(self._base_path, exist_ok=True)
                # If directory creation succeeds, remove from failed operations
                self._failed_operations.pop("base_dir", None)
            except Exception as e:
                self._failed_operations["base_dir"] = str(e)
                logger.error(f"Failed to create base directory: {e}")
            
            logger.info(f"Using base path: {self._base_path}")
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

            if not self._base_path:
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

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed operations."""
        if "base_dir" in self._failed_operations:
            try:
                os.makedirs(self._base_path, exist_ok=True)
                self._failed_operations.pop("base_dir")
                logger.info("Successfully recovered base directory")
            except Exception as e:
                logger.error(f"Failed to recover base directory: {e}")

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Attempt recovery of failed operations
            await self._attempt_recovery()
            
            # Check component health
            base_exists = os.path.exists(self._base_path) if self._base_path else False
            base_writable = os.access(self._base_path, os.W_OK) if base_exists else False
            
            # Build component status
            components = {
                "base_dir": ComponentHealth(
                    status="ok" if base_exists and base_writable else "error",
                    error=None if base_exists and base_writable else "Base directory not accessible"
                )
            }
            
            # Add failed operations component if any exist
            if self._failed_operations:
                failed_list = ", ".join(self._failed_operations.keys())
                components["failed_operations"] = ComponentHealth(
                    status="error",
                    error=f"Failed operations: {failed_list}"
                )
            
            # Overall status is error only if base directory is completely inaccessible
            overall_status = "error" if not base_exists else "ok"
            
            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None if overall_status == "ok" else "One or more components in error state",
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ServiceHealth(
                status="error",
                service=self.service_name,
                version=self.version,
                is_running=False,
                uptime=self.uptime,
                error=error_msg,
                components={name: ComponentHealth(status="error", error=error_msg)
                            for name in ["base_dir"]}
            )
