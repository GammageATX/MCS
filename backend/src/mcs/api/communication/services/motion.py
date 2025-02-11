"""Motion service implementation."""

from typing import Dict, Any, Callable
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.communication.services.tag_cache import TagCacheService
from mcs.api.communication.services.internal_state import InternalStateService
from mcs.api.communication.models.state import (
    Position, SystemStatus, MotionState, AxisStatus
)


class MotionService:
    """Service for motion control."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize service."""
        self._service_name = "motion"
        self._version = config.get("communication", {}).get("services", {}).get("motion", {}).get("version", "1.0.0")
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._config = config  # Store config here
        self._tag_cache = None
        self._internal_state = None
        self._state_callbacks = []
        
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
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    def on_state_changed(self, callback: Callable[[MotionState], None]) -> None:
        """Register callback for motion state changes."""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def remove_state_changed_callback(self, callback: Callable[[MotionState], None]) -> None:
        """Remove state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    async def _notify_state_changed(self) -> None:
        """Notify all registered callbacks of state change."""
        try:
            position = await self.get_position()
            status = await self.get_status()
            state = MotionState(position=position, status=status)
            
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error notifying state change: {str(e)}")

    def set_tag_cache(self, tag_cache: TagCacheService) -> None:
        """Set tag cache service."""
        self._tag_cache = tag_cache
        logger.info(f"{self.service_name} tag cache service set")

    def set_internal_state(self, internal_state: InternalStateService) -> None:
        """Set internal state service."""
        self._internal_state = internal_state
        logger.info(f"{self.service_name} internal state service set")

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Initialize tag cache
            if not self._tag_cache:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} tag cache service not initialized"
                )

            # Wait for tag cache service to be ready
            if not self._tag_cache.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} tag cache service not running"
                )
            
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
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

            if not self._tag_cache or not self._tag_cache.is_running:
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

            # Clear state callbacks
            self._state_callbacks.clear()
            
            # Reset service state
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

    async def _get_component_health(self) -> Dict[str, ComponentHealth]:
        """Get health status of all components."""
        components = {}
        
        # Check tag cache status
        tag_cache_ok = self._tag_cache and self._tag_cache.is_running
        components["tag_cache"] = ComponentHealth(
            status=HealthStatus.OK if tag_cache_ok else HealthStatus.ERROR,
            error=None if tag_cache_ok else "Tag cache not running"
        )
        
        # Only check hardware if tag cache is running
        if tag_cache_ok:
            try:
                # Try to read position to verify communication
                position = await self._tag_cache.get_tag("motion.position.x")
                hardware_ok = position is not None
                components["hardware"] = ComponentHealth(
                    status=HealthStatus.OK if hardware_ok else HealthStatus.WARN,
                    error=None if hardware_ok else "Failed to read position"
                )
            except Exception as e:
                logger.error(f"Failed to read position: {str(e)}")
                components["hardware"] = ComponentHealth(
                    status=HealthStatus.WARN,  # Warn instead of error since motion might not be critical
                    error=f"Failed to read position: {str(e)}"
                )
        
        return components

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            components = await self._get_component_health()
            
            # Overall status is OK if service is running, even if some components are degraded
            # Only ERROR if critical failures occur
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

    async def get_position(self) -> Position:
        """Get current position."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get current positions from motion.position.*
            x = await self._tag_cache.get_tag("motion.position.x")
            y = await self._tag_cache.get_tag("motion.position.y")
            z = await self._tag_cache.get_tag("motion.position.z")

            # Default to 0 if position is None
            x = x if x is not None else 0.0
            y = y if y is not None else 0.0
            z = z if z is not None else 0.0

            return Position(x=x, y=y, z=z)

        except Exception as e:
            error_msg = "Failed to get position"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_status(self) -> SystemStatus:
        """Get system status."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get axis statuses
            x_status = await self.get_axis_status("x")
            y_status = await self.get_axis_status("y")
            z_status = await self.get_axis_status("z")

            # Get module ready status
            module_ready = await self._tag_cache.get_tag("motion.status.module")
            if module_ready is None:
                module_ready = False

            return SystemStatus(
                x_axis=x_status,
                y_axis=y_status,
                z_axis=z_status,
                module_ready=module_ready
            )

        except Exception as e:
            error_msg = "Failed to get system status"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_axis_status(self, axis: str) -> AxisStatus:
        """Get axis status."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate axis
            if axis not in ["x", "y", "z"]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid axis: {axis}"
                )

            # Get axis status
            if axis in ["x", "y"]:
                # Get coordinated move status
                current_position = await self._tag_cache.get_tag(f"motion.position.{axis}")
                in_progress = await self._tag_cache.get_tag("motion.coordinated_move.xy.in_progress")
                complete = await self._tag_cache.get_tag("motion.coordinated_move.xy.status")
            else:
                # Get relative move status for Z
                current_position = await self._tag_cache.get_tag(f"motion.position.{axis}")
                in_progress = await self._tag_cache.get_tag(f"motion.relative_move.{axis}.in_progress")
                complete = await self._tag_cache.get_tag(f"motion.relative_move.{axis}.status")

            # Parse status
            in_position = bool(complete)  # In position if move completed
            moving = bool(in_progress)  # Moving if in progress
            error = False  # No longer using module status for error detection
            homed = True   # Assume homed since we don't have explicit homing status

            # Default to 0 if position is None
            position = current_position if current_position is not None else 0.0

            return AxisStatus(
                position=position,
                in_position=in_position,
                moving=moving,
                error=error,
                homed=homed
            )

        except Exception as e:
            error_msg = f"Failed to get {axis} axis status"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def move(self, x: float, y: float, z: float, velocity: float, wait_complete: bool = True) -> None:
        """Move to position."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Set XY target positions and parameters for coordinated move
            await self._tag_cache.set_tag("motion.coordinated_move.xy.x_position", x)
            await self._tag_cache.set_tag("motion.coordinated_move.xy.y_position", y)
            await self._tag_cache.set_tag("motion.coordinated_move.xy.velocity", velocity)
            
            # Trigger XY move
            await self._tag_cache.set_tag("motion.coordinated_move.xy.trigger", True)

            # Notify state change
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to move"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def jog_axis(self, axis: str, distance: float, velocity: float) -> None:
        """Jog axis by distance."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate axis
            if axis not in ["x", "y", "z"]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid axis: {axis}"
                )

            if axis in ["x", "y"]:
                # For X/Y, use coordinated move
                await self._tag_cache.set_tag(f"coordinated_move.xy.{axis}_position", distance)
                await self._tag_cache.set_tag("coordinated_move.xy.velocity", velocity)
                await self._tag_cache.set_tag("coordinated_move.xy.trigger", True)
            else:
                # For Z, use relative move
                await self._tag_cache.set_tag("relative_move.z.position", distance)
                await self._tag_cache.set_tag("relative_move.z.velocity", velocity)
                await self._tag_cache.set_tag("relative_move.z.trigger", True)

            # Notify state change
            await self._notify_state_changed()

        except Exception as e:
            error_msg = f"Failed to jog {axis} axis"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_home(self) -> None:
        """Set current position as home."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Set home position
            await self._tag_cache.set_tag("set_home", True)

            # Notify state change
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set home"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def move_to_home(self) -> None:
        """Move all axes to home position."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Default velocity for homing
            velocity = 10.0  # mm/s

            # Move to home position
            await self._tag_cache.set_tag("motion.coordinated_move.xy.x_position", 0)
            await self._tag_cache.set_tag("motion.coordinated_move.xy.y_position", 0)
            await self._tag_cache.set_tag("motion.coordinated_move.xy.velocity", velocity)
            await self._tag_cache.set_tag("motion.coordinated_move.xy.trigger", True)

            # Notify state change
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to move to home"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_motion_state(self) -> MotionState:
        """Get current motion state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get position from raw tags
            position = await self.get_position()
            system_status = await self.get_status()

            # Get internal states
            at_valid_position = await self._internal_state.get_state("at_valid_position")
            motion_enabled = await self._internal_state.get_state("motion_enabled")

            # Update status with internal states
            system_status.module_ready = motion_enabled
            system_status.x_axis.in_position = at_valid_position and not system_status.x_axis.moving
            system_status.y_axis.in_position = at_valid_position and not system_status.y_axis.moving
            system_status.z_axis.in_position = at_valid_position and not system_status.z_axis.moving

            return MotionState(
                position=position,
                status=system_status
            )

        except Exception as e:
            error_msg = "Failed to get motion state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
