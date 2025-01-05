"""Schema service implementation."""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import status
from loguru import logger
import jsonschema

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health


class SchemaService:
    """Schema service."""

    def __init__(self, schema_path: str = os.path.join("backend", "config", "schemas"), version: str = "1.0.0"):
        """Initialize service.
        
        Args:
            schema_path: Path to schema directory
            version: Service version
        """
        self._service_name = "schema"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components
        self._schema_path = schema_path
        self._schemas = None
        self._failed_schemas = {}  # Track failed schema loads
        
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
            # Verify schema directory exists
            if not os.path.exists(self._schema_path):
                error_msg = f"Schema directory does not exist: {self._schema_path}"
                logger.error(error_msg)
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=error_msg
                )
            
            logger.info(f"Using schema path: {self._schema_path}")
            
            # Load schemas from files
            self._schemas = {}
            await self._load_schemas()
            
            logger.info(f"Loaded {len(self._schemas)} schemas")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_schemas(self) -> None:
        """Load schemas from files."""
        for filename in os.listdir(self._schema_path):
            if filename.endswith(('.json', '.yaml', '.yml')):
                schema_name = os.path.splitext(filename)[0]
                schema_path = os.path.join(self._schema_path, filename)
                try:
                    with open(schema_path, 'r') as f:
                        schema_data = json.load(f)
                        # Ensure schema is a valid JSON Schema
                        jsonschema.validators.Draft7Validator.check_schema(schema_data)
                        self._schemas[schema_name] = schema_data
                    # If schema was previously failed, remove from failed list
                    self._failed_schemas.pop(schema_name, None)
                except Exception as e:
                    logger.error(f"Failed to load schema {schema_name}: {e}")
                    self._failed_schemas[schema_name] = str(e)

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed schemas."""
        if self._failed_schemas:
            logger.info(f"Attempting to recover {len(self._failed_schemas)} failed schemas...")
            await self._load_schemas()

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            if not self._schema_path or self._schemas is None:
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

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Check critical components
            path_exists = os.path.exists(self._schema_path) if self._schema_path else False
            path_writable = os.access(self._schema_path, os.W_OK) if path_exists else False
            schemas_loaded = self._schemas is not None and len(self._schemas) > 0
            
            # Build component status focusing on critical components
            components = {
                "schemas": ComponentHealth(
                    status=HealthStatus.OK if path_exists and path_writable and schemas_loaded else HealthStatus.ERROR,
                    error=None if path_exists and path_writable and schemas_loaded else "Schema system not operational",
                    details={
                        "path": self._schema_path,
                        "path_exists": path_exists,
                        "path_writable": path_writable,
                        "total_schemas": len(self._schemas or {}),
                        "loaded_schemas": list(self._schemas.keys()) if self._schemas else [],
                        "failed_schemas": list(self._failed_schemas.keys()),
                        "recovery_attempts": len(self._failed_schemas)
                    }
                )
            }
            
            # Overall status is ERROR if schema system is not operational
            overall_status = HealthStatus.ERROR if not (path_exists and path_writable and schemas_loaded) else HealthStatus.OK

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

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get schema by name.
        
        Args:
            name: Schema name
            
        Returns:
            Schema definition or None if not found
        """
        return self._schemas.get(name)

    def get_schema_names(self) -> List[str]:
        """Get list of available schema names.
        
        Returns:
            List of schema names
        """
        return list(self._schemas.keys()) if self._schemas else []
