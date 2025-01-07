"""Equipment service implementation."""

from typing import Dict, Any, Callable
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.communication.services.tag_cache import TagCacheService
from mcs.api.communication.services.internal_state import InternalStateService
from mcs.api.communication.models.state import (
    GasState, VacuumState, EquipmentState, FeederState,
    NozzleState, DeagglomeratorState, PressureState, HardwareState,
    ProcessState
)


class EquipmentService:
    """Service for equipment control."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize service."""
        self._service_name = "equipment"
        self._version = config.get("communication", {}).get("services", {}).get("equipment", {}).get("version", "1.0.0")
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

            if not self._tag_cache or not self._internal_state:
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
            components = {}
            
            # Check tag cache service
            tag_cache_ok = self._tag_cache and self._tag_cache.is_running
            components["tag_cache"] = ComponentHealth(
                status=HealthStatus.OK if tag_cache_ok else HealthStatus.ERROR,
                error=None if tag_cache_ok else "Tag cache service not running"
            )

            # Check internal state service
            internal_state_ok = self._internal_state and self._internal_state.is_running
            components["internal_state"] = ComponentHealth(
                status=HealthStatus.OK if internal_state_ok else HealthStatus.ERROR,
                error=None if internal_state_ok else "Internal state service not running"
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

    async def get_equipment_state(self) -> EquipmentState:
        """Get current equipment state."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if not self._tag_cache or not self._tag_cache.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Tag cache service not running"
                )

            if not self._internal_state or not self._internal_state.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message="Internal state service not running"
                )

            # Get vacuum state
            try:
                chamber_pressure = await self._tag_cache.get_tag("pressure.chamber")
                logger.debug(f"Chamber pressure from tag cache: {chamber_pressure}")
                
                vacuum_state = VacuumState(
                    chamber_pressure=chamber_pressure,
                    gate_valve_state=await self._tag_cache.get_tag("vacuum.gate_valve.open"),
                    mechanical_pump_state=await self._tag_cache.get_tag("vacuum.mechanical_pump.start"),  # wrong, need state this is a momentary tag to start the pump
                    booster_pump_state=await self._tag_cache.get_tag("vacuum.booster_pump.start"),  # wrong, need state this is a momentary tag to start the pump
                    vent_valve_state=await self._tag_cache.get_tag("vacuum.vent_valve")
                )
            except Exception as e:
                logger.error(f"Failed to get vacuum state: {str(e)}")
                raise

            # Get gas state
            try:
                gas_state = GasState(
                    main_flow_rate=await self._tag_cache.get_tag("gas_control.main_flow.measured"),
                    feeder_flow_rate=await self._tag_cache.get_tag("gas_control.feeder_flow.measured"),
                    main_valve_state=await self._tag_cache.get_tag("gas_control.main_valve.open"),
                    feeder_valve_state=await self._tag_cache.get_tag("gas_control.feeder_valve.open")
                )
            except Exception as e:
                logger.error(f"Failed to get gas state: {str(e)}")
                raise

            # Get feeder state
            try:
                # Try feeder1 first, then feeder2
                feeder1_running = await self._tag_cache.get_tag("feeders.feeder1.running")  # wrong, set as bool but its an integer 4 for off 1 for on
                feeder2_running = await self._tag_cache.get_tag("feeders.feeder2.running")  # wrong, set as bool but its an integer 4 for off 1 for on
                feeder1_freq = await self._tag_cache.get_tag("feeders.feeder1.frequency")
                feeder2_freq = await self._tag_cache.get_tag("feeders.feeder2.frequency")
                
                feeder_state = FeederState(
                    running=feeder1_running or feeder2_running,  # True if either feeder is running
                    frequency=feeder1_freq if feeder1_running else feeder2_freq  # Use frequency of active feeder
                )
            except Exception as e:
                logger.error(f"Failed to get feeder state: {str(e)}")
                raise

            # Get deagglomerator state
            try:
                # Try deagg1 first, then deagg2
                deagg1_duty = await self._tag_cache.get_tag("deagglomerators.deagg1.duty_cycle")
                deagg2_duty = await self._tag_cache.get_tag("deagglomerators.deagg2.duty_cycle")
                
                deagg_state = DeagglomeratorState(
                    duty_cycle=deagg1_duty if deagg1_duty is not None else deagg2_duty
                )
            except Exception as e:
                logger.error(f"Failed to get deagglomerator state: {str(e)}")
                raise

            # Get nozzle state
            try:
                nozzle_state = NozzleState(
                    active_nozzle=1 if not await self._tag_cache.get_tag("nozzle.select") else 2,
                    shutter_state=await self._tag_cache.get_tag("nozzle.shutter.open")
                )
            except Exception as e:
                logger.error(f"Failed to get nozzle state: {str(e)}")
                raise

            # Get pressure state
            try:
                pressure_state = PressureState(
                    chamber=await self._tag_cache.get_tag("pressure.chamber"),
                    feeder=await self._tag_cache.get_tag("pressure.feeder"),
                    main_supply=await self._tag_cache.get_tag("pressure.main_supply"),
                    nozzle=await self._tag_cache.get_tag("pressure.nozzle"),
                    regulator=await self._tag_cache.get_tag("pressure.regulator")
                )
            except Exception as e:
                logger.error(f"Failed to get pressure state: {str(e)}")
                raise

            # Get hardware state from internal state service
            try:
                hardware_state = HardwareState(
                    motion_enabled=await self._internal_state.get_state("motion_enabled"),
                    plc_connected=self._tag_cache._plc_client.is_connected(),
                    position_valid=await self._internal_state.get_state("at_valid_position")
                )
            except Exception as e:
                logger.error(f"Failed to get hardware state: {str(e)}")
                raise

            # Get process state from internal state service
            try:
                process_state = ProcessState(
                    gas_flow_stable=await self._internal_state.get_state("flows_stable"),  # I don't think we are actually checking the time average of the flow rates
                    powder_feed_active=await self._internal_state.get_state("powder_feed_on"),
                    process_ready=await self._internal_state.get_state("pressures_stable")  # I don't think we are actually checking the time average of the pressures
                )
            except Exception as e:
                logger.error(f"Failed to get process state: {str(e)}")
                raise

            return EquipmentState(
                gas=gas_state,
                vacuum=vacuum_state,
                feeder=feeder_state,
                deagglomerator=deagg_state,
                nozzle=nozzle_state,
                pressure=pressure_state,
                hardware=hardware_state,
                process=process_state
            )

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

            # Get gas state from individual tags
            try:
                gas_state = GasState(
                    main_flow=await self._tag_cache.get_tag("gas_control.main_flow.setpoint"),
                    main_flow_measured=await self._tag_cache.get_tag("gas_control.main_flow.measured"),
                    feeder_flow=await self._tag_cache.get_tag("gas_control.feeder_flow.setpoint"),
                    feeder_flow_measured=await self._tag_cache.get_tag("gas_control.feeder_flow.measured"),
                    main_valve=await self._tag_cache.get_tag("gas_control.main_valve.open"),
                    feeder_valve=await self._tag_cache.get_tag("gas_control.feeder_valve.open")
                )
                return gas_state
            except Exception as e:
                logger.error(f"Failed to get gas state: {str(e)}")
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to get gas state"
                )

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

            # Get vacuum state from individual tags
            try:
                vacuum_state = VacuumState(
                    chamber_pressure=await self._tag_cache.get_tag("pressure.chamber"),
                    gate_valve=await self._tag_cache.get_tag("vacuum.gate_valve.open"),
                    mech_pump=await self._tag_cache.get_tag("vacuum.mechanical_pump.start"),
                    booster_pump=await self._tag_cache.get_tag("vacuum.booster_pump.start"),
                    vent_valve=await self._tag_cache.get_tag("vacuum.vent_valve")
                )
                return vacuum_state
            except Exception as e:
                logger.error(f"Failed to get vacuum state: {str(e)}")
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to get vacuum state"
                )

        except Exception as e:
            error_msg = "Failed to get vacuum state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_main_flow_rate(self, flow_rate: float) -> None:
        """Set main gas flow rate setpoint."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("gas_control.main_flow.setpoint", flow_rate)
            logger.info(f"Set main gas flow rate to {flow_rate} SLPM")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set main flow rate"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_flow_rate(self, flow_rate: float) -> None:
        """Set feeder gas flow rate setpoint."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("gas_control.feeder_flow.setpoint", flow_rate)
            logger.info(f"Set feeder gas flow rate to {flow_rate} SLPM")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set feeder flow rate"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_main_gas_valve_state(self, open: bool) -> None:
        """Set main gas valve state.
        
        Args:
            open: True to open valve, False to close
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("gas_control.main_valve.open", open)
            logger.info(f"Set main gas valve state to {'open' if open else 'closed'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set main gas valve state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_gas_valve_state(self, open: bool) -> None:
        """Set feeder gas valve state.
        
        Args:
            open: True to open valve, False to close
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("gas_control.feeder_valve.open", open)
            logger.info(f"Set feeder gas valve state to {'open' if open else 'closed'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set feeder gas valve state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_gate_valve_state(self, open: bool) -> None:
        """Set vacuum gate valve state.
        
        Args:
            open: True to open valve, False to close
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("vacuum.gate_valve.open", open)
            logger.info(f"Set vacuum gate valve state to {'open' if open else 'closed'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set gate valve state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_vent_valve_state(self, open: bool) -> None:
        """Set vacuum vent valve state.
        
        Args:
            open: True to open valve, False to close
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("vacuum.vent_valve", open)
            logger.info(f"Set vacuum vent valve state to {'open' if open else 'closed'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set vent valve state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_mechanical_pump_state(self, running: bool) -> None:
        """Set mechanical pump state.
        
        Args:
            running: True to start pump, False to stop
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("vacuum.mechanical_pump.start", running)
            logger.info(f"Set mechanical pump state to {'running' if running else 'stopped'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set mechanical pump state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_booster_pump_state(self, running: bool) -> None:
        """Set booster pump state.
        
        Args:
            running: True to start pump, False to stop
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("vacuum.booster_pump.start", running)
            logger.info(f"Set booster pump state to {'running' if running else 'stopped'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set booster pump state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_frequency(self, feeder_id: int, frequency: float) -> None:
        """Set feeder frequency setpoint.
        
        Args:
            feeder_id: ID of feeder to control (1 or 2)
            frequency: Operating frequency in Hz
        """
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

            await self._tag_cache.set_tag(f"feeders.feeder{feeder_id}.frequency", frequency)
            logger.info(f"Set feeder {feeder_id} frequency to {frequency} Hz")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = f"Failed to set feeder {feeder_id} frequency"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_feeder_state(self, feeder_id: int, running: bool) -> None:
        """Set feeder running state.
        
        Args:
            feeder_id: ID of feeder to control (1 or 2)
            running: True to start feeder, False to stop
        """
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

            await self._tag_cache.set_tag(f"feeders.feeder{feeder_id}.running", running)
            logger.info(f"Set feeder {feeder_id} state to {'running' if running else 'stopped'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = f"Failed to set feeder {feeder_id} state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_nozzle_state(self, nozzle_id: int) -> None:
        """Set active nozzle state.
        
        Args:
            nozzle_id: ID of nozzle to select (1 or 2)
        """
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

            await self._tag_cache.set_tag("nozzle.select", nozzle_id == 2)
            logger.info(f"Set active nozzle state to nozzle {nozzle_id}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set nozzle state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_shutter_state(self, open: bool) -> None:
        """Set nozzle shutter state.
        
        Args:
            open: True to open shutter, False to close
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            await self._tag_cache.set_tag("nozzle.shutter.open", open)
            logger.info(f"Set nozzle shutter state to {'open' if open else 'closed'}")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = "Failed to set shutter state"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_deagglomerator_duty_cycle(self, deagg_id: int, duty_cycle: float) -> None:
        """Set deagglomerator duty cycle setpoint.
        
        Args:
            deagg_id: ID of deagglomerator to control (1 or 2)
            duty_cycle: Duty cycle in percent (0-100)
        """
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

            # Validate duty cycle
            if not 0 <= duty_cycle <= 100:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Invalid duty cycle: {duty_cycle}, must be between 0 and 100"
                )

            await self._tag_cache.set_tag(f"deagglomerators.deagg{deagg_id}.duty_cycle", duty_cycle)
            logger.info(f"Set deagglomerator {deagg_id} duty cycle to {duty_cycle}%")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = f"Failed to set deagglomerator {deagg_id} duty cycle"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def set_deagglomerator_frequency(self, deagg_id: int, frequency: float) -> None:
        """Set deagglomerator frequency setpoint.
        
        Args:
            deagg_id: ID of deagglomerator to control (1 or 2)
            frequency: Operating frequency in Hz
        """
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

            await self._tag_cache.set_tag(f"deagglomerators.deagg{deagg_id}.frequency", frequency)
            logger.info(f"Set deagglomerator {deagg_id} frequency to {frequency} Hz")
            await self._notify_state_changed()

        except Exception as e:
            error_msg = f"Failed to set deagglomerator {deagg_id} frequency"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def _notify_state_changed(self) -> None:
        """Notify subscribers that equipment state has changed."""
        try:
            state = await self.get_equipment_state()
            for callback in self._state_callbacks:
                try:
                    await callback(state)
                except Exception as e:
                    logger.error(f"Error in state callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error notifying state change: {str(e)}")
