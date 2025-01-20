"""Tag mapping service implementation."""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import status
from fastapi.exceptions import HTTPException
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health


def load_config() -> Dict[str, Any]:
    """Load tag mapping configuration.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config_path = os.path.join("backend", "config", "tags.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r") as f:
        return json.load(f)


class TagMappingService:
    """Service for mapping between internal tag names and PLC tags."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize tag mapping service.
        
        Args:
            config: Service configuration
        """
        self._service_name = "tag_mapping"
        self._version = config["communication"]["services"]["tag_mapping"]["version"]
        self._is_running = False
        self._start_time = None
        self._config = config
        self._tag_map: Dict[str, Dict[str, Any]] = {}
        
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

    def _load_config(self) -> None:
        """Load tag mapping configuration."""
        try:
            # Load tag configuration from JSON file
            config_path = os.path.join("backend", "config", "tags.json")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Tag configuration file not found: {config_path}")
                
            with open(config_path, "r") as f:
                tag_config = json.load(f)
            
            # Process tag mappings from hierarchical structure
            self._tag_map.clear()
            for group_name, group_tags in tag_config.get("tag_groups", {}).items():
                self._process_tag_group(group_name, group_tags)
                
            logger.info(f"Loaded {len(self._tag_map)} tag mappings")
            
        except Exception as e:
            error_msg = f"Failed to load tag configuration: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )
            
    def _process_tag_group(self, group_name: str, group_data: Dict[str, Any]) -> None:
        """Process a tag group and add mappings."""
        logger.info(f"Processing tag group {group_name}")
        
        # Process each tag in the group
        for tag_name, tag_data in group_data.items():
            # Skip if tag_data is None
            if tag_data is None:
                continue
                
            # Check if this is a subgroup or leaf node
            if isinstance(tag_data, dict):
                # Skip if this is a mapped tag (leaf node)
                if tag_data.get("mapped", False):
                    tag_path = f"{group_name}.{tag_name}"
                    logger.debug(f"Processing tag {tag_path} with data: {tag_data}")
                    
                    # Create tag mapping
                    mapping = {
                        "type": tag_data.get("type"),
                        "access": tag_data.get("access"),
                        "mapped": tag_data.get("mapped", False),
                        "internal": tag_data.get("internal", False),
                        "plc_tag": tag_data.get("plc_tag"),
                        "description": tag_data.get("description"),
                        "scaling": tag_data.get("scaling"),
                        "range": tag_data.get("range"),
                        "unit": tag_data.get("unit"),
                        "default": tag_data.get("default")
                    }
                    
                    # Add mapping
                    self._tag_map[tag_path] = mapping
                    logger.debug(f"Added tag mapping: {tag_path} -> {mapping}")
                else:
                    # This is a subgroup, recursively process it
                    logger.debug(f"Found subgroup {tag_name} in {group_name}")
                    subgroup_name = f"{group_name}.{tag_name}"
                    self._process_tag_group(subgroup_name, tag_data)

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Load tag configuration
            self._load_config()
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

            if not self._tag_map:
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
            
            # 1. Clear tag mappings
            self._tag_map.clear()
            
            # 2. Reset service state
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
            config_file = os.path.join("backend", "config", "tags.json")
            config_exists = os.path.exists(config_file)
            mappings_loaded = len(self._tag_map) > 0

            components = {
                "config": ComponentHealth(
                    status=HealthStatus.OK if config_exists else HealthStatus.ERROR,
                    error=None if config_exists else "Tag configuration file not found"
                ),
                "mapping": ComponentHealth(
                    status=HealthStatus.OK if mappings_loaded else HealthStatus.ERROR,
                    error=None if mappings_loaded else "No tag mappings loaded",
                    details={"total_tags": len(self._tag_map)}
                )
            }
            
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
            
            # Overall status is ERROR if any component is in error
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

    def get_plc_tag(self, internal_tag: str) -> Optional[str]:
        """Get PLC tag name for internal tag."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        logger.debug(f"Looking up PLC tag for {internal_tag}")
        if internal_tag not in self._tag_map:
            logger.error(f"Tag not found in mapping: {internal_tag}")
            return None
            
        tag_info = self._tag_map[internal_tag]
        logger.debug(f"Found tag info: {tag_info}")
        if not tag_info.get("mapped", False):
            logger.debug(f"Tag is not mapped: {internal_tag}")
            return None
            
        plc_tag = tag_info.get("plc_tag")
        if not plc_tag:
            logger.error(f"No PLC tag defined for: {internal_tag}")
            return None
            
        logger.debug(f"Mapped {internal_tag} to PLC tag: {plc_tag}")
        return plc_tag

    def get_internal_tag(self, plc_tag: str) -> Optional[str]:
        """Get internal tag name for PLC tag."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        # Search for PLC tag in mappings
        for internal_name, tag_info in self._tag_map.items():
            if tag_info.get("mapped", False) and tag_info.get("plc_tag") == plc_tag:
                return internal_name
                
        logger.error(f"No mapping found for PLC tag: {plc_tag}")
        return None

    def get_tag_type(self, internal_tag: str) -> Optional[str]:
        """Get tag type for internal tag."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        if internal_tag not in self._tag_map:
            logger.error(f"Tag not found in mapping: {internal_tag}")
            return None
            
        return self._tag_map[internal_tag].get("type")

    def get_tag_access(self, internal_tag: str) -> Optional[str]:
        """Get tag access mode."""
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        if internal_tag not in self._tag_map:
            return None
            
        return self._tag_map[internal_tag].get("access")

    def get_tag_info(self, internal_name: str) -> Optional[Dict[str, Any]]:
        """Get all tag information."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if internal_name not in self._tag_map:
                logger.warning(f"Tag not found: {internal_name}")
                return None

            return self._tag_map[internal_name]

        except Exception as e:
            error_msg = f"Failed to get tag info for {internal_name}: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    def scale_value(self, internal_tag: str, raw_value: Any) -> Any:
        """Scale raw PLC value to internal value based on tag configuration.
        
        Args:
            internal_tag: Internal tag name
            raw_value: Raw PLC value
            
        Returns:
            Scaled value
            
        Raises:
            HTTPException: If service not running or tag not found
        """
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=f"{self.service_name} service not running"
            )

        # Validate tag exists
        if internal_tag not in self._tag_map:
            error_msg = f"Tag not found in mapping: {internal_tag}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=error_msg
            )

        try:
            tag_info = self._tag_map[internal_tag]
            scaling = tag_info.get("scaling")

            if not scaling:
                return raw_value

            # Validate raw value type
            if not isinstance(raw_value, (int, float)):
                error_msg = f"Invalid raw value type for {internal_tag}: {type(raw_value)}"
                logger.error(error_msg)
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=error_msg
                )

            if scaling == "12bit_dac":
                # Validate raw value range
                if not 0 <= raw_value <= 4095:
                    error_msg = f"Raw value {raw_value} out of range for 12-bit DAC"
                    logger.error(error_msg)
                    raise create_error(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=error_msg
                    )
                    
                # Get range with validation
                range_info = tag_info.get("range")
                if not range_info or not isinstance(range_info, list) or len(range_info) != 2:
                    error_msg = f"Invalid range configuration for {internal_tag}"
                    logger.error(error_msg)
                    raise create_error(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=error_msg
                    )
                    
                range_min, range_max = range_info
                return range_min + (range_max - range_min) * (raw_value / 4095.0)

            elif scaling == "12bit_linear":
                # Already scaled by PLC, just return as is
                return raw_value

            else:
                error_msg = f"Unknown scaling type {scaling} for tag {internal_tag}"
                logger.warning(error_msg)
                return raw_value

        except Exception as e:
            if not isinstance(e, HTTPException):
                error_msg = f"Failed to scale value for {internal_tag}: {str(e)}"
                logger.error(error_msg)
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=error_msg
                )
            raise
