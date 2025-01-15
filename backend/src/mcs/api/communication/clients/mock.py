"""Mock client that simulates PLC behavior."""

import asyncio
import json
from typing import Any, Dict, List
from pathlib import Path
from loguru import logger
import random


class MockPLCClient:
    """Mock client that simulates PLC behavior."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock client."""
        self._connected = False
        self._config = config
        
        # Load mock data
        mock_data_path = Path("backend/config/mock_data.json")
        if not mock_data_path.exists():
            logger.warning(f"Mock data file not found: {mock_data_path}")
            self._plc_tags = {}
        else:
            with open(mock_data_path) as f:
                data = json.load(f)
                # Extract PLC tags from inside mock_data object
                self._plc_tags = data["mock_data"]  # This should exist, no need for get()
            logger.info(f"Loaded mock data from {mock_data_path}")
            
        logger.info(f"Mock client initialized with {len(self._plc_tags)} tags")
        logger.debug(f"Available mock tags: {list(self._plc_tags.keys())}")

    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            Connection status
        """
        return self._connected

    async def connect(self) -> None:
        """Simulate connection."""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self._connected = True
        self._running = True
        
        # Start background task to simulate tag updates
        self._update_task = asyncio.create_task(self._simulate_updates())
        logger.info("Mock client connected")

    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            
        self._connected = False
        logger.info("Mock client disconnected")

    async def read_tag(self, tag: str) -> Any:
        """Read mock tag value.
        
        Args:
            tag: Tag name to read
            
        Returns:
            Mock tag value
            
        Raises:
            KeyError: If tag not found in mock data
        """
        if not self._connected:
            raise ConnectionError("Mock client not connected")
            
        # Check if tag exists
        if tag not in self._plc_tags:
            logger.warning(f"Tag not found in mock data: {tag}")
            raise KeyError(f"Tag not found: {tag}")
            
        value = self._plc_tags[tag]
        logger.debug(f"Read mock tag {tag} = {value}")
        return value

    async def write_tag(self, tag: str, value: Any) -> None:
        """Write mock tag value."""
        if not self._connected:
            raise ConnectionError("Mock client not connected")
            
        # Validate tag exists
        if tag not in self._plc_tags:
            logger.warning(f"Tag not found in mock data: {tag}")
            raise KeyError(f"Tag not found: {tag}")
            
        # Update mock value in memory
        old_value = self._plc_tags[tag]
        self._plc_tags[tag] = value
        
        # Update mock_data.json file
        try:
            mock_data_path = Path("backend/config/mock_data.json")
            with open(mock_data_path, 'r') as f:
                data = json.load(f)
            
            # Update the mock_data section while preserving version
            data["mock_data"] = self._plc_tags
            
            with open(mock_data_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Updated mock data file for tag {tag}: {old_value} -> {value}")
        except Exception as e:
            logger.error(f"Failed to persist mock tag change to file: {e}")

    async def _simulate_updates(self) -> None:
        """Background task to simulate tag value updates."""
        try:
            while self._running:
                # Simulate tag value changes
                for tag in self._plc_tags:
                    if tag == "MainFlowRate":
                        # Main flow fluctuates around setpoint
                        setpoint = self._plc_tags.get("MainFlowRate", 0.0)
                        noise = random.uniform(-0.5, 0.5)  # ±0.5 SLPM
                        self._plc_tags[tag] = max(0.0, min(100.0, setpoint + noise))
                        
                    elif tag == "FeederFlowRate":
                        # Feeder flow fluctuates around setpoint
                        setpoint = self._plc_tags.get("FeederFlowRate", 0.0)
                        noise = random.uniform(-0.2, 0.2)  # ±0.2 SLPM
                        self._plc_tags[tag] = max(0.0, min(10.0, setpoint + noise))
                        
                await asyncio.sleep(0.1)  # Update every 100ms

        except asyncio.CancelledError:
            logger.debug("Mock update simulation stopped")
            raise
        except Exception as e:
            logger.error(f"Error in mock update simulation: {str(e)}")
            raise

    async def get(self, tags: List[str]) -> Dict[str, Any]:
        """Get multiple tag values at once.
        
        Args:
            tags: List of tag names to read
            
        Returns:
            Dictionary mapping tag names to their values
            
        Raises:
            ConnectionError: If client not connected
            KeyError: If tag not found and cannot be mapped
        """
        if not self._connected:
            raise ConnectionError("Mock client not connected")
            
        results = {}
        for tag in tags:
            # First try direct tag lookup
            if tag in self._plc_tags:
                results[tag] = self._plc_tags[tag]
                continue
                
            # Tag not found - check if it matches known PLC tag patterns
            if tag.startswith(("AMC.", "XYMove.", "XAxis.", "YAxis.", "ZAxis.")):
                logger.warning(f"Missing PLC tag {tag}, will add to mock data")
                self._plc_tags[tag] = 0.0 if "Position" in tag else False
                results[tag] = self._plc_tags[tag]
            else:
                # Unknown tag - raise error
                logger.error(f"Unknown tag {tag} requested")
                raise KeyError(f"Tag not found and cannot be mapped: {tag}")
                
        # Save any new tags to mock data file
        try:
            mock_data_path = Path("backend/config/mock_data.json")
            with open(mock_data_path, 'r') as f:
                data = json.load(f)
            
            # Update the mock_data section while preserving version
            data["mock_data"] = self._plc_tags
            
            with open(mock_data_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist mock data changes: {e}")
                
        return results
