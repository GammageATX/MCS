"""PLC communication client."""

from typing import Any, Dict, List, Optional
from loguru import logger
from productivity import ProductivityPLC


class PLCClient:
    """Client for communicating with Productivity PLC."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize PLC client.
        
        Args:
            config: Client configuration from communication.json
        """
        self._config = config
        self._connected = False
        
        # Extract PLC config
        plc_config = config["communication"]["hardware"]["network"]["plc"]
        self._ip = plc_config["ip"]
        self._tag_file = plc_config["tag_file"]
        self._timeout = plc_config.get("timeout", 5.0)
        self._plc: Optional[ProductivityPLC] = None
        self._tags: Dict[str, Any] = {}
        logger.info(f"Initialized PLC client for {self._ip}")

    async def connect(self) -> None:
        """Connect to PLC.
        
        Connection is established on first request.
        """
        try:
            # Create PLC instance
            self._plc = ProductivityPLC(self._ip, self._tag_file, self._timeout)
            
            # Get tag configuration and test connection with first request
            self._tags = self._plc.get_tags()
            await self._plc.get()
                
            self._connected = True
            logger.info(f"Connected to PLC at {self._ip} with {len(self._tags)} tags")
            
        except Exception as e:
            logger.error(f"Failed to connect to PLC at {self._ip}: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from PLC.
        
        Connection is closed automatically when requests stop.
        """
        self._plc = None
        self._connected = False
        logger.info(f"Disconnected from PLC at {self._ip}")

    async def read_tag(self, tag: str) -> Any:
        """Read tag value.
        
        Args:
            tag: Tag name to read
            
        Returns:
            Tag value
        """
        if not self._connected:
            raise ConnectionError("PLC not connected")
            
        if tag not in self._tags:
            raise ValueError(f"Tag '{tag}' not found in PLC")
            
        try:
            values = await self._plc.get()
            if tag not in values:
                raise ValueError(f"Tag '{tag}' not found in PLC response")
                
            return values[tag]
            
        except Exception as e:
            logger.error(f"Failed to read tag '{tag}' from PLC: {str(e)}")
            raise

    async def write_tag(self, tag: str, value: Any) -> None:
        """Write tag value.
        
        Args:
            tag: Tag name to write
            value: Value to write
        """
        if not self._connected:
            raise ConnectionError("PLC not connected")
            
        if tag not in self._tags:
            raise ValueError(f"Tag '{tag}' not found in PLC")
            
        try:
            # The library handles type validation and conversion
            await self._plc.set({tag: value})
            logger.debug(f"Wrote tag {tag} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to write tag '{tag}' = {value} to PLC: {str(e)}")
            raise

    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            Connection status
        """
        return self._connected

    async def get(self, tags: List[str]) -> Dict[str, Any]:
        """Read multiple tag values.
        
        Args:
            tags: List of tags to read
            
        Returns:
            Dict mapping tag names to values
            
        Note:
            Tags not found in PLC will be skipped with a warning
        """
        if not self._connected:
            raise ConnectionError("PLC not connected")
            
        try:
            # Get all values in one request for efficiency
            values = await self._plc.get()
            result = {}
            missing_tags = []
            
            # Filter requested tags
            for tag in tags:
                if tag not in self._tags:
                    missing_tags.append(tag)
                    continue
                    
                if tag in values:
                    result[tag] = values[tag]
                else:
                    missing_tags.append(tag)
                
            if missing_tags:
                logger.warning(f"Tags not found in PLC: {missing_tags}")
                logger.debug(f"Available PLC tags: {list(self._tags.keys())}")
                
            if not result:
                logger.error("No valid tags found in request")
                
            logger.debug(f"Read {len(result)} PLC tags")
            return result
            
        except Exception as e:
            logger.error(f"Failed to read tags from PLC: {str(e)}")
            raise
