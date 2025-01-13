"""Process Service

This module implements the Process service for managing process execution and control.
"""

import os
from typing import Dict, Any
from datetime import datetime
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

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize process service.
        
        Args:
            config: Service configuration dictionary
        """
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._service_name = "process"
        self._is_initialized = False
        self._is_running = False
        self._is_prepared = False
        self._components = {}
        
        logger.info(f"{self.service_name} service initialized")

        # Default paths
        self.config_path = os.path.join("backend", "config")
        self.schema_path = os.path.join("backend", "schema")
        
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

            # Initialize component services with their respective configs
            self.action_service = ActionService(version=self.version)  # ActionService still uses version
            self.parameter_service = ParameterService(config=self._config)  # Pass full config
            self.pattern_service = PatternService(config=self._config)  # Pass full config
            self.sequence_service = SequenceService(config=self._config)  # Pass full config
            self.schema_service = SchemaService(version=self.version)  # SchemaService still uses version
            
            # Store components for health checks
            self._components = {
                "action": self.action_service,
                "parameter": self.parameter_service,
                "pattern": self.pattern_service,
                "sequence": self.sequence_service,
                "schema": self.schema_service
            }
            
            # Initialize all components
            for name, component in self._components.items():
                logger.info(f"Initializing {name} component...")
                await component.initialize()
                logger.info(f"Initialized {name} component")

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
            config_file = os.path.join(self.config_path, "process.json")
            if not os.path.exists(config_file):
                raise FileNotFoundError(f"Process configuration file not found: {config_file}")

            with open(config_file, "r") as f:
                return json.load(f)

        except Exception as e:
            error_msg = f"Failed to load process configuration: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get service health status.
        
        Returns:
            ServiceHealth: Service health status including component health
        """
        try:
            if not self.is_running:
                return create_error_health(
                    service_name=self.service_name,
                    version=self.version,
                    error_msg=f"{self.service_name} not running"
                )

            components = {}
            overall_status = HealthStatus.OK

            # Check critical components
            for name, component in self._components.items():
                try:
                    if hasattr(component, "health"):
                        health = await component.health()
                        components[name] = health
                        if health.status != HealthStatus.OK:
                            overall_status = HealthStatus.ERROR
                    else:
                        status = HealthStatus.OK if component.is_running else HealthStatus.ERROR
                        components[name] = ComponentHealth(
                            status=status,
                            error=None if status == HealthStatus.OK else "Component not running"
                        )
                        if status != HealthStatus.OK:
                            overall_status = HealthStatus.ERROR
                except Exception as e:
                    logger.error(f"Component health check failed - {name}: {str(e)}")
                    components[name] = ComponentHealth(
                        status=HealthStatus.ERROR,
                        error=str(e)
                    )
                    overall_status = HealthStatus.ERROR

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None,  # No need to aggregate component errors here
                components=components
            )

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return create_error_health(
                service_name=self.service_name,
                version=self.version,
                error_msg=str(e)
            )
