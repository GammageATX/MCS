"""Process Service

This module implements the Process service for managing process execution and control.
"""

import logging
import os
from typing import Dict

import yaml

from mcs.utils.errors import create_error


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
        self.version = version
        self.is_initialized = False
        self.is_running = False
        
        # Default paths
        self.config_path = os.path.join("backend", "config")
        self.schema_path = os.path.join("backend", "schema")
        
        # Component states
        self._components = {}
        self._health = {}

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
            # Load config
            config = self._load_config()
            
            # Initialize components
            await self._initialize_components(config)
            
            # Setup health monitoring
            self._setup_health_monitoring()
            
            self.is_initialized = True
            logger.info("Process service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize process service: {str(e)}")
            raise create_error(
                status_code=500,
                message=f"Failed to initialize process service: {str(e)}"
            )

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        try:
            # Stop components
            for component in self._components.values():
                if hasattr(component, "shutdown"):
                    await component.shutdown()
                    
            self.is_initialized = False
            self.is_running = False
            logger.info("Process service shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during process service shutdown: {str(e)}")
            raise create_error(
                status_code=500,
                message=f"Error during process service shutdown: {str(e)}"
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
            components_config = config.get("components", {})
            
            # Initialize components based on config
            for name, cfg in components_config.items():
                logger.info(f"Initializing component: {name}")
                # Initialize component based on type
                # Add component initialization logic here
                
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise create_error(
                status_code=500,
                message=f"Failed to initialize components: {str(e)}"
            )

    def _setup_health_monitoring(self) -> None:
        """Setup health monitoring for service and components."""
        # Initialize health state
        self._health = {
            "status": "healthy",
            "version": self.version,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {}
        }
        
        # Add component health monitoring
        for name, component in self._components.items():
            if hasattr(component, "health"):
                self._health["components"][name] = component.health()

    async def get_health(self) -> Dict:
        """Get service health status.
        
        Returns:
            Dict containing health status information
        """
        return {
            "status": "healthy" if self.is_running else "stopped",
            "version": self.version,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": self._health.get("components", {})
        }

    def get_version(self) -> str:
        """Get service version.
        
        Returns:
            Service version string
        """
        return self.version
