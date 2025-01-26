"""Pattern Service

This module implements the Pattern service for managing process patterns.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import json
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ComponentHealth
)
from mcs.api.process.models.process_models import ProcessStatus, Pattern


class PatternService:
    """Service for managing process patterns."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize pattern service.
        
        Args:
            config: Service configuration
        """
        self._service_name = "pattern"
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        
        # Initialize components to None
        self._patterns = {}
        self._failed_patterns = {}
        self._pattern_status = ProcessStatus.IDLE
        
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
            
            # Initialize patterns
            self._patterns = {}
            
            # Load patterns from config
            await self._load_patterns()
            
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
            self._pattern_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._pattern_status = ProcessStatus.ERROR
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
            self._pattern_status = ProcessStatus.IDLE
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
            patterns_loaded = self._patterns is not None and len(self._patterns) > 0
            pattern_dir = Path("backend/data/patterns")
            dir_exists = pattern_dir.exists()
            dir_writable = dir_exists and os.access(pattern_dir, os.W_OK)

            # Map process status to health status
            if self._pattern_status == ProcessStatus.ERROR:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error="Pattern system in error state",
                    details={
                        "patterns": {
                            "total": len(self._patterns or {}),
                            "loaded": list(self._patterns.keys()) if self._patterns else [],
                            "failed": list(self._failed_patterns.keys()),
                            "recovery_attempts": len(self._failed_patterns)
                        },
                        "storage": {
                            "path": str(pattern_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )
            elif self._pattern_status == ProcessStatus.PAUSED:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Pattern system paused",
                    details={
                        "patterns": {
                            "total": len(self._patterns or {}),
                            "loaded": list(self._patterns.keys()) if self._patterns else [],
                            "failed": list(self._failed_patterns.keys()),
                            "recovery_attempts": len(self._failed_patterns)
                        },
                        "storage": {
                            "path": str(pattern_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            # Check if any critical components are missing
            if not (patterns_loaded and dir_exists and dir_writable):
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Pattern system partially operational",
                    details={
                        "patterns": {
                            "total": len(self._patterns or {}),
                            "loaded": list(self._patterns.keys()) if self._patterns else [],
                            "failed": list(self._failed_patterns.keys()),
                            "recovery_attempts": len(self._failed_patterns)
                        },
                        "storage": {
                            "path": str(pattern_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            return ComponentHealth(
                status=HealthStatus.OK,
                error=None,
                details={
                    "patterns": {
                        "total": len(self._patterns or {}),
                        "loaded": list(self._patterns.keys()) if self._patterns else [],
                        "failed": list(self._failed_patterns.keys()),
                        "recovery_attempts": len(self._failed_patterns)
                    },
                    "storage": {
                        "path": str(pattern_dir),
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

    async def _load_patterns(self) -> None:
        """Load patterns from configuration."""
        try:
            # Load service config
            config_path = os.path.join("backend", "config", "process.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "pattern" in config:
                        self._version = config["pattern"].get("version", self._version)
            
            # Load pattern files from data directory
            pattern_dir = Path("backend/data/patterns")
            if pattern_dir.exists():
                for file_path in pattern_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            pattern_data = json.load(f)
                            pattern_id = file_path.stem
                            # Convert the loaded JSON data into a Pattern model
                            self._patterns[pattern_id] = {
                                "id": pattern_id,
                                "name": pattern_data["pattern"]["name"],
                                "description": pattern_data["pattern"]["description"],
                                "type": pattern_data["pattern"]["type"],
                                "params": pattern_data["pattern"]["params"]
                            }
                            logger.info(f"Loaded pattern file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load pattern file {file_path.name}: {str(e)}")
                        self._failed_patterns[file_path.stem] = str(e)
            
            logger.info(f"Loaded {len(self._patterns)} patterns")
            
        except Exception as e:
            error_msg = f"Failed to load patterns: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_pattern(self, pattern_id: str) -> Pattern:
        """Get pattern by ID.
        
        Args:
            pattern_id: Pattern ID
            
        Returns:
            Pattern object
            
        Raises:
            HTTPException if pattern not found or service not running
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
                
            if pattern_id not in self._patterns:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Pattern {pattern_id} not found"
                )
                
            pattern_data = self._patterns[pattern_id]
            return Pattern(
                id=pattern_id,
                name=pattern_data["name"],
                description=pattern_data["description"],
                type=pattern_data["type"],
                params=pattern_data["params"]
            )
            
        except Exception as e:
            error_msg = f"Failed to get pattern {pattern_id}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
            
    async def list_patterns(self) -> List[Pattern]:
        """List all available patterns.
        
        Returns:
            List of Pattern objects
            
        Raises:
            HTTPException if service not running
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
                
            patterns = []
            for pattern_id, pattern_data in self._patterns.items():
                pattern = Pattern(
                    id=pattern_id,
                    name=pattern_data["name"],
                    description=pattern_data["description"],
                    type=pattern_data["type"],
                    params=pattern_data["params"]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            error_msg = f"Failed to list patterns: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
