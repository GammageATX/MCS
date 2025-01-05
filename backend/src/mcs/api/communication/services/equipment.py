"""Equipment service implementation."""

from typing import Dict, Any, Callable
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth
from mcs.api.communication.services.tag_cache import TagCacheService
from mcs.api.communication.models.equipment import (
    GasState, VacuumState, EquipmentState
)


class EquipmentService:
    """Service for equipment control."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize service."""
        self._service_name = "equipment"
        self._version = "1.0.0"  # Will be updated from config
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._config = None
        self._tag_cache = None
        self._state_callbacks = []
        
        # Store constructor args for initialization
        self._init_config = config
        
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

    def on_state_changed(self, callback: Callable[[EquipmentState], None]) -> None:
        """Register callback for equipment state changes."""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def remove_state_changed_callback(self, callback: Callable[[EquipmentState], None]) -> None:
        """Remove state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _handle_state_change(self, state_type: str, state: Any) -> None:
        """Handle state change from tag cache."""
        if state_type == "equipment":
            # Notify equipment state callbacks
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in equipment state callback: {str(e)}")

    def set_tag_cache(self, tag_cache: TagCacheService) -> None:
        """Set tag cache service."""
        self._tag_cache = tag_cache
        logger.info(f"{self.service_name} tag cache service set")

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Load config and version
            self._config = self._init_config
            self._version = self._config["communication"]["services"]["equipment"]["version"]

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
            
            # Register for state changes
            self._tag_cache.add_state_callback(self._handle_state_change)
            
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

            # Unregister state callback
            if self._tag_cache:
                self._tag_cache.remove_state_callback(self._handle_state_change)
            
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
            # Get current equipment state
            equipment_state = await self.get_equipment_state()
            
            components = {
                "tag_cache": ComponentHealth(
                    status="ok" if self._tag_cache and self._tag_cache.is_running else "error",
                    error=None if self._tag_cache and self._tag_cache.is_running else "Tag cache not running",
                    details={
                        "is_initialized": self._tag_cache is not None,
                        "is_running": self._tag_cache.is_running if self._tag_cache else False,
                        "uptime": self._tag_cache.uptime if self._tag_cache else 0
                    }
                )
            }
            
            if equipment_state:
                # Gas control health - warning if flows out of tolerance
                gas_status = "ok"
                gas_error = None
                gas_details = {}
                if equipment_state.gas:
                    gas = equipment_state.gas
                    # Only check flows if they are active (non-zero setpoint)
                    if gas.main_flow > 0:
                        main_flow_error = abs(gas.main_flow - gas.main_flow_measured) / gas.main_flow > 0.1
                        if main_flow_error:
                            gas_status = "warning"
                            gas_error = "Main flow out of tolerance"
                    
                    if gas.feeder_flow > 0:
                        feeder_flow_error = abs(gas.feeder_flow - gas.feeder_flow_measured) / gas.feeder_flow > 0.1
                        if feeder_flow_error:
                            gas_status = "warning"
                            gas_error = gas_error or "Feeder flow out of tolerance"
                            
                    gas_details = {
                        "main_flow": {"setpoint": gas.main_flow, "measured": gas.main_flow_measured},
                        "feeder_flow": {"setpoint": gas.feeder_flow, "measured": gas.feeder_flow_measured},
                        "valves": {"main": gas.main_valve, "feeder": gas.feeder_valve}
                    }
                else:
                    gas_status = "error"
                    gas_error = "Gas state not available"
                
                components["gas"] = ComponentHealth(
                    status=gas_status,
                    error=gas_error,
                    details=gas_details
                )
                
                # Vacuum system health - warning if pressure high but system functional
                vacuum_status = "ok"
                vacuum_error = None
                vacuum_details = {}
                if equipment_state.vacuum:
                    vacuum = equipment_state.vacuum
                    if vacuum.chamber_pressure > 1000:
                        vacuum_status = "warning"
                        vacuum_error = "Chamber pressure high"
                    elif vacuum.chamber_pressure > 5000:
                        vacuum_status = "error"
                        vacuum_error = "Chamber pressure too high"
                        
                    vacuum_details = {
                        "chamber_pressure": vacuum.chamber_pressure,
                        "pumps": {
                            "mechanical": vacuum.mech_pump,
                            "booster": vacuum.booster_pump
                        },
                        "valves": {
                            "gate": vacuum.gate_valve,
                            "vent": vacuum.vent_valve
                        }
                    }
                else:
                    vacuum_status = "error"
                    vacuum_error = "Vacuum state not available"
                
                components["vacuum"] = ComponentHealth(
                    status=vacuum_status,
                    error=vacuum_error,
                    details=vacuum_details
                )
                
                # Hardware health - warning if some systems disabled but others ok
                hardware_status = "ok"
                hardware_error = None
                hardware_details = {}
                if equipment_state.hardware:
                    hardware = equipment_state.hardware
                    if not hardware.motion_enabled and not hardware.position_valid:
                        hardware_status = "error"
                        hardware_error = "Motion system disabled and position invalid"
                    elif not hardware.motion_enabled:
                        hardware_status = "warning"
                        hardware_error = "Motion system disabled"
                    elif not hardware.position_valid:
                        hardware_status = "warning"
                        hardware_error = "Position tracking invalid"
                        
                    hardware_details = {
                        "motion_enabled": hardware.motion_enabled,
                        "position_valid": hardware.position_valid,
                        "plc_connected": hardware.plc_connected
                    }
                else:
                    hardware_status = "error"
                    hardware_error = "Hardware state not available"
                
                components["hardware"] = ComponentHealth(
                    status=hardware_status,
                    error=hardware_error,
                    details=hardware_details
                )
                
                # Safety health - no warnings, either ok or error
                safety_status = "ok"
                safety_error = None
                safety_details = {}
                if equipment_state.safety:
                    safety = equipment_state.safety
                    if safety.emergency_stop:
                        safety_status = "error"
                        safety_error = "Emergency stop active"
                    elif not safety.interlocks_ok:
                        safety_status = "error"
                        safety_error = "Interlocks not satisfied"
                    elif not safety.limits_ok:
                        safety_status = "error"
                        safety_error = "Motion limits exceeded"
                        
                    safety_details = {
                        "emergency_stop": safety.emergency_stop,
                        "interlocks_ok": safety.interlocks_ok,
                        "limits_ok": safety.limits_ok
                    }
                else:
                    safety_status = "error"
                    safety_error = "Safety state not available"
                
                components["safety"] = ComponentHealth(
                    status=safety_status,
                    error=safety_error,
                    details=safety_details
                )
            
            return components
            
        except Exception as e:
            logger.error(f"Failed to get component health: {str(e)}")
            return {
                "error": ComponentHealth(
                    status="error",
                    error=f"Failed to get component health: {str(e)}"
                )
            }

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            component_healths = await self._get_component_health()
            
            return ServiceHealth(
                status="ok" if all(h.status == "ok" for h in component_healths.values()) else "error",
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None if all(h.status == "ok" for h in component_healths.values()) else "One or more components in error state",
                components=component_healths
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
                components={"error": ComponentHealth(status="error", error=error_msg)}
            )

    async def get_equipment_state(self) -> EquipmentState:
        """Get equipment state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get cached equipment state
            state = await self._tag_cache.get_state("equipment")
            if not state:
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Equipment state not available"
                )

            return state

        except Exception as e:
            error_msg = "Failed to get equipment state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_gas_state(self) -> GasState:
        """Get gas system state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get cached gas state
            state = await self._tag_cache.get_state("gas")
            if not state:
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Gas state not available"
                )

            return state

        except Exception as e:
            error_msg = "Failed to get gas state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_vacuum_state(self) -> VacuumState:
        """Get vacuum system state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Get cached vacuum state
            state = await self._tag_cache.get_state("vacuum")
            if not state:
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Vacuum state not available"
                )

            return state

        except Exception as e:
            error_msg = "Failed to get vacuum state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_main_flow(self, flow_rate: float) -> None:
        """Set main gas flow rate."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write flow rate setpoint
            await self._tag_cache.set_tag("gas_control.main_flow.setpoint", flow_rate)
            logger.info(f"Set main gas flow to {flow_rate} SLPM")

        except Exception as e:
            error_msg = "Failed to set main flow"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_flow(self, flow_rate: float) -> None:
        """Set feeder gas flow rate."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write flow rate setpoint
            await self._tag_cache.set_tag("gas_control.feeder_flow.setpoint", flow_rate)
            logger.info(f"Set feeder gas flow to {flow_rate} SLPM")

        except Exception as e:
            error_msg = "Failed to set feeder flow"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_main_valve(self, open: bool) -> None:
        """Set main gas valve state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write valve state
            await self._tag_cache.set_tag("gas_control.main_valve.open", open)
            logger.info(f"Set main gas valve {'open' if open else 'closed'}")

        except Exception as e:
            error_msg = "Failed to set main valve"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_valve(self, open: bool) -> None:
        """Set feeder gas valve state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write valve state
            await self._tag_cache.set_tag("gas_control.feeder_valve.open", open)
            logger.info(f"Set feeder gas valve {'open' if open else 'closed'}")

        except Exception as e:
            error_msg = "Failed to set feeder valve"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_gate_valve(self, open: bool) -> None:
        """Set vacuum gate valve state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write valve state
            await self._tag_cache.set_tag("vacuum.gate_valve.open", open)
            logger.info(f"Set vacuum gate valve {'open' if open else 'closed'}")

        except Exception as e:
            error_msg = "Failed to set gate valve"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_vent_valve(self, open: bool) -> None:
        """Set vacuum vent valve state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write valve state
            await self._tag_cache.set_tag("vacuum.vent_valve", open)
            logger.info(f"Set vacuum vent valve {'open' if open else 'closed'}")

        except Exception as e:
            error_msg = "Failed to set vent valve"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_mechanical_pump(self, start: bool) -> None:
        """Set mechanical pump state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write pump state
            await self._tag_cache.set_tag("vacuum.mechanical_pump.start", start)
            logger.info(f"Set mechanical pump {'started' if start else 'stopped'}")

        except Exception as e:
            error_msg = "Failed to set mechanical pump"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_booster_pump(self, start: bool) -> None:
        """Set booster pump state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write pump state
            await self._tag_cache.set_tag("vacuum.booster_pump.start", start)
            logger.info(f"Set booster pump {'started' if start else 'stopped'}")

        except Exception as e:
            error_msg = "Failed to set booster pump"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_frequency(self, feeder_id: int, frequency: float) -> None:
        """Set feeder frequency."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate feeder ID
            if feeder_id not in [1, 2]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid feeder ID: {feeder_id}"
                )

            # Write frequency
            await self._tag_cache.set_tag(f"feeders.feeder{feeder_id}.frequency", frequency)
            logger.info(f"Set feeder {feeder_id} frequency to {frequency} Hz")

        except Exception as e:
            error_msg = f"Failed to set feeder {feeder_id} frequency"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_running(self, feeder_id: int, running: bool) -> None:
        """Set feeder running state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate feeder ID
            if feeder_id not in [1, 2]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid feeder ID: {feeder_id}"
                )

            # Write running state
            await self._tag_cache.set_tag(f"feeders.feeder{feeder_id}.running", running)
            logger.info(f"Set feeder {feeder_id} {'running' if running else 'stopped'}")

        except Exception as e:
            error_msg = f"Failed to set feeder {feeder_id} running state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_nozzle_select(self, nozzle_id: int) -> None:
        """Set active nozzle."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate nozzle ID
            if nozzle_id not in [1, 2]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid nozzle ID: {nozzle_id}"
                )

            # Write nozzle select (True = nozzle 2, False = nozzle 1)
            await self._tag_cache.set_tag("nozzle.select", nozzle_id == 2)
            logger.info(f"Selected nozzle {nozzle_id}")

        except Exception as e:
            error_msg = "Failed to set nozzle select"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_shutter_open(self, open: bool) -> None:
        """Set nozzle shutter state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Write shutter state
            await self._tag_cache.set_tag("nozzle.shutter.open", open)
            logger.info(f"Set nozzle shutter {'open' if open else 'closed'}")

        except Exception as e:
            error_msg = "Failed to set shutter state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_deagglomerator_duty_cycle(self, deagg_id: int, duty_cycle: float) -> None:
        """Set deagglomerator duty cycle."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate deagglomerator ID
            if deagg_id not in [1, 2]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid deagglomerator ID: {deagg_id}"
                )

            # Write duty cycle
            await self._tag_cache.set_tag(f"deagglomerators.deagg{deagg_id}.duty_cycle", duty_cycle)
            logger.info(f"Set deagglomerator {deagg_id} duty cycle to {duty_cycle}%")

        except Exception as e:
            error_msg = f"Failed to set deagglomerator {deagg_id} duty cycle"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_deagglomerator_frequency(self, deagg_id: int, frequency: float) -> None:
        """Set deagglomerator frequency."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Validate deagglomerator ID
            if deagg_id not in [1, 2]:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid deagglomerator ID: {deagg_id}"
                )

            # Write frequency
            await self._tag_cache.set_tag(f"deagglomerators.deagg{deagg_id}.frequency", frequency)
            logger.info(f"Set deagglomerator {deagg_id} frequency to {frequency} Hz")

        except Exception as e:
            error_msg = f"Failed to set deagglomerator {deagg_id} frequency"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
