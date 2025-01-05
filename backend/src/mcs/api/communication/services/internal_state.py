"""Internal state evaluation service."""

from typing import Dict, Any, Optional
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
        """Handle tag update from cache.
        
        Args:
            tag: Updated tag name
            value: New tag value
        """
        try:
            # Find rules that depend on this tag
            affected_states = []
            for state, rule in self._state_rules.items():
                if self._tag_affects_rule(tag, rule):
                    affected_states.append(state)
            
            # Re-evaluate affected states
            for state in affected_states:
                await self._evaluate_state(state)
                
        except Exception as e:
            logger.error(f"Failed to handle tag update: {e}")

    def _tag_affects_rule(self, tag: str, rule: Dict[str, Any]) -> bool:
        """Check if tag affects a state rule.
        
        Args:
            tag: Tag name to check
            rule: Rule definition
            
        Returns:
            bool: True if tag affects rule
        """
        if rule["type"] == "comparison":
            return tag == rule["tag"]
        elif rule["type"] == "multi_condition":
            return any(tag == c["tag"] for c in rule["conditions"])
        return False

    async def _evaluate_state(self, state: str) -> None:
        """Evaluate a single internal state.
        
        Args:
            state: State name to evaluate
        """
        try:
            rule = self._state_rules.get(state)
            if not rule:
                logger.warning(f"No rule found for state: {state}")
                return
                
            # Get current value based on rule type
            if rule["type"] == "comparison":
                tag_value = await self._tag_cache.get_tag(rule["tag"])
                if tag_value is None:
                    logger.warning(f"No value for tag: {rule['tag']}")
                    return
                    
                operator = rule.get("operator", "equal")
                if operator == "greater_than":
                    new_value = tag_value > rule["value"]
                elif operator == "less_than":
                    new_value = tag_value < rule["value"]
                elif operator == "greater_than_equal":
                    new_value = tag_value >= rule["value"]
                elif operator == "less_than_equal":
                    new_value = tag_value <= rule["value"]
                else:  # equal
                    new_value = tag_value == rule["value"]
                    
            elif rule["type"] == "multi_condition":
                values = []
                for condition in rule["conditions"]:
                    tag_value = await self._tag_cache.get_tag(condition["tag"])
                    if tag_value is None:
                        logger.warning(f"No value for tag: {condition['tag']}")
                        return
                        
                    operator = condition.get("operator", "equal")
                    if operator == "greater_than":
                        values.append(tag_value > condition["value"])
                    elif operator == "less_than":
                        values.append(tag_value < condition["value"])
                    elif operator == "greater_than_equal":
                        values.append(tag_value >= condition["value"])
                    elif operator == "less_than_equal":
                        values.append(tag_value <= condition["value"])
                    else:  # equal
                        values.append(tag_value == condition["value"])
                        
                new_value = all(values)
                
            else:
                logger.warning(f"Unknown rule type: {rule['type']}")
                return
                
            # Update state if changed
            if state not in self._internal_states or self._internal_states[state] != new_value:
                self._internal_states[state] = new_value
                logger.debug(f"Internal state {state} = {new_value} ({rule.get('description', '')})")
                
        except Exception as e:
            logger.error(f"Failed to evaluate state {state}: {e}")

    async def _evaluate_all_states(self) -> None:
        """Evaluate all internal states."""
        for state in self._state_rules:
            await self._evaluate_state(state)

    async def get_state(self, state: str) -> Optional[bool]:
        """Get current value of an internal state.
        
        Args:
            state: State name to get
            
        Returns:
            Optional[bool]: Current state value or None if not found
        """
        return self._internal_states.get(state)

    async def get_all_states(self) -> Dict[str, bool]:
        """Get all internal states.
        
        Returns:
            Dict[str, bool]: Current state values
        """
        return self._internal_states.copy()
