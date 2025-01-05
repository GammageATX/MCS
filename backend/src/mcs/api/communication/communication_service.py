"""Communication service implementation."""

from typing import Dict, Any
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth
from mcs.api.communication.services import (
    EquipmentService,
    MotionService,
    TagCacheService,
    TagMappingService
)
from mcs.api.communication.clients import (
    MockPLCClient,
    PLCClient,
    SSHClient
)


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
        self._mode = config.get("mode", "mock")
        self._start_time = None

        # Initialize services to None
        self._tag_mapping = None
        self._tag_cache = None
        self._equipment = None
        self._motion = None

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

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            logger.info(f"Initializing {self.service_name} service...")

            # Create services in dependency order
            self._tag_mapping = TagMappingService(self._config)  # No dependencies

            # Initialize and start tag_mapping first (needed by tag_cache initialization)
            await self._tag_mapping.initialize()
            await self._tag_mapping.start()

            # Initialize clients based on mode
            mode = self._config.get("mode", "mock")
            if mode == "mock":
                plc_client = MockPLCClient(self._config)
                ssh_client = None
            else:
                plc_client = PLCClient(self._config)
                ssh_client = SSHClient(self._config)

            # Create remaining services in dependency order
            self._tag_cache = TagCacheService(self._config, plc_client, ssh_client, self._tag_mapping)  # Depends on tag_mapping
            self._equipment = EquipmentService(self._config)  # Depends on tag_cache
            self._motion = MotionService(self._config)  # Depends on tag_cache

            # Set tag cache dependencies before initializing services
            self._equipment.set_tag_cache(self._tag_cache)
            self._motion.set_tag_cache(self._tag_cache)

            # Initialize and start services in dependency order
            await self._tag_cache.initialize()
            await self._tag_cache.start()  # Start tag_cache before equipment needs it

            await self._equipment.initialize()
            await self._equipment.start()  # Start equipment before motion needs it

            await self._motion.initialize()
            await self._motion.start()  # Start motion last

            logger.info(f"{self.service_name} service initialized")

        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service and all components."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            if not all([self._tag_mapping, self._tag_cache, self._equipment, self._motion]):
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            # All services are already started in initialize()
            # Just set our running state
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
        """Stop service and all components."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )

            # 1. Stop services in reverse dependency order
            await self._motion.stop()
            await self._equipment.stop()
            await self._tag_cache.stop()
            await self._tag_mapping.stop()

            # 2. Clear service references
            self._motion = None
            self._equipment = None
            self._tag_cache = None
            self._tag_mapping = None

            # 3. Reset service state
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
            # Get health from components
            tag_mapping_health = await self._tag_mapping.health() if self._tag_mapping else None
            tag_cache_health = await self._tag_cache.health() if self._tag_cache else None
            equipment_health = await self._equipment.health() if self._equipment else None
            motion_health = await self._motion.health() if self._motion else None

            # Track component states and recovery attempts
            components = {}
            
            # Tag Mapping Component
            components["tag_mapping"] = ComponentHealth(
                status="ok" if tag_mapping_health and tag_mapping_health.status == "ok" else "error",
                error=tag_mapping_health.error if tag_mapping_health else "Component not initialized",
                details={
                    "is_initialized": self._tag_mapping is not None,
                    "is_running": tag_mapping_health.is_running if tag_mapping_health else False,
                    "uptime": tag_mapping_health.uptime if tag_mapping_health else 0
                }
            )

            # Tag Cache Component
            components["tag_cache"] = ComponentHealth(
                status="ok" if tag_cache_health and tag_cache_health.status == "ok" else "error",
                error=tag_cache_health.error if tag_cache_health else "Component not initialized",
                details={
                    "is_initialized": self._tag_cache is not None,
                    "is_running": tag_cache_health.is_running if tag_cache_health else False,
                    "uptime": tag_cache_health.uptime if tag_cache_health else 0,
                    "connection_state": tag_cache_health.components["plc_client"].status if tag_cache_health and "plc_client" in tag_cache_health.components else "unknown"
                }
            )

            # Equipment Component
            components["equipment"] = ComponentHealth(
                status="ok" if equipment_health and equipment_health.status == "ok" else "warning" if equipment_health and any(c.status == "ok" for c in equipment_health.components.values()) else "error",
                error=equipment_health.error if equipment_health else "Component not initialized",
                details={
                    "is_initialized": self._equipment is not None,
                    "is_running": equipment_health.is_running if equipment_health else False,
                    "uptime": equipment_health.uptime if equipment_health else 0,
                    "plc_connected": equipment_health.components["plc_client"].status == "ok" if equipment_health and "plc_client" in equipment_health.components else False,
                    "feeder_status": equipment_health.components["feeder"].status if equipment_health and "feeder" in equipment_health.components else "unknown",
                    "vacuum_status": equipment_health.components["vacuum"].status if equipment_health and "vacuum" in equipment_health.components else "unknown",
                    "motion_status": equipment_health.components["motion"].status if equipment_health and "motion" in equipment_health.components else "unknown"
                }
            )

            # Motion Component
            components["motion"] = ComponentHealth(
                status="ok" if motion_health and motion_health.status == "ok" else "warning" if motion_health and any(c.status == "ok" for c in motion_health.components.values()) else "error",
                error=motion_health.error if motion_health else "Component not initialized",
                details={
                    "is_initialized": self._motion is not None,
                    "is_running": motion_health.is_running if motion_health else False,
                    "uptime": motion_health.uptime if motion_health else 0,
                    "module_ready": motion_health.components["module"].status == "ok" if motion_health and "module" in motion_health.components else False,
                    "axes_status": {
                        axis: motion_health.components[f"{axis}_axis"].status if motion_health and f"{axis}_axis" in motion_health.components else "unknown"
                        for axis in ["x", "y", "z"]
                    }
                }
            )

            # Determine overall status - ok if core functionality available, warning if degraded, error if critical failure
            has_critical = any(c.status == "error" for c in [components["tag_mapping"], components["tag_cache"]])
            has_warning = any(c.status == "warning" for c in components.values())
            has_working = any(c.status == "ok" for c in [components["equipment"], components["motion"]])

            overall_status = "error" if has_critical or not has_working else "warning" if has_warning else "ok"

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None if overall_status == "ok" else "Degraded operation" if overall_status == "warning" else "Critical component failure",
                mode=self._mode,
                components=components
            )

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ServiceHealth(
                status="error",
                service=self.service_name,
                version=self.version,
                is_running=False,
                uptime=self.uptime,
                error=error_msg,
                mode=self._mode,
                components={name: ComponentHealth(status="error", error=error_msg)
                            for name in ["tag_mapping", "tag_cache", "equipment", "motion"]}
            )
