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
        try:
            # Check tag cache status
            tag_cache_ok = self._tag_cache and self._tag_cache.is_running
            components = {
                "tag_cache": ComponentHealth(
                    status=HealthStatus.OK if tag_cache_ok else HealthStatus.ERROR,
                    error=None if tag_cache_ok else "Tag cache not running"
                )
            }
            
            # Check motion system status
            try:
                status = await self.get_status()
                if status:
                    # Check motion module
                    components["module"] = ComponentHealth(
                        status=HealthStatus.OK if status.module_ready else HealthStatus.ERROR,
                        error=None if status.module_ready else "Motion module not ready"
                    )
                    
                    # Check critical axes
                    for axis_name, axis in [("x", status.x_axis), ("y", status.y_axis), ("z", status.z_axis)]:
                        axis_homed = axis.homed
                        # Error only if axis has fault, degraded if not homed
                        status = HealthStatus.ERROR if axis.error else (
                            HealthStatus.DEGRADED if not axis_homed else HealthStatus.OK
                        )
                        components[f"{axis_name}_axis"] = ComponentHealth(
                            status=status,
                            error="Axis error" if axis.error else ("Not homed" if not axis_homed else None)
                        )
                else:
                    components["status"] = ComponentHealth(
                        status=HealthStatus.ERROR,
                        error="Motion status not available"
                    )
            except Exception as e:
                logger.error(f"Failed to get motion status: {str(e)}")
                components["status"] = ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=f"Failed to get motion status: {str(e)}"
                )
            
            return components
            
        except Exception as e:
            logger.error(f"Failed to get component health: {str(e)}")
            return {
                "error": ComponentHealth(
                    status=HealthStatus.ERROR,
                    error=f"Failed to get component health: {str(e)}"
                )
            }

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

            # Read current position from AMC controller
            x = await self._tag_cache.get_tag("motion.motion_control.coordinated_move.xy_move.parameters.x_position")
            y = await self._tag_cache.get_tag("motion.motion_control.coordinated_move.xy_move.parameters.y_position")
            z = await self._tag_cache.get_tag("motion.motion_control.relative_move.z_move.parameters.position")

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
            module_ready = await self._tag_cache.get_tag("interlocks.motion_ready")
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
                # For X and Y axes, use coordinated move status
                position = await self._tag_cache.get_tag(f"motion.motion_control.coordinated_move.xy_move.parameters.{axis}_position")
                in_progress = await self._tag_cache.get_tag("motion.motion_control.coordinated_move.xy_move.parameters.in_progress")
                complete = await self._tag_cache.get_tag("motion.motion_control.coordinated_move.xy_move.parameters.status")
            else:
                # For Z axis, use relative move status
                position = await self._tag_cache.get_tag(f"motion.motion_control.relative_move.{axis}_move.parameters.position")
                in_progress = await self._tag_cache.get_tag(f"motion.motion_control.relative_move.{axis}_move.parameters.in_progress")
                complete = await self._tag_cache.get_tag(f"motion.motion_control.relative_move.{axis}_move.parameters.status")

            # Parse status
            moving = bool(in_progress)  # Moving if in progress
            in_position = bool(complete)  # In position if move completed
            error = not await self._tag_cache.get_tag("interlocks.motion_ready")  # Error if not enabled
            homed = bool(complete)  # Consider homed if last move completed

            # Default to 0 if position is None
            position = position if position is not None else 0.0

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

            # Set XY move parameters
            await self._tag_cache.set_tag("motion.motion_control.coordinated_move.xy_move.parameters.x_position", x)
            await self._tag_cache.set_tag("motion.motion_control.coordinated_move.xy_move.parameters.y_position", y)
            await self._tag_cache.set_tag("motion.motion_control.coordinated_move.xy_move.parameters.velocity", velocity)
            
            # Trigger XY move
            await self._tag_cache.set_tag("motion.motion_control.coordinated_move.xy_move.trigger", True)
            
            # Set Z position and trigger move
            await self._tag_cache.set_tag("motion.motion_control.relative_move.z_move.parameters.position", z)
            await self._tag_cache.set_tag("motion.motion_control.relative_move.z_move.parameters.velocity", velocity)
            await self._tag_cache.set_tag("motion.motion_control.relative_move.z_move.trigger", True)

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

            # Set velocity and trigger move
            move_tag = f"motion.motion_control.relative_move.{axis}_move"
            await self._tag_cache.set_tag(f"{move_tag}.parameters.position", distance)
            await self._tag_cache.set_tag(f"{move_tag}.parameters.velocity", velocity)
            await self._tag_cache.set_tag(f"{move_tag}.trigger", True)

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

            # Set current position as home
            await self._tag_cache.set_tag("motion.set_home", True)

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
        """Move to home position."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Trigger move to home
            await self._tag_cache.set_tag("motion.motion_control.move_to_home", True)

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
