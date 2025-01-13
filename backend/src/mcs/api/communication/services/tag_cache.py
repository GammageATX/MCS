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
        
        # Track PLC vs SSH tags
        self._plc_tags = []
        self._ssh_tags = []
        
        # State change callbacks
        self._state_callbacks: List[Callable[[str, Any], None]] = []
        
        # Tag subscriptions
        self._tag_subscribers: Dict[str, Set[Callable[[str, Any], None]]] = {}
        
        # Track logged tags to avoid duplicate debug messages
        self._logged_tag_mappings: Set[str] = set()
        self._logged_tag_changes: Set[str] = set()
        
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
            
            # Connect SSH client if available
            if self._ssh_client:
                logger.info("Connecting SSH client")
                await self._ssh_client.connect()
            
            # Categorize tags as PLC or SSH
            internal_to_plc = {}  # Track mapping for error reporting
            plc_to_internal = {}  # Track all internal tags for each PLC tag
            internal_to_ssh = {}  # Track mapping for SSH tags
            ssh_to_internal = {}  # Track all internal tags for each SSH tag
            
            for internal_tag, tag_info in self._tag_mapping._tag_map.items():
                if tag_info.get("mapped", False) and tag_info.get("plc_tag"):
                    plc_tag = tag_info["plc_tag"]
                    
                    # Check if it's a P-variable (SSH) or PLC tag
                    # P-variables start with P followed by a number
                    if plc_tag.startswith("P") and len(plc_tag) > 1 and plc_tag[1].isdigit():
                        if not self._ssh_client:
                            logger.warning(f"SSH tag {plc_tag} found but no SSH client available")
                            continue
                            
                        self._ssh_tags.append(plc_tag)
                        internal_to_ssh[plc_tag] = internal_tag
                        if plc_tag not in ssh_to_internal:
                            ssh_to_internal[plc_tag] = []
                        ssh_to_internal[plc_tag].append(internal_tag)
                        logger.debug(f"Mapped internal tag {internal_tag} -> SSH tag {plc_tag}")
                    else:
                        self._plc_tags.append(plc_tag)
                        internal_to_plc[plc_tag] = internal_tag
                        if plc_tag not in plc_to_internal:
                            plc_to_internal[plc_tag] = []
                        plc_to_internal[plc_tag].append(internal_tag)
                        logger.debug(f"Mapped internal tag {internal_tag} -> PLC tag {plc_tag}")
            
            logger.info(f"Found {len(self._plc_tags)} PLC tags and {len(self._ssh_tags)} SSH tags")
            
            # Get initial PLC values
            if self._plc_tags:
                try:
                    values = await self._plc_client.get(self._plc_tags)
                    logger.debug(f"Retrieved {len(values)} initial PLC values: {values}")
                    
                    # Store both PLC and internal tag values
                    for plc_tag, value in values.items():
                        # Store raw PLC tag value
                        self._cache[plc_tag] = value
                        # Store scaled internal tag values
                        for internal_tag in plc_to_internal[plc_tag]:
                            scaled_value = self._tag_mapping.scale_value(internal_tag, value)
                            self._cache[internal_tag] = scaled_value
                            logger.debug(f"Initialized {internal_tag} = {scaled_value} (PLC: {plc_tag} = {value})")
                        
                except Exception as e:
                    logger.error(f"Failed to get initial PLC values: {e}")
                    raise
            
            # Get initial SSH values
            if self._ssh_tags and self._ssh_client:
                try:
                    values = await self._ssh_client.get(self._ssh_tags)
                    logger.debug(f"Retrieved {len(values)} initial SSH values: {values}")
                    
                    # Store both SSH and internal tag values
                    for ssh_tag, value in values.items():
                        # Store raw SSH tag value
                        self._cache[ssh_tag] = value
                        # Store scaled internal tag values
                        for internal_tag in ssh_to_internal[ssh_tag]:
                            scaled_value = self._tag_mapping.scale_value(internal_tag, value)
                            self._cache[internal_tag] = scaled_value
                            logger.debug(f"Initialized {internal_tag} = {scaled_value} (SSH: {ssh_tag} = {value})")
                        
                except Exception as e:
                    logger.error(f"Failed to get initial SSH values: {e}")
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
            
            # Add SSH client status if configured (non-critical)
            if self._ssh_client:
                ssh_connected = self._ssh_client.is_connected()
                components["ssh_client"] = ComponentHealth(
                    status=HealthStatus.OK if ssh_connected else HealthStatus.WARN,
                    error=None if ssh_connected else "SSH client not connected"
                )
            
            # Overall status is ERROR if any critical component is in error
            # SSH client is non-critical, so its status doesn't affect overall health
            critical_components = ["plc_client", "tag_mapping", "cache", "polling"]
            overall_status = HealthStatus.ERROR if any(
                components[c].status == HealthStatus.ERROR for c in critical_components
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
            
        # Check if tag exists in mapping
        tag_info = self._tag_mapping.get_tag_info(tag)
        if not tag_info:
            logger.warning(f"Tag not found in mapping: {tag}")
            return None
            
        # Get value from cache
        value = self._cache.get(tag)
        if value is None:
            logger.warning(f"Tag not found in cache: {tag}")
            return None
            
        logger.debug(f"Retrieved value for tag {tag}: {value}")
        return value

    async def set_tag(self, internal_tag: str, value: Any) -> None:
        """Set tag value.
        
        Args:
            internal_tag: Internal tag name
            value: Value to set
        """
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        try:
            # Get mapped tag
            plc_tag = self._tag_mapping.get_plc_tag(internal_tag)
            if not plc_tag:
                raise ValueError(f"No mapped tag for {internal_tag}")

            # Route to appropriate client - P-variables start with P followed by a number
            if plc_tag.startswith("P") and len(plc_tag) > 1 and plc_tag[1].isdigit():
                if not self._ssh_client:
                    raise RuntimeError("SSH client not available")
                await self._ssh_client.write_tag(plc_tag, value)
                # Immediately read back the value to confirm and update cache
                try:
                    new_value = await self._ssh_client.read_tag(plc_tag)
                    self._cache[plc_tag] = new_value
                    self._cache[internal_tag] = self._tag_mapping.scale_value(internal_tag, new_value)
                    self._notify_tag_subscribers(internal_tag, value)
                except Exception as e:
                    logger.error(f"Failed to read back SSH tag {plc_tag}: {e}")
            else:
                await self._plc_client.write_tag(plc_tag, value)
                # Cache will be updated on next poll
            
            logger.debug(f"Set {internal_tag} ({plc_tag}) = {value}")
            
        except Exception as e:
            error_msg = f"Failed to set tag {internal_tag}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
        """Background task to poll tag values."""
        try:
            interval = self._polling["interval"]
            batch_size = self._polling["batch_size"]
            
            while True:
                try:
                    # Only poll PLC tags
                    if self._plc_tags:
                        try:
                            # Split tags into batches
                            for i in range(0, len(self._plc_tags), batch_size):
                                batch = self._plc_tags[i:i + batch_size]
                                values = await self._plc_client.get(batch)
                                for tag, value in values.items():
                                    if tag in self._cache and self._cache[tag] != value:
                                        self._cache[tag] = value
                                        self._notify_tag_subscribers(tag, value)
                        except Exception as e:
                            logger.error(f"Failed to poll PLC tags: {e}")
                    
                    await asyncio.sleep(interval)
                    
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in tag polling: {e}")
                    await asyncio.sleep(interval)
                    
        except asyncio.CancelledError:
            logger.info("Tag polling stopped")
            raise
        except Exception as e:
            logger.error(f"Tag polling failed: {e}")
            raise

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
