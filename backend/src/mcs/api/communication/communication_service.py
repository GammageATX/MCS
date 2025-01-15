"""Communication service implementation."""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import status
from loguru import logger
import json

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.communication.services import (
    EquipmentService,
    InternalStateService,
    MotionService,
    TagCacheService,
    TagMappingService
)
from mcs.api.communication.clients import (
    MockPLCClient,
    PLCClient,
    SSHClient
)


def load_config() -> Dict[str, Any]:
    """Load service configuration.

    Returns:
        Dict[str, Any]: Configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
    """
    config_path = Path("backend/config/communication.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    return config


class CommunicationService:
    """Communication service."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize service.

        Args:
            config: Service configuration
        """
        self._service_name = "communication"
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._start_time = None

        # Initialize services to None
        self._tag_mapping = None
        self._tag_cache = None
        self._equipment = None
        self._motion = None
        self._internal_state = None

        logger.info(f"{self._service_name} service initialized")

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
    def uptime(self) -> float:
        """Get service uptime."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    @property
    def equipment(self) -> EquipmentService:
        """Get equipment service."""
        return self._equipment

    @property
    def motion(self) -> MotionService:
        """Get motion service."""
        return self._motion

    @property
    def tag_cache(self) -> TagCacheService:
        """Get tag cache service."""
        return self._tag_cache

    @property
    def tag_mapping(self) -> TagMappingService:
        """Get tag mapping service."""
        return self._tag_mapping

    @property
    def internal_state(self) -> InternalStateService:
        """Get internal state service."""
        return self._internal_state

    async def initialize(self) -> None:
        """One-time initialization and basic setup.
        
        The initialize method handles operations that don't require running dependencies:
        1. Creating service instances
        2. Loading configurations
        3. Basic setup
        """
        try:
            logger.info(f"Initializing {self.service_name} service...")

            # Create core services
            self._tag_mapping = TagMappingService(self._config)
            await self._tag_mapping.initialize()

            # Initialize clients based on force_mock setting
            force_mock = self._config.get("communication", {}).get("hardware", {}).get("network", {}).get("force_mock", True)
            if force_mock:
                logger.info("Using mock PLC client (force_mock=true)")
                plc_client = MockPLCClient(self._config)
                # Use the same mock client for SSH tags
                ssh_client = plc_client
            else:
                logger.info("Using real PLC client (force_mock=false)")
                plc_client = PLCClient(self._config)
                ssh_client = SSHClient(self._config)

            # Create remaining services
            self._tag_cache = TagCacheService(self._config, plc_client, ssh_client, self._tag_mapping)
            self._equipment = EquipmentService(self._config)
            self._motion = MotionService(self._config)
            self._internal_state = InternalStateService(self._config)

            logger.info(f"{self.service_name} service basic initialization complete")

        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def prepare(self) -> None:
        """Prepare service for operation.
        
        The prepare method handles operations that require running dependencies:
        1. Starting core services needed by others
        2. Initializing dependent services
        3. Setting up service interconnections
        """
        try:
            logger.info(f"Preparing {self.service_name} service...")

            # 1. Initialize and start tag_mapping
            await self._tag_mapping.start()

            # 2. Initialize and start tag_cache
            await self._tag_cache.initialize()
            await self._tag_cache.start()

            # 3. Set up service interconnections
            self._equipment.set_tag_cache(self._tag_cache)
            self._equipment.set_internal_state(self._internal_state)
            self._motion.set_tag_cache(self._tag_cache)
            self._motion.set_internal_state(self._internal_state)
            self._internal_state.set_tag_cache(self._tag_cache)
            self._internal_state.set_tag_mapping(self._tag_mapping)

            # 4. Initialize remaining services
            await self._equipment.initialize()
            await self._motion.initialize()
            await self._internal_state.initialize()

            logger.info(f"{self.service_name} service preparation complete")

        except Exception as e:
            error_msg = f"Failed to prepare {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service operations.
        
        The start method handles:
        1. Starting remaining services
        2. Beginning actual operations
        """
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Ensure services are prepared
            if not all([self._tag_mapping, self._tag_cache, self._equipment, self._motion, self._internal_state]):
                logger.info(f"Services need initialization, preparing {self.service_name} service")
                await self.initialize()
                await self.prepare()

            # Start remaining services (tag_mapping and tag_cache already running from prepare)
            await self._equipment.start()
            await self._motion.start()
            await self._internal_state.start()

            # Set main service state
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

    async def stop(self) -> None:
        """Stop service components but maintain initialization state.
        
        The stop method:
        1. Stops all services in reverse dependency order
        2. Maintains service references but clears initialized state
        3. Allows restart via start() which will reinitialize
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )

            # Stop services in reverse dependency order
            if self._internal_state:
                await self._internal_state.stop()
            if self._motion:
                await self._motion.stop()
            if self._equipment:
                await self._equipment.stop()
            if self._tag_cache:
                await self._tag_cache.stop()
            if self._tag_mapping:
                await self._tag_mapping.stop()

            # Reset service state but maintain references
            self._is_running = False
            self._start_time = None

            # Clear initialized state so start() will reinitialize
            self._tag_mapping = None
            self._tag_cache = None
            self._equipment = None
            self._motion = None
            self._internal_state = None

            logger.info(f"{self.service_name} service stopped")

        except Exception as e:
            error_msg = f"Failed to stop {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources.
        
        The shutdown method:
        1. Stops all services if running
        2. Cleans up resources and references
        3. Requires re-initialization to use again
        """
        try:
            # Stop if running
            if self.is_running:
                await self.stop()
            else:
                # Clear service references even if not running
                self._internal_state = None
                self._motion = None
                self._equipment = None
                self._tag_cache = None
                self._tag_mapping = None

            logger.info(f"{self.service_name} service shutdown complete")

        except Exception as e:
            error_msg = f"Failed to shutdown {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Get health from critical components
            tag_mapping_health = await self._tag_mapping.health() if self._tag_mapping else None
            tag_cache_health = await self._tag_cache.health() if self._tag_cache else None
            equipment_health = await self._equipment.health() if self._equipment else None
            motion_health = await self._motion.health() if self._motion else None
            internal_state_health = await self._internal_state.health() if self._internal_state else None

            # Track critical component states
            components = {}
            
            # Tag Mapping (Critical - needed for all operations)
            components["tag_mapping"] = ComponentHealth(
                status=HealthStatus.OK if tag_mapping_health and tag_mapping_health.status == HealthStatus.OK else HealthStatus.ERROR,
                error=tag_mapping_health.error if tag_mapping_health else "Component not initialized",
                details={"is_initialized": self._tag_mapping is not None}
            )

            # Tag Cache (Critical - needed for hardware communication)
            components["tag_cache"] = ComponentHealth(
                status=HealthStatus.OK if tag_cache_health and tag_cache_health.status == HealthStatus.OK else HealthStatus.ERROR,
                error=tag_cache_health.error if tag_cache_health else "Component not initialized",
                details={"plc_connected": tag_cache_health.components["plc_client"].status == HealthStatus.OK if tag_cache_health and "plc_client" in tag_cache_health.components else False}
            )

            # Equipment (Critical hardware systems)
            components["equipment"] = ComponentHealth(
                status=HealthStatus.OK if equipment_health and equipment_health.status == HealthStatus.OK else HealthStatus.ERROR,
                error=equipment_health.error if equipment_health else "Component not initialized",
                details={"is_initialized": self._equipment is not None}
            )

            # Motion (Critical for pattern execution)
            components["motion"] = ComponentHealth(
                status=HealthStatus.OK if motion_health and motion_health.status == HealthStatus.OK else HealthStatus.ERROR,
                error=motion_health.error if motion_health else "Component not initialized",
                details={"is_initialized": self._motion is not None}
            )

            # Internal State (Critical for operation)
            components["internal_state"] = ComponentHealth(
                status=HealthStatus.OK if internal_state_health and internal_state_health.status == HealthStatus.OK else HealthStatus.ERROR,
                error=internal_state_health.error if internal_state_health else "Component not initialized",
                details={"is_initialized": self._internal_state is not None}
            )

            # Overall status is error if any critical component is in error
            overall_status = HealthStatus.ERROR if any(
                c.status == HealthStatus.ERROR for c in components.values()
            ) else HealthStatus.OK

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None if overall_status == HealthStatus.OK else "Critical component error",
                components=components
            )

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg)
