"""Sequence service implementation."""

import yaml
from typing import List
from datetime import datetime
from fastapi import status
from loguru import logger
from pathlib import Path
import os

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.process.models.process_models import (
    Sequence,
    StatusType
)


class SequenceService:
    """Service for managing process sequences."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize sequence service."""
        self._service_name = "sequence"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._sequences = None
        self._failed_sequences = {}
        self._active_sequence = None
        self._sequence_status = StatusType.IDLE
        
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
            
            # Initialize sequences
            self._sequences = {}
            
            # Load sequences from config
            await self._load_sequences()
            
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_sequences(self) -> None:
        """Load sequences from files."""
        try:
            sequence_dir = Path("data/sequences")
            if not sequence_dir.exists():
                return
            
            for sequence_file in sequence_dir.glob("*.yaml"):
                try:
                    with open(sequence_file, "r") as f:
                        data = yaml.safe_load(f)
                    
                    if "sequence" not in data:
                        logger.error(f"Missing 'sequence' root key in {sequence_file}")
                        continue
                    
                    sequence_data = data["sequence"]
                    sequence = Sequence(**sequence_data)
                    self._sequences[sequence.metadata.name] = sequence
                    logger.info(f"Loaded sequence: {sequence.metadata.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to load sequence {sequence_file}: {e}")
                    self._failed_sequences[sequence_file.stem] = str(e)
                    continue
                
        except Exception as e:
            logger.error(f"Failed to load sequences: {e}")

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed sequences."""
        if self._failed_sequences:
            logger.info(f"Attempting to recover {len(self._failed_sequences)} failed sequences...")
            await self._load_sequences()

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Set service as running
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
            
            # 1. Stop active sequences
            if self._active_sequence:
                await self.stop_sequence(self._active_sequence)
            
            # 2. Clear sequence data
            self._sequences.clear()
            self._active_sequence = None
            self._sequence_status = StatusType.IDLE
            
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

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Check critical components
            sequences_loaded = self._sequences is not None and len(self._sequences) > 0
            sequence_dir = Path("data/sequences")
            dir_exists = sequence_dir.exists()
            dir_writable = dir_exists and os.access(sequence_dir, os.W_OK)
            
            # Build component status focusing on critical components
            components = {
                "sequences": ComponentHealth(
                    status=HealthStatus.OK if sequences_loaded and dir_exists and dir_writable else HealthStatus.ERROR,
                    error=None if sequences_loaded and dir_exists and dir_writable else "Sequence system not operational",
                    details={
                        "total_sequences": len(self._sequences or {}),
                        "loaded_sequences": list(self._sequences.keys()) if self._sequences else [],
                        "failed_sequences": list(self._failed_sequences.keys()),
                        "recovery_attempts": len(self._failed_sequences),
                        "directory": {
                            "path": str(sequence_dir),
                            "exists": dir_exists,
                            "writable": dir_writable
                        },
                        "execution": {
                            "active_sequence": self._active_sequence,
                            "status": self._sequence_status.value if self._sequence_status else None
                        }
                    }
                )
            }
            
            # Overall status is ERROR if sequence system is not operational
            # or if active sequence is in error state
            overall_status = HealthStatus.ERROR if (
                not (sequences_loaded and dir_exists and dir_writable)
                or self._sequence_status == StatusType.ERROR  # noqa: W503
            ) else HealthStatus.OK

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error="Critical component failure" if overall_status == HealthStatus.ERROR else None,
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg)

    async def list_sequences(self) -> List[Sequence]:
        """List available sequences.
        
        Returns:
            List[Sequence]: List of sequences
            
        Raises:
            HTTPException: If service not running or listing fails
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
            
            sequences = list(self._sequences.values())
            logger.info(f"Retrieved {len(sequences)} sequences")
            return sequences
            
        except Exception as e:
            error_msg = "Failed to list sequences"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def get_sequence(self, sequence_id: str) -> Sequence:
        """Get sequence by ID.
        
        Args:
            sequence_id: Sequence identifier
            
        Returns:
            Sequence: Sequence if found
            
        Raises:
            HTTPException: If service not running or sequence not found
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if sequence_id not in self._sequences:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Sequence {sequence_id} not found"
                )
                
            return self._sequences[sequence_id]
            
        except Exception as e:
            error_msg = f"Failed to get sequence {sequence_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start_sequence(self, sequence_id: str) -> None:
        """Start sequence execution."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            # Case-insensitive lookup
            sequence_id = sequence_id.lower().replace("-", "_")
            sequence = None
            for seq in self._sequences.values():
                if seq.metadata.name.lower().replace(" ", "_") == sequence_id:
                    sequence = seq
                    break
                
            if not sequence:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Sequence {sequence_id} not found"
                )
                
            # Check if already running
            if sequence_id in self._running_sequences:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"Sequence {sequence_id} already running"
                )
                
            # Start sequence execution
            self._running_sequences[sequence_id] = {
                "sequence": sequence,
                "status": StatusType.RUNNING,
                "current_step": 0,
                "start_time": datetime.now()
            }
            
            logger.info(f"Started sequence {sequence_id}")
            
        except Exception as e:
            error_msg = f"Failed to start sequence {sequence_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop_sequence(self, sequence_id: str) -> StatusType:
        """Stop sequence execution."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if not self._active_sequence:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No sequence in progress"
                )
                
            if sequence_id != self._active_sequence:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Sequence {sequence_id} not in progress"
                )
                
            self._active_sequence = None
            self._sequence_status = StatusType.IDLE
            logger.info(f"Stopped sequence {sequence_id}")
            
            return self._sequence_status
            
        except Exception as e:
            error_msg = f"Failed to stop sequence {sequence_id}"
            logger.error(f"{error_msg}: {str(e)}")
            self._sequence_status = StatusType.ERROR
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def get_sequence_status(self, sequence_id: str) -> StatusType:
        """Get sequence execution status."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Service not running"
                )
                
            if not self._active_sequence:
                return StatusType.IDLE
                
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
