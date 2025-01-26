"""Sequence Service

This module implements the Sequence service for managing process sequences.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from fastapi import status
from loguru import logger
import json

from mcs.utils.errors import create_error
from mcs.utils.health import HealthStatus, ComponentHealth
from mcs.api.process.models.process_models import (
    ProcessStatus,
    Sequence,
    SequenceMetadata,
    SequenceStep,
    SequenceResponse
)


class SequenceService:
    """Service for managing process sequences."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize sequence service.
        
        Args:
            config: Service configuration
        """
        # Basic properties
        self._service_name = "sequence"
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._is_initialized = False
        self._is_prepared = False
        self._start_time = None
        
        # Paths
        self._data_path = None
        self._schema_path = None
        self._sequence_dir = None
        
        # State
        self._sequences = {}
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
            
            # Get paths from config
            self._data_path = Path(self._config["paths"]["data"])
            self._schema_path = Path(self._config["paths"]["schemas"])
            
            # Set component directories - use data path directly since it already points to the sequences folder
            self._sequence_dir = self._data_path
            
            # Validate paths
            if not self._sequence_dir.exists():
                self._sequence_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created sequence directory: {self._sequence_dir}")
            
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
            self._sequences = {}
            self._failed_sequences = {}
            self._active_sequence = None
            self._sequence_status = ProcessStatus.IDLE

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

            # Load sequences
            await self._load_sequences()

            self._is_running = True
            self._start_time = datetime.now()
            self._sequence_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._sequence_status = ProcessStatus.ERROR
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
            self._sequence_status = ProcessStatus.IDLE
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
            self._sequences = {}
            self._failed_sequences = {}
            self._active_sequence = None
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
            "sequences_loaded": len(self._sequences),
            "failed_sequences": len(self._failed_sequences),
            "active_sequence": self._active_sequence,
            "sequence_status": self._sequence_status
        }
        return ComponentHealth(
            name=self.service_name,
            status=status,
            details=details
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
            # Load sequence files from data directory
            if self._sequence_dir.exists():
                for file_path in self._sequence_dir.glob("*.json"):
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
            sequence_id: Sequence ID
            
        Returns:
            Sequence data
            
        Raises:
            HTTPException: If sequence not found or service not running
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
                    message=f'Sequence "{sequence_id}" not found'
                )
                
            sequence_data = self._sequences[sequence_id]
            if "sequence" not in sequence_data:
                sequence_data = {"sequence": sequence_data}
                
            # First create the metadata object
            metadata = SequenceMetadata(
                name=sequence_data["sequence"]["metadata"]["name"],
                version=sequence_data["sequence"]["metadata"]["version"],
                created=sequence_data["sequence"]["metadata"]["created"],
                author=sequence_data["sequence"]["metadata"]["author"],
                description=sequence_data["sequence"]["metadata"]["description"]
            )
            
            # Create list of sequence steps
            steps = [SequenceStep(**step) for step in sequence_data["sequence"]["steps"]]
            
            # Create the sequence object
            sequence = Sequence(
                id=sequence_id,
                metadata=metadata,
                steps=steps
            )
            
            # Create and return the response
            response = SequenceResponse(sequence=sequence)
            return response
            
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
