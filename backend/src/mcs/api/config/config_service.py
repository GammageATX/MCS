"""Configuration service."""

import os
import json
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from fastapi import status
from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.config.services.file_service import FileService
from mcs.api.config.services.format_service import FormatService
from mcs.api.config.services.schema_service import SchemaService
import jsonschema


# Default paths - relative to project root
DEFAULT_CONFIG_PATH = os.path.join("backend", "config")
DEFAULT_SCHEMA_PATH = os.path.join(DEFAULT_CONFIG_PATH, "schemas")


class ConfigService:
    """Configuration service.
    
    Lifecycle:
    1. __init__: Set basic properties
    2. initialize: Create and initialize components
    3. prepare: Handle operations requiring running dependencies
    4. start: Begin service operations
    5. shutdown: Clean shutdown of service
    """

    def __init__(self, version: str = "1.0.0"):
        """Initialize service.
        
        Args:
            version: Service version
        """
        self._service_name = "config"
        self._version = version
        self._is_running = False
        self._is_initialized = False
        self._is_prepared = False
        self._start_time = None
        
        # Initialize components to None
        self._config = None
        self._file = None
        self._format = None
        self._schema = None
        
        # Track failed configurations
        self._failed_configs = {}
        
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
    def is_initialized(self) -> bool:
        """Get service initialization state."""
        return self._is_initialized

    @property
    def is_prepared(self) -> bool:
        """Get service preparation state."""
        return self._is_prepared

    @property
    def uptime(self) -> float:
        """Get service uptime."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize service and components."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            logger.info(f"Initializing {self.service_name} service...")
            
            # Load config
            await self._load_config()
            
            # Initialize services with config
            try:
                self._file = FileService(
                    base_path=self._config["components"]["file"]["base_path"],
                    version=self._config["components"]["file"]["version"]
                )
                self._failed_configs.pop("file", None)
            except Exception as e:
                self._failed_configs["file"] = str(e)
                logger.error(f"Failed to initialize file service: {e}")
            
            try:
                self._format = FormatService(
                    enabled_formats=self._config["components"]["format"]["enabled_formats"],
                    version=self._config["components"]["format"]["version"]
                )
                self._failed_configs.pop("format", None)
            except Exception as e:
                self._failed_configs["format"] = str(e)
                logger.error(f"Failed to initialize format service: {e}")
            
            try:
                self._schema = SchemaService(
                    schema_path=self._config["components"]["schema"]["schema_path"],
                    version=self._config["components"]["schema"]["version"]
                )
                self._failed_configs.pop("schema", None)
            except Exception as e:
                self._failed_configs["schema"] = str(e)
                logger.error(f"Failed to initialize schema service: {e}")
            
            # Initialize services in order
            if self._file:
                await self._file.initialize()
            if self._format:
                await self._format.initialize()
            if self._schema:
                await self._schema.initialize()
            
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
        """Prepare service after initialization.
        
        This step handles operations that require running dependencies.
        """
        try:
            if not self.is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            if self.is_prepared:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already prepared"
                )

            # Attempt recovery of any failed configurations
            await self._attempt_recovery()

            # Prepare components in dependency order
            for name, component in [
                ("file", self._file),
                ("format", self._format),
                ("schema", self._schema)
            ]:
                if component and hasattr(component, "prepare"):
                    logger.info(f"Preparing {name} component...")
                    await component.prepare()
                    logger.info(f"Prepared {name} component")

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
        """Start service operations."""
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

            if not self.is_prepared:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not prepared"
                )
            
            # Start services in dependency order
            if self._file:
                await self._file.start()
            if self._format:
                await self._format.start()
            if self._schema:
                await self._schema.start()
            
            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.service_name} service started successfully")
            
        except Exception as e:
            self._is_running = False
            self._start_time = None
            error_msg = f"Failed to start {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _stop(self) -> None:
        """Internal method to stop service operations.
        
        This is called by shutdown() and should not be called directly.
        """
        try:
            if not self.is_running:
                return  # Already stopped

            # Stop services in reverse dependency order
            for name, component in reversed([
                ("schema", self._schema),
                ("format", self._format),
                ("file", self._file)
            ]):
                try:
                    if component and hasattr(component, "stop"):
                        logger.info(f"Stopping {name} component...")
                        await component.stop()
                        logger.info(f"Stopped {name} component")
                except Exception as e:
                    logger.error(f"Error stopping {name} component: {str(e)}")

            self._is_running = False
            self._start_time = None
            logger.info(f"{self.service_name} service stopped")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service stop: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        try:
            # Stop running operations
            await self._stop()
            
            # Clear component references
            self._schema = None
            self._format = None
            self._file = None
            self._config = None
            
            # Reset service state
            self._is_initialized = False
            self._is_prepared = False
            self._failed_configs = {}
            
            logger.info(f"{self.service_name} service shut down successfully")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_config(self) -> None:
        """Load configuration."""
        try:
            config_path = os.path.join("backend", "config", "config.json")
            with open(config_path, "r") as f:
                self._config = json.load(f)
            self._version = self._config["version"]
            logger.info(f"Loaded config version {self._version}")
            self._failed_configs.pop("main", None)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._failed_configs["main"] = str(e)
            self._config = {
                "version": self._version,
                "components": {
                    "file": {
                        "version": "1.0.0",
                        "base_path": os.path.join("backend", "config")
                    },
                    "format": {
                        "version": "1.0.0",
                        "enabled_formats": ["json"]
                    },
                    "schema": {
                        "version": "1.0.0",
                        "schema_path": os.path.join("backend", "config", "schemas")
                    }
                }
            }

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed configurations."""
        if self._failed_configs:
            logger.info(f"Attempting to recover {len(self._failed_configs)} failed configs...")
            
            # Try to reload main config
            if "main" in self._failed_configs:
                await self._load_config()
            
            # Try to reinitialize failed services
            if "file" in self._failed_configs and not self._file:
                try:
                    self._file = FileService(
                        base_path=self._config["components"]["file"]["base_path"],
                        version=self._config["components"]["file"]["version"]
                    )
                    await self._file.initialize()
                    self._failed_configs.pop("file", None)
                except Exception as e:
                    logger.error(f"Failed to recover file service: {e}")
            
            if "format" in self._failed_configs and not self._format:
                try:
                    self._format = FormatService(
                        enabled_formats=self._config["components"]["format"]["enabled_formats"],
                        version=self._config["components"]["format"]["version"]
                    )
                    await self._format.initialize()
                    self._failed_configs.pop("format", None)
                except Exception as e:
                    logger.error(f"Failed to recover format service: {e}")
            
            if "schema" in self._failed_configs and not self._schema:
                try:
                    self._schema = SchemaService(
                        schema_path=self._config["components"]["schema"]["schema_path"],
                        version=self._config["components"]["schema"]["version"]
                    )
                    await self._schema.initialize()
                    self._failed_configs.pop("schema", None)
                except Exception as e:
                    logger.error(f"Failed to recover schema service: {e}")

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Check critical components
            components = {}
            
            # File service (critical for config access)
            if self._file:
                file_health = await self._file.health()
                file_ok = file_health and file_health.status == HealthStatus.OK
                components["file"] = ComponentHealth(
                    status=HealthStatus.OK if file_ok else HealthStatus.ERROR,
                    error=file_health.error if file_health else "File service not initialized",
                    details={
                        "base_path": self._config["components"]["file"]["base_path"],
                        "recovery_attempts": len(self._failed_configs.get("file", []))
                    }
                )
            else:
                components["file"] = ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=self._failed_configs.get("file", "File service not initialized")
                )
            
            # Schema service (critical for validation)
            if self._schema:
                schema_health = await self._schema.health()
                schema_ok = schema_health and schema_health.status == HealthStatus.OK
                components["schema"] = ComponentHealth(
                    status=HealthStatus.OK if schema_ok else HealthStatus.ERROR,
                    error=schema_health.error if schema_health else "Schema service not initialized",
                    details={
                        "schema_path": self._config["components"]["schema"]["schema_path"],
                        "recovery_attempts": len(self._failed_configs.get("schema", []))
                    }
                )
            else:
                components["schema"] = ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=self._failed_configs.get("schema", "Schema service not initialized")
                )
            
            # Format service (critical for parsing)
            if self._format:
                format_health = await self._format.health()
                format_ok = format_health and format_health.status == HealthStatus.OK
                components["format"] = ComponentHealth(
                    status=HealthStatus.OK if format_ok else HealthStatus.ERROR,
                    error=format_health.error if format_health else "Format service not initialized",
                    details={
                        "enabled_formats": self._config["components"]["format"]["enabled_formats"],
                        "recovery_attempts": len(self._failed_configs.get("format", []))
                    }
                )
            else:
                components["format"] = ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=self._failed_configs.get("format", "Format service not initialized")
                )
            
            # Overall status is ERROR if any critical component is in error
            overall_status = HealthStatus.ERROR if any(
                c.status == HealthStatus.ERROR for c in components.values()
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

    async def list_configs(self) -> list:
        """List available configurations."""
        if not self._file or not self._format:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="File or format service not initialized"
            )
        
        try:
            # Get list of files in base directory
            files = os.listdir(self._file._base_path)
            configs = []
            
            # Filter for supported formats
            for file in files:
                name, ext = os.path.splitext(file)
                if ext[1:] in self._format._enabled_formats:
                    configs.append(name)
            
            return configs
            
        except Exception as e:
            error_msg = f"Failed to list configurations: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_config(self, name: str) -> Dict[str, Any]:
        """Get configuration by name."""
        if not self._file or not self._format:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="File or format service not initialized"
            )
        
        try:
            file_path = os.path.join(self._file._base_path, f"{name}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Configuration {name} not found"
            )
            
        except Exception as e:
            error_msg = f"Failed to get configuration {name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def list_schemas(self) -> list:
        """List available schemas."""
        if not self._schema:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Schema service not initialized"
            )
        
        try:
            # Get list of files in schema directory
            files = os.listdir(self._schema._schema_path)
            schemas = []
            
            # Filter for JSON files
            for file in files:
                name, ext = os.path.splitext(file)
                if ext == '.json':
                    schemas.append(name)
            
            return schemas
            
        except Exception as e:
            error_msg = f"Failed to list schemas: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_schema(self, name: str) -> Dict[str, Any]:
        """Get schema by name."""
        if not self._schema:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Schema service not initialized"
            )
        
        try:
            file_path = os.path.join(self._schema._schema_path, f"{name}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Schema {name} not found"
            )
            
        except Exception as e:
            error_msg = f"Failed to get schema {name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def validate_config(self, name: str, data: Dict[str, Any]) -> None:
        """Validate configuration against schema."""
        if not self._schema:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Schema service not initialized"
            )
            
        try:
            # Get schema for config
            schema = self._schema.get_schema(name)
            if not schema:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Schema not found for {name}"
                )
                
            # Validate data against schema
            try:
                validator = jsonschema.validators.Draft7Validator(schema)
                validator.validate(data)
            except jsonschema.exceptions.ValidationError as e:
                raise create_error(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"Validation failed: {str(e)}"
                )
                
        except Exception as e:
            if isinstance(e, create_error):
                raise e
            error_msg = f"Failed to validate config {name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def update_config(self, name: str, data: Dict[str, Any], preserve_format: bool = True) -> None:
        """Update configuration by name."""
        if not self._file or not self._format:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="File or format service not initialized"
            )
        
        try:
            # Write config to file
            file_path = os.path.join(self._file._base_path, f"{name}.json")
            content = await self._format.save_json(data, preserve_format=preserve_format)
            with open(file_path, 'w') as f:
                f.write(content)
            
        except Exception as e:
            error_msg = f"Failed to update config {name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def update_schema(self, name: str, schema_definition: Dict[str, Any]) -> None:
        """Update schema by name.
        
        Args:
            name: Name of schema to update
            schema_definition: Schema definition to save
        """
        if not self._schema:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Schema service not initialized"
            )
            
        try:
            # Validate schema definition is valid JSON Schema
            try:
                jsonschema.Draft7Validator.check_schema(schema_definition)
            except jsonschema.exceptions.SchemaError as e:
                raise create_error(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"Invalid schema definition: {str(e)}"
                )
            
            # Write schema to file
            file_path = os.path.join(self._schema._schema_path, f"{name}.json")
            try:
                with open(file_path, 'w') as f:
                    json.dump(schema_definition, f, indent=2)
            except Exception as e:
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=f"Failed to write schema: {str(e)}"
                )
                
        except Exception as e:
            if isinstance(e, create_error):
                raise e
            error_msg = f"Failed to update schema {name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
