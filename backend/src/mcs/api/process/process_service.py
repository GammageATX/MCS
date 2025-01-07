"""Process Service

This module implements the Process service for managing process execution and control.
"""

import logging
import os
from typing import Dict
from datetime import datetime

import yaml
from fastapi import status

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ServiceHealth,
    ComponentHealth,
    create_error_health
)
from mcs.api.process.services.action_service import ActionService
from mcs.api.process.services.parameter_service import ParameterService
from mcs.api.process.services.pattern_service import PatternService
from mcs.api.process.services.sequence_service import SequenceService
from mcs.api.process.services.schema_service import SchemaService


logger = logging.getLogger(__name__)


class ProcessService:
    """Process service for managing process execution and control.
    
    The Process service is responsible for:
    - Managing process parameters and configurations
    - Executing process sequences and patterns
    - Coordinating hardware control during processing
    - Monitoring process state and health
    """

    def __init__(self, version: str = "1.0.0"):
        """Initialize the Process service.
        
        Args:
            version: Service version string
        """
        self._service_name = "process"
        self._version = version
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        
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
        """Initialize service and components.
        
        This method:
        1. Loads service configuration
        2. Initializes component clients
        3. Sets up health monitoring
        
        Raises:
            HTTPException: If initialization fails
        """
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Load config
            config = self._load_config()
            
            # Initialize components
            await self._initialize_components(config)
            
            # Setup health monitoring
            self._setup_health_monitoring()
            
            self._is_initialized = True
            logger.info("Process service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize process service: {e}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"Failed to initialize process service: {str(e)}"
            )

    async def start(self) -> None:
        """Start service and components.
        
        This method:
        1. Verifies service is initialized
        2. Starts all components in dependency order
        3. Sets service state to running
        
        Raises:
            HTTPException: If start fails
        """
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

            # Start components in dependency order
            for component in self._components.values():
                if hasattr(component, 'start'):
                    await component.start()
            
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
        """Shutdown service and cleanup resources."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )

            # Stop components in reverse dependency order
            for component in reversed(list(self._components.values())):
                if hasattr(component, 'stop'):
                    await component.stop()
                    
            self._is_initialized = False
            self._is_running = False
            self._start_time = None
            logger.info(f"{self.service_name} service stopped successfully")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    def _load_config(self) -> Dict:
        """Load service configuration.
        
        Returns:
            Dict containing service configuration
            
        Raises:
            HTTPException: If config loading fails
        """
        try:
            config_file = os.path.join(self.config_path, "process.yaml")
            
            if not os.path.exists(config_file):
                logger.warning(f"Config file not found at {config_file}, using defaults")
                return {
                    "version": self.version,
                    "service": {
                        "name": "process",
                        "host": "0.0.0.0",
                        "port": 8004,
                        "log_level": "INFO"
                    }
                }
                
            with open(config_file) as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise create_error(
                status_code=500,
                message=f"Failed to load configuration: {str(e)}"
            )

    async def _initialize_components(self, config: Dict) -> None:
        """Initialize service components.
        
        Args:
            config: Service configuration dictionary
            
        Raises:
            HTTPException: If component initialization fails
        """
        try:
            # Initialize component services
            self.action_service = ActionService(version=self.version)
            self.parameter_service = ParameterService(version=self.version)
            self.pattern_service = PatternService(version=self.version)
            self.sequence_service = SequenceService(version=self.version)
            self.schema_service = SchemaService(version=self.version)
            
            # Store components for health monitoring
            self._components = {
                "action": self.action_service,
                "parameter": self.parameter_service,
                "pattern": self.pattern_service,
                "sequence": self.sequence_service,
                "schema": self.schema_service
            }
            
            # Initialize each component
            for name, component in self._components.items():
                logger.info(f"Initializing {name} component...")
                await component.initialize()
                logger.info(f"{name} component initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to initialize components: {str(e)}"
            )

    def _setup_health_monitoring(self) -> None:
        """Setup health monitoring for service and components."""
        # Initialize health state
        self._health = {
            "status": HealthStatus.OK,
            "version": self.version,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {}
        }
        
        # Add component health monitoring
        for name, component in self._components.items():
            self._health["components"][name] = ComponentHealth(
                status=HealthStatus.OK if component.is_running else HealthStatus.STARTING,
                error=None
            )

    async def health(self) -> ServiceHealth:
        """Get service health status.
        
        Returns:
            ServiceHealth: Service health status
        """
        try:
            components = {}
            overall_status = HealthStatus.OK
            error_msg = None

            # Check component health
            for name, component in self._components.items():
                try:
                    if hasattr(component, "health"):
                        health = await component.health()
                        components[name] = health
                        if health.status != HealthStatus.OK:
                            overall_status = HealthStatus.ERROR
                    else:
                        components[name] = ComponentHealth(
                            status=HealthStatus.OK if component.is_running else HealthStatus.ERROR,
                            error="No health check implemented"
                        )
                except Exception as e:
                    error = f"{name} health check failed: {str(e)}"
                    logger.error(error)
                    components[name] = ComponentHealth(
                        status=HealthStatus.ERROR,
                        error=error
                    )
                    overall_status = HealthStatus.ERROR

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=error_msg,
                components=components
            )

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(
                service=self.service_name,
                version=self.version,
                error=error_msg
            )
