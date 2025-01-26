"""Parameter Service

This module implements the Parameter service for managing process parameters.
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid
from pathlib import Path
from fastapi import status
from loguru import logger
import json

from mcs.utils.errors import create_error
from mcs.utils.health import (
    HealthStatus,
    ComponentHealth
)
from mcs.api.process.models.process_models import ProcessStatus, Parameter, Nozzle, Powder


class ParameterService:
    """Service for managing process parameters."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize parameter service.
        
        Args:
            config: Service configuration
        """
        # Basic properties
        self._service_name = "parameter"
        self._config = config
        self._version = config.get("version", "1.0.0")
        self._is_running = False
        self._is_initialized = False
        self._is_prepared = False
        self._start_time = None
        
        # Paths
        self._data_path = None
        self._schema_path = None
        self._parameter_dir = None
        self._nozzle_dir = None
        self._powder_dir = None
        
        # State
        self._parameters = {}
        self._nozzles = {}
        self._powders = {}
        self._failed_parameters = {}
        self._failed_nozzles = {}
        self._failed_powders = {}
        self._parameter_status = ProcessStatus.IDLE
        
        logger.info(f"{self.service_name} service initialized")

    @property
    def version(self) -> str:
        """Get service version."""
        return self._version

    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._service_name

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    @property
    def is_initialized(self) -> bool:
        """Get service initialization state."""
        return self._is_initialized

    @property
    def is_prepared(self) -> bool:
        """Get service preparation state."""
        return self._is_prepared

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
            
            # Get paths from config
            self._data_path = Path(self._config["paths"]["data"])
            self._schema_path = Path(self._config["paths"]["schemas"])
            
            # Set component directories
            self._parameter_dir = self._data_path / "parameters"
            self._nozzle_dir = self._data_path / "nozzles"
            self._powder_dir = self._data_path / "powders"
            
            # Validate paths
            for path in [self._parameter_dir, self._nozzle_dir, self._powder_dir]:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {path}")
            
            self._is_initialized = True
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def prepare(self) -> None:
        """Prepare service for operation."""
        try:
            if not self.is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            # Initialize state
            self._parameters = {}
            self._nozzles = {}
            self._powders = {}
            self._failed_parameters = {}
            self._failed_nozzles = {}
            self._failed_powders = {}
            self._parameter_status = ProcessStatus.IDLE

            self._is_prepared = True
            logger.info(f"{self.service_name} service prepared")

        except Exception as e:
            error_msg = f"Failed to prepare {self.service_name} service: {str(e)}"
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

            if not self.is_prepared:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not prepared"
                )

            # Load all data
            await self._load_parameters()
            await self._load_nozzles()
            await self._load_powders()

            self._is_running = True
            self._start_time = datetime.now()
            self._parameter_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            self._parameter_status = ProcessStatus.ERROR
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
            self._parameter_status = ProcessStatus.IDLE
            logger.info(f"{self.service_name} service stopped")

        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def shutdown(self) -> None:
        """Shutdown service and cleanup resources."""
        try:
            if self.is_running:
                await self.stop()
                
            self._is_initialized = False
            self._is_prepared = False
            self._parameters = {}
            self._nozzles = {}
            self._powders = {}
            self._failed_parameters = {}
            self._failed_nozzles = {}
            self._failed_powders = {}
            logger.info(f"{self.service_name} service shut down")
            
        except Exception as e:
            error_msg = f"Error during {self.service_name} service shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ComponentHealth:
        """Get service health."""
        status = HealthStatus.OK if self.is_running else HealthStatus.ERROR
        details = {
            "version": self._version,
            "uptime": self.uptime,
            "initialized": self.is_initialized,
            "prepared": self.is_prepared,
            "parameters_loaded": len(self._parameters),
            "nozzles_loaded": len(self._nozzles),
            "powders_loaded": len(self._powders),
            "failed_parameters": len(self._failed_parameters),
            "failed_nozzles": len(self._failed_nozzles),
            "failed_powders": len(self._failed_powders),
            "parameter_status": self._parameter_status
        }
        error = None if status == HealthStatus.OK else "Service not running"
        return ComponentHealth(
            status=status,
            error=error,
            details=details
        )

    async def _load_parameters(self) -> None:
        """Load parameters from configuration."""
        try:
            # Load parameter files from data directory
            if self._parameter_dir.exists():
                for file_path in self._parameter_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            parameter_data = json.load(f)
                            parameter_id = file_path.stem
                            self._parameters[parameter_id] = parameter_data
                            logger.info(f"Loaded parameter file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load parameter file {file_path.name}: {str(e)}")
                        self._failed_parameters[file_path.stem] = str(e)
            
            logger.info(f"Loaded {len(self._parameters)} parameters")
            
        except Exception as e:
            error_msg = f"Failed to load parameters: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def _load_nozzles(self) -> None:
        """Load nozzles from configuration."""
        try:
            # Load nozzle files from data directory
            if self._nozzle_dir.exists():
                for file_path in self._nozzle_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            nozzle_data = json.load(f)
                            nozzle_id = file_path.stem
                            self._nozzles[nozzle_id] = nozzle_data
                            logger.info(f"Loaded nozzle file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load nozzle file {file_path.name}: {str(e)}")
                        self._failed_nozzles[file_path.stem] = str(e)
            
            logger.info(f"Loaded {len(self._nozzles)} nozzles")
            
        except Exception as e:
            error_msg = f"Failed to load nozzles: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def _load_powders(self) -> None:
        """Load powders from configuration."""
        try:
            # Load powder files from data directory
            if self._powder_dir.exists():
                for file_path in self._powder_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            powder_data = json.load(f)
                            powder_id = file_path.stem
                            self._powders[powder_id] = powder_data
                            logger.info(f"Loaded powder file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to load powder file {file_path.name}: {str(e)}")
                        self._failed_powders[file_path.stem] = str(e)
            
            logger.info(f"Loaded {len(self._powders)} powders")
            
        except Exception as e:
            error_msg = f"Failed to load powders: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def list_parameters(self) -> List[Parameter]:
        """List available parameters."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            parameters = []
            for param_id, param_data in self._parameters.items():
                if "process" in param_data:
                    process_data = param_data["process"]
                    parameter = Parameter(
                        name=process_data.get("name", param_id),
                        created=process_data.get("created", ""),
                        author=process_data.get("author", ""),
                        description=process_data.get("description", ""),
                        nozzle=process_data.get("nozzle", ""),
                        main_gas=float(process_data.get("main_gas", 0.0)),
                        feeder_gas=float(process_data.get("feeder_gas", 0.0)),
                        frequency=int(process_data.get("frequency", 0)),
                        deagglomerator_speed=int(process_data.get("deagglomerator_speed", 0))
                    )
                    parameters.append(parameter)

            return parameters

        except Exception as e:
            error_msg = f"Failed to list parameters: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_parameter(self, param_id: str):
        """Get parameter by ID.
        
        Args:
            param_id: Parameter identifier
            
        Returns:
            Parameter: Parameter data
            
        Raises:
            HTTPException: If parameter not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
            
            if param_id not in self._parameters:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Parameter {param_id} not found"
                )
                
            return self._parameters[param_id]
            
        except Exception as e:
            logger.error(f"Failed to get parameter {param_id}: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to get parameter: {str(e)}"
            )

    async def list_nozzles(self) -> List[Nozzle]:
        """List available nozzles."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            nozzles = []
            for nozzle_id, nozzle_data in self._nozzles.items():
                if "nozzle" in nozzle_data:
                    nozzle_info = nozzle_data["nozzle"]
                    nozzle = Nozzle(
                        name=nozzle_info.get("name", nozzle_id),
                        manufacturer=nozzle_info.get("manufacturer", ""),
                        type=nozzle_info.get("type", ""),
                        description=nozzle_info.get("description", "")
                    )
                    nozzles.append(nozzle)

            return nozzles

        except Exception as e:
            error_msg = f"Failed to list nozzles: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def list_powders(self) -> List[str]:
        """List available powders.
        
        Returns:
            List[str]: List of powder IDs
            
        Raises:
            HTTPException: If service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            return list(self._powders.keys())

        except Exception as e:
            error_msg = f"Failed to list powders: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_nozzle(self, nozzle_id: str) -> Nozzle:
        """Get nozzle by ID."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if nozzle_id not in self._nozzles:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Nozzle {nozzle_id} not found"
                )

            nozzle_data = self._nozzles[nozzle_id]
            if "nozzle" in nozzle_data:
                nozzle_info = nozzle_data["nozzle"]
                return Nozzle(
                    name=nozzle_info.get("name", nozzle_id),
                    manufacturer=nozzle_info.get("manufacturer", ""),
                    type=nozzle_info.get("type", ""),
                    description=nozzle_info.get("description", "")
                )

            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Invalid nozzle data format for {nozzle_id}"
            )

        except Exception as e:
            error_msg = f"Failed to get nozzle: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def get_powder(self, powder_id: str) -> Powder:
        """Get powder by ID."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if powder_id not in self._powders:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Powder {powder_id} not found"
                )

            powder_data = self._powders[powder_id]
            if "powder" in powder_data:
                powder_info = powder_data["powder"]
                return Powder(
                    name=powder_info.get("name", powder_id),
                    type=powder_info.get("type", ""),
                    size=powder_info.get("size", ""),
                    manufacturer=powder_info.get("manufacturer", ""),
                    lot=powder_info.get("lot", "")
                )

            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Invalid powder data format for {powder_id}"
            )

        except Exception as e:
            error_msg = f"Failed to get powder: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def create_nozzle(self, nozzle: Nozzle) -> str:
        """Create new nozzle configuration.
        
        Args:
            nozzle: Nozzle configuration
            
        Returns:
            str: Nozzle ID
            
        Raises:
            HTTPException: If service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Generate unique ID
            nozzle_id = str(uuid.uuid4())
            
            # Create nozzle data structure
            nozzle_data = {
                "nozzle": {
                    "name": nozzle.name,
                    "manufacturer": nozzle.manufacturer,
                    "type": nozzle.type,
                    "description": nozzle.description,
                    "created": datetime.now().isoformat()
                }
            }
            
            # Save to file
            nozzle_dir = Path("backend/data/nozzles")
            nozzle_dir.mkdir(parents=True, exist_ok=True)
            
            nozzle_path = nozzle_dir / f"{nozzle_id}.json"
            with open(nozzle_path, "w") as f:
                json.dump(nozzle_data, f, indent=2)
            
            # Add to memory
            self._nozzles[nozzle_id] = nozzle_data
            
            logger.info(f"Created nozzle configuration: {nozzle_id}")
            return nozzle_id

        except Exception as e:
            error_msg = f"Failed to create nozzle: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def update_nozzle(self, nozzle_id: str, nozzle: Nozzle) -> None:
        """Update nozzle configuration.
        
        Args:
            nozzle_id: Nozzle identifier
            nozzle: Updated nozzle configuration
            
        Raises:
            HTTPException: If nozzle not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if nozzle_id not in self._nozzles:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Nozzle {nozzle_id} not found"
                )
            
            # Update nozzle data
            nozzle_data = {
                "nozzle": {
                    "name": nozzle.name,
                    "manufacturer": nozzle.manufacturer,
                    "type": nozzle.type,
                    "description": nozzle.description,
                    "updated": datetime.now().isoformat()
                }
            }
            
            # Save to file
            nozzle_path = Path(f"backend/data/nozzles/{nozzle_id}.json")
            with open(nozzle_path, "w") as f:
                json.dump(nozzle_data, f, indent=2)
            
            # Update memory
            self._nozzles[nozzle_id] = nozzle_data
            
            logger.info(f"Updated nozzle configuration: {nozzle_id}")

        except Exception as e:
            error_msg = f"Failed to update nozzle: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def delete_nozzle(self, nozzle_id: str) -> None:
        """Delete nozzle configuration.
        
        Args:
            nozzle_id: Nozzle identifier
            
        Raises:
            HTTPException: If nozzle not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if nozzle_id not in self._nozzles:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Nozzle {nozzle_id} not found"
                )
            
            # Delete file
            nozzle_path = Path(f"backend/data/nozzles/{nozzle_id}.json")
            if nozzle_path.exists():
                nozzle_path.unlink()
            
            # Remove from memory
            del self._nozzles[nozzle_id]
            
            logger.info(f"Deleted nozzle configuration: {nozzle_id}")

        except Exception as e:
            error_msg = f"Failed to delete nozzle: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def create_powder(self, powder: Powder) -> str:
        """Create new powder configuration.
        
        Args:
            powder: Powder configuration
            
        Returns:
            str: Powder ID
            
        Raises:
            HTTPException: If service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            # Generate unique ID
            powder_id = str(uuid.uuid4())
            
            # Create powder data structure
            powder_data = {
                "powder": {
                    "name": powder.name,
                    "type": powder.type,
                    "size": powder.size,
                    "manufacturer": powder.manufacturer,
                    "lot": powder.lot,
                    "created": datetime.now().isoformat()
                }
            }
            
            # Save to file
            powder_dir = Path("backend/data/powders")
            powder_dir.mkdir(parents=True, exist_ok=True)
            
            powder_path = powder_dir / f"{powder_id}.json"
            with open(powder_path, "w") as f:
                json.dump(powder_data, f, indent=2)
            
            # Add to memory
            self._powders[powder_id] = powder_data
            
            logger.info(f"Created powder configuration: {powder_id}")
            return powder_id

        except Exception as e:
            error_msg = f"Failed to create powder: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def update_powder(self, powder_id: str, powder: Powder) -> None:
        """Update powder configuration.
        
        Args:
            powder_id: Powder identifier
            powder: Updated powder configuration
            
        Raises:
            HTTPException: If powder not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if powder_id not in self._powders:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Powder {powder_id} not found"
                )
            
            # Update powder data
            powder_data = {
                "powder": {
                    "name": powder.name,
                    "type": powder.type,
                    "size": powder.size,
                    "manufacturer": powder.manufacturer,
                    "lot": powder.lot,
                    "updated": datetime.now().isoformat()
                }
            }
            
            # Save to file
            powder_path = Path(f"backend/data/powders/{powder_id}.json")
            with open(powder_path, "w") as f:
                json.dump(powder_data, f, indent=2)
            
            # Update memory
            self._powders[powder_id] = powder_data
            
            logger.info(f"Updated powder configuration: {powder_id}")

        except Exception as e:
            error_msg = f"Failed to update powder: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def delete_powder(self, powder_id: str) -> None:
        """Delete powder configuration.
        
        Args:
            powder_id: Powder identifier
            
        Raises:
            HTTPException: If powder not found or service error
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            if powder_id not in self._powders:
                raise create_error(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Powder {powder_id} not found"
                )
            
            # Delete file
            powder_path = Path(f"backend/data/powders/{powder_id}.json")
            if powder_path.exists():
                powder_path.unlink()
            
            # Remove from memory
            del self._powders[powder_id]
            
            logger.info(f"Deleted powder configuration: {powder_id}")

        except Exception as e:
            error_msg = f"Failed to delete powder: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
