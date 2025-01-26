"""Schema Service

This module implements the Schema service for managing process schemas.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import status
from loguru import logger
import json

from mcs.utils.errors import create_error
from mcs.utils.health import HealthStatus, ComponentHealth
from mcs.api.process.models.process_models import ProcessStatus


class SchemaService:
    """Service for managing process schemas."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize schema service.
        
        Args:
            config: Service configuration
        """
        # Basic properties
        self._service_name = "schema"
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
        self._schemas = {}
        self._failed_schemas = {}
        self._schema_status = ProcessStatus.IDLE
        
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
            
            # Get schema path from config
            self._schema_path = Path(self._config["paths"]["schemas"])
            
            # Validate paths
            if not self._schema_path.exists():
                self._schema_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created schema directory: {self._schema_path}")
            
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
            self._schemas = {}
            self._failed_schemas = {}
            self._schema_status = ProcessStatus.IDLE

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

            # Load schemas
            await self._load_schemas()

            self._is_running = True
            self._start_time = datetime.now()
            self._schema_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._schema_status = ProcessStatus.ERROR
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
            self._schema_status = ProcessStatus.IDLE
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
            self._schemas = {}
            self._failed_schemas = {}
            logger.info(f"{self.service_name} service shut down")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    def health(self) -> ComponentHealth:
        """Get service health."""
        status = HealthStatus.OK if self.is_running else HealthStatus.ERROR
        details = {
            "version": self._version,
            "uptime": self.uptime,
            "status": status,
            "initialized": self.is_initialized,
            "prepared": self.is_prepared,
            "schemas_loaded": len(self._schemas),
            "failed_schemas": len(self._failed_schemas),
            "schema_status": self._schema_status
        }
        return ComponentHealth(
            name=self.service_name,
            status=status,
            details=details
        )

    async def _load_schemas(self) -> None:
        """Load schema definitions."""
        try:
            self._schemas = {}
            
            # Load schemas from JSON files
            schema_types = ["nozzle", "pattern", "parameter", "powder", "sequence"]
            
            for schema_type in schema_types:
                schema_file = self._schema_path / f"{schema_type}.json"
                if schema_file.exists():
                    try:
                        with open(schema_file, "r") as f:
                            self._schemas[schema_type] = json.load(f)
                            logger.info(f"Loaded {schema_type} schema from {schema_file}")
                    except Exception as e:
                        logger.error(f"Failed to load {schema_type} schema: {str(e)}")
                        self._failed_schemas[schema_type] = str(e)
                else:
                    logger.warning(f"Schema file not found: {schema_file}")
            
            logger.info(f"Loaded {len(self._schemas)} schema definitions")
            
        except Exception as e:
            error_msg = f"Failed to load schemas: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_schema(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get JSON Schema for entity type.
        
        Args:
            entity_type: Type of entity (pattern, parameter, nozzle, powder, sequence)
            
        Returns:
            JSON Schema definition or None if not found
            
        Raises:
            HTTPException: If service not running or schema not found
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if entity_type not in self._schemas:
                return None

            return self._schemas[entity_type]

        except Exception as e:
            error_msg = f"Failed to get schema for {entity_type}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
