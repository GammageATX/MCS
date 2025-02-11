"""Internal state evaluation service."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
from fastapi import status

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health


class InternalStateService:
    """Service for evaluating internal states from PLC tags."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize internal state service.
        
        Args:
            config: Service configuration
        """
        self._service_name = "internal_state"
        self._config = config
        
        # Get version from config, default to 1.0.0 if not found
        try:
            self._version = config.get("communication", {}).get("services", {}).get("internal_state", {}).get("version", "1.0.0")
        except Exception as e:
            logger.warning(f"Failed to get version from config, using default: {e}")
            self._version = "1.0.0"
            
        self._is_running = False
        self._start_time = None
        
        # State tracking
        self._internal_states = {}
        self._state_rules = {}
        self._tag_cache = None
        self._tag_mapping = None
        
        # Add callback lists
        self._equipment_state_callbacks = []
        self._motion_state_callbacks = []
        
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

    def set_tag_cache(self, tag_cache_service: Any) -> None:
        """Set tag cache service.
        
        Args:
            tag_cache_service: TagCacheService instance
        """
        self._tag_cache = tag_cache_service

    def set_tag_mapping(self, tag_mapping_service: Any) -> None:
        """Set tag mapping service.
        
        Args:
            tag_mapping_service: TagMappingService instance
        """
        self._tag_mapping = tag_mapping_service

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if not self._tag_cache:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Tag cache service not set"
                )
            if not self._tag_mapping:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Tag mapping service not set"
                )
            
            # Load state evaluation rules
            await self._load_state_rules()
            
            # Subscribe to tag cache updates
            await self._tag_cache.subscribe(self._on_tag_update)
            
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_state_rules(self) -> None:
        """Load state evaluation rules from config."""
        try:
            # Get rules from already loaded config
            self._state_rules = self._config.get("internal_states", {}).get("rules", {})
            if not self._state_rules:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="No internal state rules found in config"
                )
                
            logger.info(f"Loaded {len(self._state_rules)} internal state rules")
            
        except Exception as e:
            error_msg = f"Failed to load state rules: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                logger.warning(f"{self.service_name} service already running")
                return
                
            self._is_running = True
            self._start_time = datetime.now()
            
            # Initialize internal states
            await self._evaluate_all_states()
            
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
                logger.warning(f"{self.service_name} service not running")
                return
                
            # Unsubscribe from tag cache
            if self._tag_cache:
                await self._tag_cache.unsubscribe(self._on_tag_update)
            
            self._is_running = False
            self._start_time = None
            self._internal_states.clear()
            
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
            components = {}
            
            # Check tag cache connection
            tag_cache_ok = self._tag_cache is not None and self._tag_cache.is_running
            components["tag_cache"] = ComponentHealth(
                status=HealthStatus.OK if tag_cache_ok else HealthStatus.ERROR,
                error=None if tag_cache_ok else "Tag cache not connected",
                details={"connected": tag_cache_ok}
            )
            
            # Check tag mapping connection
            tag_mapping_ok = self._tag_mapping is not None
            components["tag_mapping"] = ComponentHealth(
                status=HealthStatus.OK if tag_mapping_ok else HealthStatus.ERROR,
                error=None if tag_mapping_ok else "Tag mapping not connected",
                details={"connected": tag_mapping_ok}
            )
            
            # Check state rules
            rules_ok = bool(self._state_rules)
            components["state_rules"] = ComponentHealth(
                status=HealthStatus.OK if rules_ok else HealthStatus.ERROR,
                error=None if rules_ok else "No state rules loaded",
                details={"rule_count": len(self._state_rules)}
            )
            
            # Overall status
            overall_status = (
                HealthStatus.OK
                if all(c.status == HealthStatus.OK for c in components.values())
                else HealthStatus.ERROR
            )
            
            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error=None if overall_status == HealthStatus.OK else "Component failure",
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg)

    async def _on_tag_update(self, tag: str, value: Any) -> None:
        """Handle tag update from tag cache.
        
        Args:
            tag: Updated tag name
            value: New tag value
        """
        # Re-evaluate states and notify callbacks if values changed
        old_equipment_states = await self.get_equipment_states()
        old_motion_states = await self.get_motion_states()
        
        await self._evaluate_all_states()
        
        new_equipment_states = await self.get_equipment_states()
        new_motion_states = await self.get_motion_states()
        
        if new_equipment_states != old_equipment_states:
            await self._notify_equipment_state_callbacks()
            
        if new_motion_states != old_motion_states:
            await self._notify_motion_state_callbacks()

    def _tag_affects_rule(self, tag: str, rule: Dict[str, Any]) -> bool:
        """Check if tag affects a state rule.
        
        Args:
            tag: Tag name to check
            rule: Rule definition
            
        Returns:
            bool: True if tag affects rule
        """
        if rule["type"] == "comparison":
            rule_tag = rule["tag"]
            if "{1|2}" in rule_tag:
                # Check if tag matches either variant
                return tag == rule_tag.replace("{1|2}", "1") or tag == rule_tag.replace("{1|2}", "2")
            return tag == rule_tag
        elif rule["type"] == "multi_condition":
            return any(
                tag == c["tag"].replace("{1|2}", "1") or tag == c["tag"].replace("{1|2}", "2")
                if "{1|2}" in c["tag"]
                else tag == c["tag"]
                for c in rule["conditions"]
            )
        return False

    async def _get_tag_value(self, tag_pattern: str) -> Any:
        """Get tag value, handling wildcard patterns.
        
        Args:
            tag_pattern: Tag pattern that may include {1|2} wildcards
            
        Returns:
            Tag value or None if not found
        """
        # First check if this is an internal state
        if tag_pattern in self._internal_states:
            return self._internal_states[tag_pattern]
            
        # Handle {1|2} pattern
        if "{1|2}" in tag_pattern:
            # Try both variants
            for i in [1, 2]:
                tag = tag_pattern.replace("{1|2}", str(i))
                try:
                    value = await self._tag_cache.get_tag(tag)
                    if value is not None:
                        return value
                except Exception as e:
                    logger.warning(f"Error getting tag {tag}: {e}")
                    continue
            logger.warning(f"No value found for wildcard tag pattern: {tag_pattern}")
            return None
        else:
            try:
                value = await self._tag_cache.get_tag(tag_pattern)
                if value is None:
                    logger.warning(f"No value found for tag: {tag_pattern}")
                return value
            except Exception as e:
                logger.warning(f"Error getting tag {tag_pattern}: {e}")
                return None

    async def _resolve_value(self, value: Any) -> Any:
        """Resolve a value that may contain a placeholder.
        
        Args:
            value: Value to resolve, may be a placeholder like {tag.name}
            
        Returns:
            Resolved value
        """
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            # This is a placeholder, get the actual value from tag cache
            tag = value[1:-1]  # Remove { and }
            resolved = await self._tag_cache.get_tag(tag)
            if resolved is None:
                logger.warning(f"Could not resolve placeholder {value} - tag {tag} not found")
                return None
            logger.debug(f"Resolved placeholder {value} -> {resolved}")
            return resolved
        return value

    async def _evaluate_state(self, state: str) -> None:
        """Evaluate a single internal state.
        
        Args:
            state: State name to evaluate
        """
        try:
            rule = self._state_rules.get(state)
            if not rule:
                logger.warning(f"No rule found for state: {state}")
                self._internal_states[state] = False
                return
                
            # Get current value based on rule type
            if rule["type"] == "comparison":
                tag_value = await self._get_tag_value(rule["tag"])
                if tag_value is None:
                    logger.warning(f"No value for tag: {rule['tag']}, setting state {state} to False")
                    self._internal_states[state] = False
                    return
                    
                # Convert values to float for numeric comparisons
                try:
                    tag_value = float(tag_value)
                    compare_value = await self._resolve_value(rule["value"])
                    if compare_value is None:
                        logger.warning(f"No comparison value for state {state}, setting to False")
                        self._internal_states[state] = False
                        return
                    compare_value = float(compare_value)
                except (TypeError, ValueError) as e:
                    logger.error(f"Failed to convert values for comparison: {e}, setting state {state} to False")
                    self._internal_states[state] = False
                    return
                    
                operator = rule.get("operator", "equal")
                if operator == "greater_than":
                    new_value = tag_value > compare_value
                elif operator == "less_than":
                    new_value = tag_value < compare_value
                elif operator == "greater_than_equal":
                    new_value = tag_value >= compare_value
                elif operator == "less_than_equal":
                    new_value = tag_value <= compare_value
                else:  # equal
                    new_value = tag_value == compare_value
                    
            elif rule["type"] == "multi_condition":
                values = []
                for condition in rule["conditions"]:
                    tag_value = await self._get_tag_value(condition["tag"])
                    if tag_value is None:
                        logger.warning(f"No value for tag: {condition['tag']}, setting state {state} to False")
                        self._internal_states[state] = False
                        return
                        
                    # Convert values to float for numeric comparisons
                    try:
                        tag_value = float(tag_value)
                        compare_value = await self._resolve_value(condition["value"])
                        if compare_value is None:
                            logger.warning(f"No comparison value for condition in state {state}, setting to False")
                            self._internal_states[state] = False
                            return
                        compare_value = float(compare_value)
                    except (TypeError, ValueError) as e:
                        logger.error(f"Failed to convert values for comparison: {e}, setting state {state} to False")
                        self._internal_states[state] = False
                        return
                        
                    operator = condition.get("operator", "equal")
                    if operator == "greater_than":
                        values.append(tag_value > compare_value)
                    elif operator == "less_than":
                        values.append(tag_value < compare_value)
                    elif operator == "greater_than_equal":
                        values.append(tag_value >= compare_value)
                    elif operator == "less_than_equal":
                        values.append(tag_value <= compare_value)
                    else:  # equal
                        values.append(tag_value == compare_value)
                
                new_value = all(values)

            elif rule["type"] == "all":
                # All rule type checks if all specified tags are True
                values = []
                for tag in rule["tags"]:
                    tag_value = await self._get_tag_value(tag)
                    if tag_value is None:
                        logger.warning(f"No value for tag: {tag}, setting state {state} to False")
                        self._internal_states[state] = False
                        return
                    values.append(bool(tag_value))
                new_value = all(values)
                
            else:
                logger.warning(f"Unknown rule type: {rule['type']}, setting state {state} to False")
                self._internal_states[state] = False
                return
                
            # Update state if changed
            if state not in self._internal_states or self._internal_states[state] != new_value:
                self._internal_states[state] = new_value
                logger.debug(f"Internal state {state} = {new_value} ({rule.get('description', '')})")
                
        except Exception as e:
            logger.error(f"Failed to evaluate state {state}: {e}, setting to False")
            self._internal_states[state] = False

    def _is_base_state(self, state: str) -> bool:
        """Check if a state only depends on PLC tags (not other states)."""
        rule = self._state_rules[state]
        if rule["type"] == "comparison":
            return rule["tag"] not in self._state_rules
        elif rule["type"] == "multi_condition":
            return all(c["tag"] not in self._state_rules for c in rule["conditions"])
        elif rule["type"] == "all":
            return all(tag not in self._state_rules for tag in rule["tags"])
        return True  # Unknown rule types are treated as base states

    async def _evaluate_all_states(self) -> None:
        """Evaluate all internal states in dependency order."""
        # First evaluate states that only depend on PLC tags
        base_states = [
            state for state in self._state_rules
            if self._is_base_state(state)
        ]
        
        for state in base_states:
            await self._evaluate_state(state)
            
        # Then evaluate states that depend on other states
        dependent_states = [state for state in self._state_rules if state not in base_states]
        
        for state in dependent_states:
            await self._evaluate_state(state)

    async def get_state(self, state: str) -> Optional[bool]:
        """Get current value of an internal state.
        
        Args:
            state: State name to get
            
        Returns:
            Optional[bool]: Current state value or False if not found
        """
        if not self.is_running:
            logger.warning(f"Service not running, returning False for state: {state}")
            return False
            
        value = self._internal_states.get(state)
        if value is None:
            logger.warning(f"State {state} not found or not yet evaluated, returning False")
            return False
            
        return value

    async def get_all_states(self) -> Dict[str, bool]:
        """Get all internal states.
        
        Returns:
            Dict[str, bool]: Current state values
        """
        return self._internal_states.copy()

    async def get_equipment_states(self) -> Dict[str, bool]:
        """Get all equipment-related internal states.
        
        Returns:
            Dict[str, bool]: Equipment-related internal states
        """
        if not self.is_running:
            logger.warning("Service not running, returning empty equipment states")
            return {}
            
        # Filter states that are equipment-related
        equipment_states = {
            state: value
            for state, value in self._internal_states.items()
            if state in [
                "gas_flow_stable",
                "powder_feed_active",
                "process_ready",
                "pressures_stable",
                "flows_stable",
                "powder_feed_on"
            ]
        }
        return equipment_states

    async def get_equipment_state(self, state_name: str) -> Optional[bool]:
        """Get single equipment-related internal state.
        
        Args:
            state_name: Name of internal state to get
            
        Returns:
            Optional[bool]: Current state value or None if not found
        """
        if not self.is_running:
            logger.warning(f"Service not running, returning None for equipment state: {state_name}")
            return None
            
        if state_name not in [
            "gas_flow_stable",
            "powder_feed_active",
            "process_ready",
            "pressures_stable",
            "flows_stable",
            "powder_feed_on"
        ]:
            logger.warning(f"State {state_name} is not an equipment state")
            return None
            
        return self._internal_states.get(state_name)

    async def get_motion_states(self) -> Dict[str, bool]:
        """Get all motion-related internal states.
        
        Returns:
            Dict[str, bool]: Motion-related internal states
        """
        if not self.is_running:
            logger.warning("Service not running, returning empty motion states")
            return {}
            
        # Filter states that are motion-related
        motion_states = {
            state: value
            for state, value in self._internal_states.items()
            if state in [
                "motion_enabled",
                "at_valid_position",
                "homing_complete",
                "axes_referenced",
                "motion_error"
            ]
        }
        return motion_states

    async def get_motion_state(self, state_name: str) -> Optional[bool]:
        """Get single motion-related internal state.
        
        Args:
            state_name: Name of internal state to get
            
        Returns:
            Optional[bool]: Current state value or None if not found
        """
        if not self.is_running:
            logger.warning(f"Service not running, returning None for motion state: {state_name}")
            return None
            
        if state_name not in [
            "motion_enabled",
            "at_valid_position",
            "homing_complete",
            "axes_referenced",
            "motion_error"
        ]:
            logger.warning(f"State {state_name} is not a motion state")
            return None
            
        return self._internal_states.get(state_name)

    def on_equipment_state_changed(self, callback: Callable[[Dict[str, bool]], None]) -> None:
        """Register callback for equipment state changes.
        
        Args:
            callback: Function to call with updated equipment states
        """
        self._equipment_state_callbacks.append(callback)
        
    def remove_equipment_state_changed_callback(self, callback: Callable[[Dict[str, bool]], None]) -> None:
        """Remove equipment state change callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._equipment_state_callbacks:
            self._equipment_state_callbacks.remove(callback)
            
    def on_motion_state_changed(self, callback: Callable[[Dict[str, bool]], None]) -> None:
        """Register callback for motion state changes.
        
        Args:
            callback: Function to call with updated motion states
        """
        self._motion_state_callbacks.append(callback)
        
    def remove_motion_state_changed_callback(self, callback: Callable[[Dict[str, bool]], None]) -> None:
        """Remove motion state change callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._motion_state_callbacks:
            self._motion_state_callbacks.remove(callback)
            
    async def _notify_equipment_state_callbacks(self) -> None:
        """Notify equipment state callbacks of current states."""
        states = await self.get_equipment_states()
        for callback in self._equipment_state_callbacks:
            try:
                callback(states)
            except Exception as e:
                logger.error(f"Error in equipment state callback: {e}")
                
    async def _notify_motion_state_callbacks(self) -> None:
        """Notify motion state callbacks of current states."""
        states = await self.get_motion_states()
        for callback in self._motion_state_callbacks:
            try:
                callback(states)
            except Exception as e:
                logger.error(f"Error in motion state callback: {e}")
