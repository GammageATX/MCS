"""Sequence Service

This module implements the Sequence service for managing process sequences.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import json
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import (  # Noqa: F401
    HealthStatus,
    ComponentHealth,
    create_error_health  # Noqa: F401
)
from mcs.api.process.models.process_models import (
    ProcessStatus,
    Sequence,
    SequenceMetadata,
    SequenceStep,
    SequenceResponse
)


class SequenceService:
    """Service for managing process sequences."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize sequence service.
        
        Args:
            config: Service configuration
        """
        self._service_name = "sequence"
        self._version = config.get("version", "1.0.0")  # Get version from top level
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        
        # Initialize components
        self._sequences = {}  # Initialize as empty dict
        self._failed_sequences = {}
        self._active_sequence = None
        self._sequence_status = ProcessStatus.IDLE
        
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
            
            # Initialize sequences
            self._sequences = {}
            
            # Load sequences from config
            await self._load_sequences()
            
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
            
            logger.info(f"Starting {self.service_name} service...")
            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.service_name} service started successfully")
            
        except Exception as e:
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
            self._sequence_status = ProcessStatus.IDLE
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
            sequences_loaded = self._sequences is not None and len(self._sequences) > 0
            sequence_dir = Path("backend/data/sequences")
            dir_exists = sequence_dir.exists()
            dir_writable = dir_exists and os.access(sequence_dir, os.W_OK)

            # Map process status to health status
            if self._sequence_status == ProcessStatus.ERROR:
                return ComponentHealth(
                    status=HealthStatus.ERROR,
                    error="Sequence system in error state",
                    details={
                        "sequences": {
                            "total": len(self._sequences or {}),
                            "loaded": list(self._sequences.keys()) if self._sequences else [],
                            "failed": list(self._failed_sequences.keys()),
                            "recovery_attempts": len(self._failed_sequences)
                        },
                        "execution": {
                            "active_sequence": self._active_sequence,
                            "status": self._sequence_status.value
                        },
                        "storage": {
                            "path": str(sequence_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )
            elif self._sequence_status == ProcessStatus.PAUSED:
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Sequence system paused",
                    details={
                        "sequences": {
                            "total": len(self._sequences or {}),
                            "loaded": list(self._sequences.keys()) if self._sequences else [],
                            "failed": list(self._failed_sequences.keys()),
                            "recovery_attempts": len(self._failed_sequences)
                        },
                        "execution": {
                            "active_sequence": self._active_sequence,
                            "status": self._sequence_status.value
                        },
                        "storage": {
                            "path": str(sequence_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            # Check if any critical components are missing
            if not (sequences_loaded and dir_exists and dir_writable):
                return ComponentHealth(
                    status=HealthStatus.DEGRADED,
                    error="Sequence system partially operational",
                    details={
                        "sequences": {
                            "total": len(self._sequences or {}),
                            "loaded": list(self._sequences.keys()) if self._sequences else [],
                            "failed": list(self._failed_sequences.keys()),
                            "recovery_attempts": len(self._failed_sequences)
                        },
                        "execution": {
                            "active_sequence": self._active_sequence,
                            "status": self._sequence_status.value
                        },
                        "storage": {
                            "path": str(sequence_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        }
                    }
                )

            return ComponentHealth(
                status=HealthStatus.OK,
                error=None,
                details={
                    "sequences": {
                        "total": len(self._sequences or {}),
                        "loaded": list(self._sequences.keys()) if self._sequences else [],
                        "failed": list(self._failed_sequences.keys()),
                        "recovery_attempts": len(self._failed_sequences)
                    },
                    "execution": {
                        "active_sequence": self._active_sequence,
                        "status": self._sequence_status.value
                    },
                    "storage": {
                        "path": str(sequence_dir),
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

    async def get_sequence_status(self, sequence_id: str) -> ProcessStatus:
        """Get sequence execution status."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if not self._active_sequence:
                return ProcessStatus.IDLE
                
            if sequence_id != self._active_sequence:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Sequence {sequence_id} not found"
                )
                
            return self._sequence_status
            
        except Exception as e:
            error_msg = f"Failed to get status for sequence {sequence_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_sequences(self) -> None:
        """Load sequences from configuration."""
        try:
            # Load service config
            config_path = os.path.join("backend", "config", "process.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "sequence" in config:
                        self._version = config["sequence"].get("version", self._version)
            
            # Load sequence files from data directory
            sequence_dir = Path("backend/data/sequences")
            if sequence_dir.exists():
                for file_path in sequence_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            sequence_data = json.load(f)
                            sequence_id = file_path.stem
                            # Validate sequence data structure
                            if "sequence" not in sequence_data:
                                sequence_data = {"sequence": sequence_data}
                            self._sequences[sequence_id] = sequence_data
                            logger.info(f"Loaded sequence file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load sequence file {file_path.name}: {str(e)}")
                        self._failed_sequences[file_path.stem] = str(e)
            
            logger.info(f"Loaded {len(self._sequences)} sequences")
            
        except Exception as e:
            error_msg = f"Failed to load sequences: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def list_sequences(self) -> List[str]:
        """List available sequences.
        
        Returns:
            List of sequence IDs
            
        Raises:
            HTTPException if service not running
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
                
            # Just return the list of sequence IDs
            return list(self._sequences.keys())
            
        except Exception as e:
            error_msg = f"Failed to list sequences: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_sequence(self, sequence_id: str) -> SequenceResponse:
        """Get sequence by ID.
        
        Args:
            sequence_id: Sequence identifier
            
        Returns:
            SequenceResponse: Sequence response containing sequence data
            
        Raises:
            HTTPException: If sequence not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
            
            if sequence_id not in self._sequences:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Sequence {sequence_id} not found"
                )
                
            sequence_data = self._sequences[sequence_id]["sequence"]
            # Convert the loaded JSON data into a Sequence model
            sequence = Sequence(
                id=sequence_id,
                metadata=SequenceMetadata(
                    name=sequence_data["metadata"]["name"],
                    version=sequence_data["metadata"]["version"],
                    created=sequence_data["metadata"]["created"],
                    author=sequence_data["metadata"]["author"],
                    description=sequence_data["metadata"]["description"]
                ),
                steps=[SequenceStep(**step) for step in sequence_data["steps"]]
            )
            return SequenceResponse(sequence=sequence)
            
        except KeyError as e:
            logger.error(f"Invalid sequence data structure for {sequence_id}: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Invalid sequence data structure: missing {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to get sequence {sequence_id}: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to get sequence: {str(e)}"
            )
