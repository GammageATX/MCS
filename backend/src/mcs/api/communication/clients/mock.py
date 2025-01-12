"""Mock client that simulates PLC behavior."""

import asyncio
import yaml
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
        mock_data_path = Path("backend/config/mock_data.yaml")
        if not mock_data_path.exists():
            logger.warning(f"Mock data file not found: {mock_data_path}")
            self._mock_data = {"plc_tags": {}}
        else:
            with open(mock_data_path) as f:
                self._mock_data = yaml.safe_load(f)
            logger.info(f"Loaded mock data from {mock_data_path}")
            
        # Initialize mock tag values from mock_data.yaml
        self._plc_tags = self._mock_data.get("plc_tags", {}).copy()  # Make a copy
        logger.info(f"Mock client initialized with {len(self._plc_tags)} tags")
        logger.debug(f"Available mock tags: {list(self._plc_tags.keys())}")

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
            
        # Update mock value
        old_value = self._plc_tags[tag]
        self._plc_tags[tag] = value
        
        # Handle special cases for linked values
        if tag == "AOS32-0.1.2.1":  # Main gas flow setpoint (DAC value)
            # Update MainFlowRate to match setpoint
            flow_slpm = (value / 4095.0) * 100.0  # Convert DAC to SLPM
            self._plc_tags["MainFlowRate"] = flow_slpm
            logger.debug(f"Updated MainFlowRate to {flow_slpm:.1f} SLPM based on setpoint DAC {value}")
        elif tag == "AOS32-0.1.2.2":  # Feeder gas flow setpoint (DAC value)
            # Update FeederFlowRate to match setpoint
            flow_slpm = (value / 4095.0) * 10.0  # Convert DAC to SLPM
            self._plc_tags["FeederFlowRate"] = flow_slpm
            logger.debug(f"Updated FeederFlowRate to {flow_slpm:.1f} SLPM based on setpoint DAC {value}")
        
        logger.debug(f"Wrote mock tag {tag} = {value} (was {old_value})")

    def is_connected(self) -> bool:
        """Check if mock client is connected.
        
        Returns:
            Connection status
        """
        return self._connected

    async def get(self, tags: List[str]) -> Dict[str, Any]:
        """Read multiple mock tag values.
        
        Args:
            tags: List of tags to read
            
        Returns:
            Dict mapping tag names to values
            
        Note:
            Tags not found in mock data will be skipped with a warning
        """
        if not self._connected:
            raise ConnectionError("Mock client not connected")
            
        # Return mock values for all requested tags
        values = {}
        missing_tags = []
        for tag in tags:
            if tag not in self._plc_tags:
                missing_tags.append(tag)
                continue
            values[tag] = self._plc_tags[tag]
            
        if missing_tags:
            logger.warning(f"Tags not found in mock data: {missing_tags}")
            logger.debug(f"Available mock tags: {list(self._plc_tags.keys())}")
            
        if not values:
            logger.error("No valid tags found in request")
            
        logger.debug(f"Read {len(values)} mock tags")
        return values

    async def _simulate_updates(self) -> None:
        """Background task to simulate tag value updates."""
        try:
            while self._running:
                # Simulate tag value changes
                for tag in self._plc_tags:
                    if tag == "MainGasPressure":
                        # Main gas pressure fluctuates around 80 PSI
                        current = self._plc_tags[tag]
                        delta = random.uniform(-0.5, 0.5)
                        self._plc_tags[tag] = max(70.0, min(90.0, current + delta))
                        
                    elif tag == "RegulatorPressure":
                        # Regulator pressure fluctuates around 60 PSI
                        current = self._plc_tags[tag]
                        delta = random.uniform(-0.3, 0.3)
                        self._plc_tags[tag] = max(55.0, min(65.0, current + delta))
                        
                    elif tag == "NozzlePressure":
                        # Nozzle pressure fluctuates around 55 PSI
                        current = self._plc_tags[tag]
                        delta = random.uniform(-0.2, 0.2)
                        self._plc_tags[tag] = max(50.0, min(60.0, current + delta))
                        
                    elif tag == "FeederPressure":
                        # Feeder pressure fluctuates around 500 torr
                        current = self._plc_tags[tag]
                        delta = random.uniform(-5.0, 5.0)
                        self._plc_tags[tag] = max(450.0, min(550.0, current + delta))
                        
                    elif tag == "ChamberPressure":
                        # Chamber pressure fluctuates around 2.5 torr
                        current = self._plc_tags[tag]
                        delta = random.uniform(-0.1, 0.1)
                        self._plc_tags[tag] = max(1.0, min(5.0, current + delta))
                        
                    elif tag == "AOS32-0.1.2.1":  # Main gas flow setpoint
                        # This is a 12-bit value (0-4095) representing 0-100 SLPM
                        continue  # Don't simulate changes to setpoint
                        
                    elif tag == "MainFlowRate":
                        # Main flow fluctuates around setpoint
                        setpoint = self._plc_tags.get("AOS32-0.1.2.1", 2048) / 4095 * 100  # Convert to SLPM
                        noise = random.uniform(-0.5, 0.5)  # ±0.5 SLPM
                        self._plc_tags[tag] = max(0.0, min(100.0, setpoint + noise))
                        
                    elif tag == "AOS32-0.1.2.2":  # Feeder gas flow setpoint
                        # This is a 12-bit value (0-4095) representing 0-10 SLPM
                        continue  # Don't simulate changes to setpoint
                        
                    elif tag == "FeederFlowRate":
                        # Feeder flow fluctuates around setpoint
                        setpoint = self._plc_tags.get("AOS32-0.1.2.2", 2048) / 4095 * 10  # Convert to SLPM
                        noise = random.uniform(-0.2, 0.2)  # ±0.2 SLPM
                        self._plc_tags[tag] = max(0.0, min(10.0, setpoint + noise))
                        
                await asyncio.sleep(0.1)  # Update every 100ms
                
        except asyncio.CancelledError:
            logger.debug("Mock update simulation stopped")
            raise
        except Exception as e:
            logger.error(f"Error in mock update simulation: {str(e)}")
            raise
