"""Tag cache service implementation."""

import asyncio
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth
from mcs.api.communication.clients.mock import MockPLCClient
from mcs.api.communication.clients.plc import PLCClient
from mcs.api.communication.clients.ssh import SSHClient
from mcs.api.communication.services.tag_mapping import TagMappingService
from mcs.api.communication.models.equipment import (
    GasState, VacuumState, FeederState, NozzleState, EquipmentState,
    DeagglomeratorState, PressureState, MotionState, HardwareState,
    ProcessState, SafetyState
)
from mcs.api.communication.models.motion import (
    Position, AxisStatus, SystemStatus
)


class TagCacheService:
    """Service for caching PLC tag values."""

    def __init__(self, config: Dict[str, Any], plc_client: Union[PLCClient, MockPLCClient], ssh_client: Optional[SSHClient], tag_mapping: TagMappingService):
        """Initialize tag cache service."""
        self._service_name = "tag_cache"
        self._version = "1.0.0"  # Will be updated from config
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._config = None
        self._plc_client = None
        self._ssh_client = None
        self._tag_mapping = None
        self._cache = {}
        self._state_cache = {}
        self._polling_task = None
        self._polling = None
        self._state_callbacks = []
        
        # Store constructor args for initialization
        self._init_config = config
        self._init_plc_client = plc_client
        self._init_ssh_client = ssh_client
        self._init_tag_mapping = tag_mapping
        
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
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Initialize components
            self._config = self._init_config
            self._version = self._config["communication"]["services"]["tag_cache"]["version"]
            self._polling = self._config["communication"]["polling"]
            self._plc_client = self._init_plc_client
            self._ssh_client = self._init_ssh_client
            self._tag_mapping = self._init_tag_mapping
            
            # Initialize empty cache
            self._cache = {}
            
            # Connect PLC client
            logger.info("Connecting PLC client")
            await self._plc_client.connect()
            
            # Get all mapped PLC tags
            plc_tags = []
            internal_to_plc = {}  # Track mapping for error reporting
            for internal_tag, tag_info in self._tag_mapping._tag_map.items():
                if tag_info.get("mapped", False) and tag_info.get("plc_tag"):
                    plc_tag = tag_info["plc_tag"]
                    plc_tags.append(plc_tag)
                    internal_to_plc[plc_tag] = internal_tag
            
            logger.info(f"Found {len(plc_tags)} mapped PLC tags")
            
            # Get initial values
            if plc_tags:
                try:
                    values = await self._plc_client.get(plc_tags)
                    logger.debug(f"Retrieved {len(values)} initial PLC values")
                    
                    # Store both PLC and internal tag values
                    for plc_tag, value in values.items():
                        internal_tag = internal_to_plc[plc_tag]
                        # Store raw PLC tag value
                        self._cache[plc_tag] = value
                        # Store scaled internal tag value
                        scaled_value = self._tag_mapping.scale_value(internal_tag, value)
                        self._cache[internal_tag] = scaled_value
                        logger.debug(f"Initialized {internal_tag} = {scaled_value} (PLC: {plc_tag} = {value})")
                        
                    # Log any missing tags
                    missing_tags = set(plc_tags) - set(values.keys())
                    if missing_tags:
                        missing_internal = [internal_to_plc[t] for t in missing_tags]
                        logger.warning(f"Missing PLC tags: {missing_tags}")
                        logger.warning(f"Corresponding internal tags: {missing_internal}")
                        
                except Exception as e:
                    logger.error(f"Failed to get initial PLC values: {e}")
                    raise
            
            logger.info(f"{self.service_name} service initialized with {len(self._cache)} cached values")
            
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
                
            if not self._plc_client or not self._tag_mapping:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )
            
            # Connect to PLC client
            if isinstance(self._plc_client, MockPLCClient):
                await self._plc_client.connect()
            
            self._is_running = True
            self._start_time = datetime.now()
            self._polling_task = asyncio.create_task(self._poll_tags())
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

            # 1. Stop external tasks
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
                self._polling_task = None

            # 2. Clear callbacks and caches
            self._state_callbacks.clear()
            self._cache.clear()
            self._state_cache.clear()
            
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

    async def _get_component_health(self) -> Dict[str, ComponentHealth]:
        """Get health status of all components."""
        try:
            components = {
                "plc_client": ComponentHealth(
                    status="ok" if self._plc_client and self._plc_client.is_connected() else "error",
                    error=None if self._plc_client and self._plc_client.is_connected() else "PLC client not connected"
                ),
                "tag_mapping": ComponentHealth(
                    status="ok" if self._tag_mapping and self._tag_mapping.is_running else "error",
                    error=None if self._tag_mapping and self._tag_mapping.is_running else "Tag mapping not running"
                ),
                "cache": ComponentHealth(
                    status="ok" if isinstance(self._cache, dict) else "error",
                    error=None if isinstance(self._cache, dict) else "Cache not initialized"
                ),
                "polling": ComponentHealth(
                    status="ok" if self._polling_task and not self._polling_task.done() else "error",
                    error=None if self._polling_task and not self._polling_task.done() else "Polling task not running"
                )
            }
            
            # Add SSH client status if configured
            if self._ssh_client:
                components["ssh_client"] = ComponentHealth(
                    status="ok" if self._ssh_client.is_connected() else "error",
                    error=None if self._ssh_client.is_connected() else "SSH client not connected"
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

    def add_state_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Register callback for state changes."""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Remove state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    async def get_tag(self, tag: str) -> Optional[Any]:
        """Get cached tag value."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )
        return self._cache.get(tag)

    async def get_state(self, state_type: str) -> Optional[Any]:
        """Get cached state."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )
        return self._state_cache.get(state_type)

    async def set_tag(self, tag: str, value: Any) -> None:
        """Set tag value."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        # Get tag mapping info
        tag_info = self._tag_mapping.get_tag_info(tag)
        if not tag_info:
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Tag not found: {tag}"
            )

        # Check if tag is mapped to PLC or SSH
        is_plc_tag = "plc_tag" in tag_info
        is_ssh_tag = tag.startswith("ssh.")

        try:
            if is_plc_tag:
                # Write to PLC
                plc_tag = tag_info["plc_tag"]
                await self._plc_client.write_tag(plc_tag, value)
                self._cache[tag] = value
                logger.debug(f"Set PLC tag {plc_tag} = {value}")
            elif is_ssh_tag and self._ssh_client:
                # Write to SSH
                ssh_tag = tag.replace("ssh.", "")  # Remove ssh. prefix
                await self._ssh_client.write_tag(ssh_tag, value)
                self._cache[tag] = value
                logger.debug(f"Set SSH tag {ssh_tag} = {value}")
            else:
                # Internal tag - just update cache
                self._cache[tag] = value
                logger.debug(f"Set internal tag {tag} = {value}")

        except Exception as e:
            error_msg = f"Failed to set tag {tag} = {value}"
            logger.error(f"{error_msg}: {str(e)}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    def get_all_tags(self) -> Dict[str, Any]:
        """Get all cached tag values."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )
        return self._cache.copy()

    async def _poll_tags(self) -> None:
        """Poll PLC tags and update cache."""
        prev_values = {}  # Track previous values to reduce logging
        consecutive_errors = 0  # Track consecutive errors for backoff
        MAX_CONSECUTIVE_ERRORS = 3  # Max errors before maximum delay
        
        while self._is_running:
            try:
                # Get all mapped PLC tags
                plc_tags = []
                internal_to_plc = {}  # Track mapping for error reporting
                for internal_tag, tag_info in self._tag_mapping._tag_map.items():
                    if tag_info.get("mapped", False) and tag_info.get("plc_tag"):
                        plc_tag = tag_info["plc_tag"]
                        plc_tags.append(plc_tag)
                        internal_to_plc[plc_tag] = internal_tag

                if not plc_tags:
                    logger.warning("No mapped PLC tags found")
                    await asyncio.sleep(self._polling["interval"])
                    continue

                # Get all tag values in one batch
                try:
                    values = await self._plc_client.get(plc_tags)
                    if not values:
                        raise ValueError("No values returned from PLC")
                        
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                except Exception as e:
                    consecutive_errors += 1
                    error_msg = f"Failed to read PLC tags: {str(e)}"
                    logger.error(error_msg)
                    
                    # Increase delay after multiple consecutive errors, up to max
                    delay = self._polling["interval"] * (2 ** min(consecutive_errors - 1, MAX_CONSECUTIVE_ERRORS))
                    logger.warning(f"Backing off for {delay} seconds after {consecutive_errors} consecutive errors")
                    await asyncio.sleep(delay)
                    continue
                
                # Update cache with new values
                for plc_tag, value in values.items():
                    internal_tag = internal_to_plc[plc_tag]
                    
                    try:
                        # Only update and log if value changed
                        if plc_tag not in prev_values or value != prev_values[plc_tag]:
                            # Store raw PLC tag value
                            self._cache[plc_tag] = value
                            # Store scaled internal tag value
                            scaled_value = self._tag_mapping.scale_value(internal_tag, value)
                            self._cache[internal_tag] = scaled_value
                            prev_values[plc_tag] = value
                            logger.debug(f"Updated tag {internal_tag} = {scaled_value} (PLC: {plc_tag} = {value})")
                            
                    except Exception as e:
                        logger.error(f"Error updating tag {internal_tag}: {str(e)}")
                        # Continue with other tags

                # Log any missing tags
                missing_tags = set(plc_tags) - set(values.keys())
                if missing_tags:
                    missing_internal = [internal_to_plc[t] for t in missing_tags]
                    logger.warning(f"Missing PLC tags: {missing_tags}")
                    logger.warning(f"Corresponding internal tags: {missing_internal}")

                # Update equipment states
                try:
                    await self._update_equipment_states()
                except Exception as e:
                    logger.error(f"Error updating equipment states: {str(e)}")
                    # Continue polling even if state update fails
                        
                await asyncio.sleep(self._polling["interval"])
                
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
                break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in polling loop: {str(e)}")
                
                # Increase delay after multiple consecutive errors, up to max
                delay = self._polling["interval"] * (2 ** min(consecutive_errors - 1, MAX_CONSECUTIVE_ERRORS))
                logger.warning(f"Backing off for {delay} seconds after {consecutive_errors} consecutive errors")
                await asyncio.sleep(delay)

    async def _update_equipment_states(self) -> None:
        """Update cached equipment states."""
        try:
            # Update gas state
            gas_state = GasState(
                main_flow=self._cache.get("gas_control.main_flow.setpoint", 0),
                main_flow_measured=self._cache.get("gas_control.main_flow.measured", 0),
                feeder_flow=self._cache.get("gas_control.feeder_flow.setpoint", 0),
                feeder_flow_measured=self._cache.get("gas_control.feeder_flow.measured", 0),
                main_valve=self._cache.get("gas_control.main_valve.open", False),
                feeder_valve=self._cache.get("gas_control.feeder_valve.open", False)
            )
            
            # Update vacuum state
            vacuum_state = VacuumState(
                chamber_pressure=self._cache.get("vacuum.chamber_pressure", 0),
                gate_valve=self._cache.get("vacuum.gate_valve.open", False),
                mech_pump=self._cache.get("vacuum.mechanical_pump.start", False),
                booster_pump=self._cache.get("vacuum.booster_pump.start", False),
                vent_valve=self._cache.get("vacuum.vent_valve", False)
            )
            
            # Update feeder state (using feeder1 as primary)
            feeder_state = FeederState(
                running=self._cache.get("feeders.feeder1.running", False),
                frequency=self._cache.get("feeders.feeder1.frequency", 0)
            )
            
            # Update deagglomerator state (using deagg1 as primary)
            deagglomerator_state = DeagglomeratorState(
                duty_cycle=self._cache.get("deagglomerators.deagg1.duty_cycle", 0)
            )
            
            # Update nozzle state
            nozzle_state = NozzleState(
                active_nozzle=2 if self._cache.get("nozzle.select", False) else 1,
                shutter_open=self._cache.get("nozzle.shutter.open", False)
            )
            
            # Update pressure state
            pressure_state = PressureState(
                chamber=self._cache.get("vacuum.chamber_pressure", 0),
                feeder=self._cache.get("pressure.feeder_pressure", 0),
                main_supply=self._cache.get("pressure.main_supply_pressure", 0),
                nozzle=self._cache.get("nozzle.pressure", 0),
                regulator=self._cache.get("pressure.regulator_pressure", 0)
            )
            
            # Update motion state
            position = Position(
                x=self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.x_position", 0),
                y=self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.y_position", 0),
                z=self._cache.get("motion.motion_control.relative_move.z_move.parameters.position", 0)
            )
            
            # Get axis statuses
            x_status = AxisStatus(
                position=position.x,
                in_position=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.status", False)),
                moving=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.in_progress", False)),
                error=not bool(self._cache.get("interlocks.motion_ready", True)),
                homed=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.status", False))
            )
            
            y_status = AxisStatus(
                position=position.y,
                in_position=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.status", False)),
                moving=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.in_progress", False)),
                error=not bool(self._cache.get("interlocks.motion_ready", True)),
                homed=bool(self._cache.get("motion.motion_control.coordinated_move.xy_move.parameters.status", False))
            )
            
            z_status = AxisStatus(
                position=position.z,
                in_position=bool(self._cache.get("motion.motion_control.relative_move.z_move.parameters.status", False)),
                moving=bool(self._cache.get("motion.motion_control.relative_move.z_move.parameters.in_progress", False)),
                error=not bool(self._cache.get("interlocks.motion_ready", True)),
                homed=bool(self._cache.get("motion.motion_control.relative_move.z_move.parameters.status", False))
            )
            
            system_status = SystemStatus(
                x_axis=x_status,
                y_axis=y_status,
                z_axis=z_status,
                module_ready=bool(self._cache.get("interlocks.motion_ready", True))
            )
            
            motion_state = MotionState(
                position=position,
                status=system_status
            )
            
            # Update hardware state
            hardware_state = HardwareState(
                motion_enabled=bool(self._cache.get("interlocks.motion_ready", True)),
                plc_connected=bool(self._cache.get("system.plc_connected", True)),
                position_valid=bool(self._cache.get("motion.position_valid", True))
            )
            
            # Update process state
            process_state = ProcessState(
                gas_flow_stable=bool(self._cache.get("process.gas_flow_stable", True)),
                powder_feed_active=bool(self._cache.get("process.powder_feed_active", False)),
                process_ready=bool(self._cache.get("process.ready", True))
            )
            
            # Update safety state
            safety_state = SafetyState(
                emergency_stop=bool(self._cache.get("safety.emergency_stop", False)),
                interlocks_ok=bool(self._cache.get("safety.interlocks_ok", True)),
                limits_ok=bool(self._cache.get("safety.limits_ok", True))
            )

            # Update equipment state
            equipment_state = EquipmentState(
                gas=gas_state,
                vacuum=vacuum_state,
                feeder=feeder_state,
                deagglomerator=deagglomerator_state,
                nozzle=nozzle_state,
                pressure=pressure_state,
                motion=motion_state,
                hardware=hardware_state,
                process=process_state,
                safety=safety_state
            )
            
            # Update state cache
            self._state_cache["equipment"] = equipment_state
            self._state_cache["gas"] = gas_state
            self._state_cache["vacuum"] = vacuum_state
            self._state_cache["feeder"] = feeder_state
            self._state_cache["deagglomerator"] = deagglomerator_state
            self._state_cache["nozzle"] = nozzle_state
            self._state_cache["pressure"] = pressure_state
            self._state_cache["motion"] = motion_state
            self._state_cache["hardware"] = hardware_state
            self._state_cache["process"] = process_state
            self._state_cache["safety"] = safety_state
            
            # Notify state change callbacks
            for callback in self._state_callbacks:
                try:
                    callback("equipment", equipment_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error updating equipment states: {str(e)}")
