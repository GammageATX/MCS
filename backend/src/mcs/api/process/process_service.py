"""Process Service

This module implements the Process service for managing process execution and control.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastapi import status
from loguru import logger
import json

from mcs.utils.errors import create_error
from mcs.utils.health import (  # Noqa: F401
    HealthStatus,
    ServiceHealth,
    ComponentHealth,
    create_error_health,
    create_simple_health
)
from mcs.api.process.services.action_service import ActionService
from mcs.api.process.services.parameter_service import ParameterService
from mcs.api.process.services.pattern_service import PatternService
from mcs.api.process.services.sequence_service import SequenceService
from mcs.api.process.services.schema_service import SchemaService
from mcs.api.process.models.process_models import ProcessStatus


class ProcessService:
    """Process service for managing process execution and control.
    
    The Process service is responsible for:
    - Managing process parameters and configurations
    - Executing process sequences and patterns
    - Coordinating hardware control during processing
    - Monitoring process state and health
    
    Lifecycle:
    1. __init__: Set basic properties
    2. initialize: Create and initialize components
    3. prepare: Handle operations requiring running dependencies
    4. start: Begin service operations
    5. shutdown: Clean shutdown of service
    """

    def __init__(self, version: str = "1.0.0") -> None:
        """Initialize process service.
        
        Args:
            version: Service version
        """
        self._version = version
        self._service_name = "process"
        self._is_initialized = False
        self._is_running = False
        self._is_prepared = False
        self._start_time = None
        
        # Default paths
        self._paths = {
            "config": Path("backend/config"),
            "data": Path("backend/data"),
            "schemas": Path("backend/schemas")
        }
        
        # Component services
        self.action_service = None
        self.parameter_service = None
        self.pattern_service = None
        self.sequence_service = None
        self.schema_service = None
        
        # Component states
        self._components = {}
        self._health = {}
        self._process_status = ProcessStatus.IDLE
        
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
        """Initialize service and components."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Load config
            config_path = self._paths["config"] / "process.json"
            if not config_path.exists():
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"Config file not found: {config_path}"
                )

            with open(config_path) as f:
                config = json.load(f)

            # Update paths from config
            if "paths" in config:
                for key, path in config["paths"].items():
                    if key in self._paths:
                        self._paths[key] = Path(path)

            # Initialize component services with config
            component_classes = {
                "action": ActionService,
                "parameter": ParameterService,
                "pattern": PatternService,
                "sequence": SequenceService,
                "schema": SchemaService
            }
            
            # Initialize all components with config sections
            for name, component_class in component_classes.items():
                logger.info(f"Initializing {name} component...")
                component_config = config.get("components", {}).get(name, {}).copy()  # Make a copy to avoid modifying original
                component_config["version"] = self.version
                
                # Set paths based on component type
                if name == "action":
                    # Action service uses config directly - no paths needed
                    component = component_class(config=component_config)
                elif name == "parameter":
                    # Parameter service needs access to parameters, nozzles, and powders
                    component_config["paths"] = {
                        "data": self._paths["data"],  # Root data path
                        "parameters": self._paths["data"] / "parameters",
                        "nozzles": self._paths["data"] / "nozzles",
                        "powders": self._paths["data"] / "powders",
                        "schemas": Path("backend/schemas/process")
                    }
                    component = component_class(config=component_config)
                elif name == "schema":
                    # Schema service only needs schema path
                    component_config["paths"] = {
                        "schemas": Path("backend/schemas/process")
                    }
                    component = component_class(config=component_config)
                else:
                    # Pattern and sequence services use their respective data folders
                    component_config["paths"] = {
                        "data": self._paths["data"] / f"{name}s",  # patterns or sequences
                        "schemas": Path("backend/schemas/process")
                    }
                    component = component_class(config=component_config)
                
                self._components[name] = component
                await component.initialize()
                logger.info(f"Initialized {name} component")
            
            # Store component references
            self.action_service = self._components["action"]
            self.parameter_service = self._components["parameter"]
            self.pattern_service = self._components["pattern"]
            self.sequence_service = self._components["sequence"]
            self.schema_service = self._components["schema"]

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

            # Prepare components in dependency order
            for name, component in self._components.items():
                if hasattr(component, "prepare"):
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
        """Start service and components."""
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

            # Start components in dependency order
            for name, component in self._components.items():
                logger.info(f"Starting {name} component...")
                await component.start()
                logger.info(f"Started {name} component")

            self._is_running = True
            self._start_time = datetime.now()
            self._process_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._process_status = ProcessStatus.ERROR
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

            # Stop components in reverse dependency order
            for name, component in reversed(list(self._components.items())):
                try:
                    if hasattr(component, "stop"):
                        logger.info(f"Stopping {name} component...")
                        await component.stop()
                        logger.info(f"Stopped {name} component")
                except Exception as e:
                    logger.error(f"Error stopping {name} component: {str(e)}")
                    
            self._is_running = False
            self._start_time = None
            self._process_status = ProcessStatus.IDLE
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
            
            # Cleanup components in reverse dependency order
            for name, component in reversed(list(self._components.items())):
                try:
                    if hasattr(component, "shutdown"):
                        logger.info(f"Shutting down {name} component...")
                        await component.shutdown()
                        logger.info(f"Shut down {name} component")
                except Exception as e:
                    logger.error(f"Error shutting down {name} component: {str(e)}")
            
            self._is_initialized = False
            self._is_prepared = False
            self._components = {}
            logger.info(f"{self.service_name} service shut down successfully")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_config(self) -> Dict[str, Any]:
        """Load process configuration."""
        try:
            config_file = self._paths["config"] / "process.json"
            if not config_file.exists():
                raise FileNotFoundError(f"Process configuration file not found: {config_file}")

            with open(config_file) as f:
                return json.load(f)

        except Exception as e:
            error_msg = f"Failed to load process configuration: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get service health."""
        try:
            # Get component health
            component_health = {}
            for name, component in self._components.items():
                try:
                    component_health[name] = await component.health()
                except Exception as e:
                    logger.error(f"Component health check failed - {name}: {str(e)}")
                    component_health[name] = ComponentHealth(
                        name=name,
                        status=HealthStatus.ERROR,
                        details={"error": str(e)}
                    )

            # Determine overall status
            status = HealthStatus.OK if self.is_running else HealthStatus.ERROR
            if status == HealthStatus.OK:
                for health in component_health.values():
                    if health.status != HealthStatus.OK:
                        status = HealthStatus.ERROR
                        break

            # Build health details
            details = {
                "version": self._version,
                "uptime": self.uptime,
                "status": status,
                "initialized": self.is_initialized,
                "prepared": self.is_prepared,
                "components": component_health
            }

            return ServiceHealth(
                name=self.service_name,
                status=status,
                details=details
            )

        except Exception as e:
            error_msg = f"Failed to get service health: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )
