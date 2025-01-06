"""Tag cache service implementation."""

import asyncio
from typing import Dict, Any, Optional, Union, Callable, List, Set
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.communication.clients.mock import MockPLCClient
from mcs.api.communication.clients.plc import PLCClient
from mcs.api.communication.clients.ssh import SSHClient
from mcs.api.communication.services.tag_mapping import TagMappingService


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
        self._polling_task = None
        self._polling = None
        
        # State change callbacks
        self._state_callbacks: List[Callable[[str, Any], None]] = []
        
        # Tag subscriptions
        self._tag_subscribers: Dict[str, Set[Callable[[str, Any], None]]] = {}
        
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
            
            # Initialize internal tags with defaults
            system_defaults = self._config.get("communication", {}).get("system_defaults", {})
            for tag_name, tag_info in self._tag_mapping._tag_map.items():
                if tag_info.get("internal", False):
                    # Check for default in tag definition
                    default = tag_info.get("default")
                    if default is None:
                        # Check system defaults using tag path
                        path = tag_name.split(".")
                        current = system_defaults
                        for part in path:
                            if not isinstance(current, dict):
                                break
                            current = current.get(part, {})
                        if not isinstance(current, dict):
                            default = current
                    
                    if default is not None:
                        self._cache[tag_name] = default
                        logger.debug(f"Initialized internal tag {tag_name} with default {default}")
            
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
                    logger.debug(f"Mapped internal tag {internal_tag} -> PLC tag {plc_tag}")
            
            logger.info(f"Found {len(plc_tags)} mapped PLC tags")
            logger.debug(f"PLC tags: {plc_tags}")
            logger.debug(f"Internal mappings: {internal_to_plc}")
            
            # Get initial values
            if plc_tags:
                try:
                    values = await self._plc_client.get(plc_tags)
                    logger.debug(f"Retrieved {len(values)} initial PLC values: {values}")
                    
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
            logger.debug(f"Cache contents: {self._cache}")
            
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

            # Stop external tasks
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
                self._polling_task = None

            # Clear cache and subscriptions
            self._cache.clear()
            self._tag_subscribers.clear()
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

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            components = {}
            
            # Check critical components
            plc_connected = self._plc_client and self._plc_client.is_connected()
            tag_mapping_ok = self._tag_mapping and self._tag_mapping.is_running
            cache_ok = isinstance(self._cache, dict)
            polling_ok = self._polling_task and not self._polling_task.done()

            components = {
                "plc_client": ComponentHealth(
                    status=HealthStatus.OK if plc_connected else HealthStatus.ERROR,
                    error=None if plc_connected else "PLC client not connected"
                ),
                "tag_mapping": ComponentHealth(
                    status=HealthStatus.OK if tag_mapping_ok else HealthStatus.ERROR,
                    error=None if tag_mapping_ok else "Tag mapping not running"
                ),
                "cache": ComponentHealth(
                    status=HealthStatus.OK if cache_ok else HealthStatus.ERROR,
                    error=None if cache_ok else "Cache not initialized"
                ),
                "polling": ComponentHealth(
                    status=HealthStatus.OK if polling_ok else HealthStatus.ERROR,
                    error=None if polling_ok else "Polling task not running"
                )
            }
            
            # Add SSH client status if configured
            if self._ssh_client:
                ssh_connected = self._ssh_client.is_connected()
                components["ssh_client"] = ComponentHealth(
                    status=HealthStatus.OK if ssh_connected else HealthStatus.ERROR,
                    error=None if ssh_connected else "SSH client not connected"
                )
            
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

    async def get_tag(self, tag: str) -> Optional[Any]:
        """Get cached tag value."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )
        value = self._cache.get(tag)
        logger.debug(f"Retrieved value for tag {tag}: {value}")
        return value

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
        """Poll PLC tags periodically."""
        consecutive_errors = 0
        while True:
            try:
                # Get all mapped PLC tags
                plc_tags = []
                internal_to_plc = {}  # Track mapping for error reporting
                for internal_tag, tag_info in self._tag_mapping._tag_map.items():
                    if tag_info.get("mapped", False) and tag_info.get("plc_tag"):
                        plc_tag = tag_info["plc_tag"]
                        plc_tags.append(plc_tag)
                        internal_to_plc[plc_tag] = internal_tag
                        logger.debug(f"Polling mapped tag: {internal_tag} -> {plc_tag}")

                # Get current values
                if plc_tags:
                    values = await self._plc_client.get(plc_tags)
                    logger.debug(f"Polled values: {values}")
                    
                    # Process each value
                    for plc_tag, value in values.items():
                        internal_tag = internal_to_plc[plc_tag]
                        
                        # Check if PLC value changed
                        if plc_tag not in self._cache or self._cache[plc_tag] != value:
                            # Store raw PLC tag value
                            self._cache[plc_tag] = value
                            
                            # Scale and store internal tag value
                            scaled_value = self._tag_mapping.scale_value(internal_tag, value)
                            old_value = self._cache.get(internal_tag)
                            self._cache[internal_tag] = scaled_value
                            
                            # If internal value changed, notify subscribers and callbacks
                            if old_value != scaled_value:
                                logger.debug(f"Tag changed: {internal_tag} = {scaled_value} (PLC: {plc_tag} = {value})")
                                
                                # Notify tag subscribers
                                self._notify_tag_subscribers(internal_tag, scaled_value)
                                
                                # Check if this is a state tag and notify state callbacks
                                tag_info = self._tag_mapping._tag_map.get(internal_tag, {})
                                if tag_info.get("state_type"):
                                    self._notify_state_callbacks(tag_info["state_type"], scaled_value)

                # Reset error counter on success
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error polling tags: {str(e)}")
                
                # Exponential backoff on consecutive errors
                delay = min(30, 2 ** consecutive_errors)
                logger.warning(f"Backing off for {delay} seconds after {consecutive_errors} consecutive errors")
                await asyncio.sleep(delay)
                continue
            
            # Wait for next poll interval
            await asyncio.sleep(self._polling.get("interval", 1.0))

    def add_state_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Add callback for state changes.
        
        Args:
            callback: Function to call when state changes. Takes state type and new state.
        """
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)
            logger.debug(f"Added state callback: {callback}")

    def remove_state_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Remove state change callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)
            logger.debug(f"Removed state callback: {callback}")

    def _notify_state_callbacks(self, state_type: str, state: Any) -> None:
        """Notify all registered callbacks of state change.
        
        Args:
            state_type: Type of state that changed
            state: New state value
        """
        for callback in self._state_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(state_type, state))
                else:
                    callback(state_type, state)
            except Exception as e:
                logger.error(f"Error in state callback: {str(e)}")

    async def subscribe(self, callback: Callable[[str, Any], None], tag: Optional[str] = None) -> None:
        """Subscribe to tag changes.
        
        Args:
            callback: Function to call when tag changes. Takes tag name and new value.
            tag: Optional specific tag to subscribe to. If None, subscribes to all changes.
        """
        if tag:
            # Subscribe to specific tag
            if tag not in self._tag_subscribers:
                self._tag_subscribers[tag] = set()
            self._tag_subscribers[tag].add(callback)
            logger.debug(f"Added subscriber for tag {tag}: {callback}")
        else:
            # Subscribe to all tags
            self._tag_subscribers["*"] = self._tag_subscribers.get("*", set())
            self._tag_subscribers["*"].add(callback)
            logger.debug(f"Added subscriber for all tags: {callback}")

    async def unsubscribe(self, callback: Callable[[str, Any], None], tag: Optional[str] = None) -> None:
        """Unsubscribe from tag changes.
        
        Args:
            callback: Callback to remove
            tag: Optional specific tag to unsubscribe from. If None, unsubscribes from all.
        """
        if tag:
            # Unsubscribe from specific tag
            if tag in self._tag_subscribers and callback in self._tag_subscribers[tag]:
                self._tag_subscribers[tag].remove(callback)
                if not self._tag_subscribers[tag]:
                    del self._tag_subscribers[tag]
                logger.debug(f"Removed subscriber for tag {tag}: {callback}")
        else:
            # Unsubscribe from all tags
            if "*" in self._tag_subscribers and callback in self._tag_subscribers["*"]:
                self._tag_subscribers["*"].remove(callback)
                if not self._tag_subscribers["*"]:
                    del self._tag_subscribers["*"]
                logger.debug(f"Removed subscriber for all tags: {callback}")

    def _notify_tag_subscribers(self, tag: str, value: Any) -> None:
        """Notify subscribers of tag change.
        
        Args:
            tag: Tag that changed
            value: New value
        """
        # Create task for each subscriber to avoid blocking
        if tag in self._tag_subscribers:
            for callback in self._tag_subscribers[tag]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(tag, value))
                    else:
                        callback(tag, value)
                except Exception as e:
                    logger.error(f"Error in tag subscriber for {tag}: {str(e)}")
        
        # Notify global subscribers
        if "*" in self._tag_subscribers:
            for callback in self._tag_subscribers["*"]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(tag, value))
                    else:
                        callback(tag, value)
                except Exception as e:
                    logger.error(f"Error in global tag subscriber: {str(e)}")
