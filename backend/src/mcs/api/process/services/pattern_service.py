"""Pattern Service

This module implements the Pattern service for managing process patterns.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import status
from loguru import logger
import json

from mcs.api.process.models import ProcessStatus
from mcs.api.process.validators import validate_pattern
from mcs.utils.errors import create_error
from mcs.utils.health import HealthStatus, ComponentHealth
from mcs.api.process.models.process_models import Pattern


class PatternService:
    """Service for managing process patterns."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize pattern service.
        
        Args:
            config: Service configuration
        """
        # Basic properties
        self._service_name = "pattern"
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._is_initialized = False
        self._is_prepared = False
        self._start_time = None
        
        # Paths
        self._data_path = None
        self._schema_path = None
        
        # State
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
            
            # Validate paths
            if not self._data_path.exists():
                self._data_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created pattern data directory: {self._data_path}")
                
            if not self._schema_path.exists():
                self._schema_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created pattern schema directory: {self._schema_path}")
            
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
            self._patterns = {}
            self._failed_patterns = {}
            self._pattern_status = ProcessStatus.IDLE

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

            # Load patterns
            await self._load_patterns()

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

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        try:
            if self.is_running:
                await self.stop()
                
            self._is_initialized = False
            self._is_prepared = False
            self._patterns = {}
            self._failed_patterns = {}
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
            "patterns_loaded": len(self._patterns),
            "failed_patterns": len(self._failed_patterns),
            "pattern_status": self._pattern_status
        }
        return ComponentHealth(
            name=self.service_name,
            status=status,
            details=details
        )

    async def _load_patterns(self) -> None:
        """Load patterns from files."""
        try:
            logger.debug(f"Loading patterns from {self._data_path}")
            if not self._data_path.exists():
                logger.error(f"Pattern directory not found: {self._data_path}")
                return

            pattern_files = [f for f in self._data_path.glob("*.json")]
            logger.debug(f"Found pattern files: {pattern_files}")

            for file_path in pattern_files:
                try:
                    logger.debug(f"Loading pattern from {file_path}")
                    
                    with open(file_path) as f:
                        pattern_data = json.load(f)
                        
                    logger.debug(f"Pattern data loaded: {pattern_data}")
                    
                    # Validate pattern data
                    try:
                        validated_data = validate_pattern(pattern_data)
                        pattern_data = validated_data.get("pattern", pattern_data)
                    except Exception as e:
                        logger.error(f"Invalid pattern data in {file_path.name}: {str(e)}")
                        self._failed_patterns[file_path.stem] = f"Validation failed: {str(e)}"
                        continue
                    
                    pattern_id = pattern_data.get("id", file_path.stem)
                    self._patterns[pattern_id] = pattern_data
                    logger.info(f"Loaded pattern file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to load pattern file {file_path.name}: {str(e)}")
                    self._failed_patterns[file_path.stem] = str(e)
                    continue

            logger.info(f"Loaded {len(self._patterns)} patterns")
            logger.debug(f"Pattern IDs: {list(self._patterns.keys())}")
            
        except Exception as e:
            error_msg = f"Failed to load patterns: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
            
    async def list_patterns(self) -> List[str]:
        """List all available patterns.
        
        Returns:
            List of pattern IDs
            
        Raises:
            HTTPException if service not running
        """
        try:
            logger.debug(f"Pattern service list_patterns called. Running: {self.is_running}")
            
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
            
            logger.debug(f"Number of patterns loaded: {len(self._patterns)}")
            pattern_ids = list(self._patterns.keys())
            logger.debug(f"Pattern IDs: {pattern_ids}")
            return pattern_ids
            
        except Exception as e:
            error_msg = f"Failed to list patterns: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
