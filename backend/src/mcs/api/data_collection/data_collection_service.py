"""Data collection service."""

import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health
from mcs.api.data_collection.data_collection_storage import DataCollectionStorage


def load_config() -> Dict[str, Any]:
    """Load data collection configuration.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        config_path = os.path.join("backend", "config", "data_collection.yaml")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "version": "1.0.0",
                "service": {
                    "name": "data_collection",
                    "host": "0.0.0.0",
                    "port": 8005,
                    "log_level": "INFO",
                    "history_retention_days": 30
                },
                "components": {
                    "database": {
                        "version": "1.0.0",
                        "host": "localhost",
                        "port": 5432,
                        "user": "mock_user",
                        "password": "mock_password",
                        "database": "mock_db",
                        "pool": {
                            "min_size": 1,
                            "max_size": 10
                        }
                    }
                }
            }
            
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
            
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to load configuration: {str(e)}"
        )


class DataCollectionService:
    """Service for collecting spray data."""

    def __init__(self, storage: Optional[DataCollectionStorage] = None, version: str = "1.0.0"):
        """Initialize service.
        
        Args:
            storage: Optional pre-configured storage service
            version: Service version
        """
        self._service_name = "data_collection"
        self._version = version
        self._is_initialized = False
        self._is_prepared = False
        self._is_running = False
        self._start_time = None
        self._config = None
        self._mode = "normal"  # Default to normal mode
        
        # Initialize components to None
        self._storage = storage
        self._collecting = False
        self._current_sequence = None
        
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
    def is_initialized(self) -> bool:
        """Get service initialization state."""
        return self._is_initialized

    @property
    def is_prepared(self) -> bool:
        """Get service preparation state."""
        return self._is_prepared

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    @property
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize service and its components."""
        try:
            if self._is_initialized:
                logger.warning(f"{self.service_name} service already initialized")
                return

            # Load config first
            self._config = load_config()
            self._version = self._config.get("version", self._version)
            
            # Initialize storage if not provided or needs re-initialization
            if not self._storage:
                db_config = self._config["components"]["database"]
                dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
                self._storage = DataCollectionStorage(dsn=dsn, pool_config=db_config["pool"])
            
            # Always initialize storage
            await self._storage.initialize()
                
            self._is_initialized = True
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            self._is_initialized = False
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def prepare(self) -> None:
        """Prepare service for operation.
        
        This step handles operations that require running dependencies.
        """
        try:
            if not self._is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            if self._is_prepared:
                logger.warning(f"{self.service_name} service already prepared")
                return

            # Prepare and start storage service
            await self._storage.prepare()
            await self._storage.start()

            self._is_prepared = True
            logger.info(f"{self.service_name} service prepared")

        except Exception as e:
            self._is_prepared = False
            error_msg = f"Failed to prepare {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start service operations."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            if not self._is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )

            if not self._is_prepared:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not prepared"
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

    async def _stop(self) -> None:
        """Internal method to stop service operations."""
        try:
            # Stop data collection if active
            if self._collecting:
                await self.stop_collection()

            # Stop storage service
            if self._storage and self._storage.is_running:
                await self._storage.shutdown()

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

    async def shutdown(self) -> None:
        """Stop service and cleanup resources."""
        try:
            if not self.is_running:
                logger.warning(f"{self.service_name} service not running")
                return

            await self._stop()
            self._is_prepared = False
            self._is_initialized = False
            logger.info(f"{self.service_name} service shut down")

        except Exception as e:
            error_msg = f"Failed to shut down {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # In mock mode, always return healthy status
            if self._mode == "mock":
                return ServiceHealth(
                    status=HealthStatus.OK,
                    service=self.service_name,
                    version=self.version,
                    is_running=self.is_running,
                    uptime=self.uptime,
                    mode=self._mode,
                    components={
                        "storage": ComponentHealth(
                            status=HealthStatus.OK,
                            details={"connected": True}
                        ),
                        "collector": ComponentHealth(
                            status=HealthStatus.OK,
                            details={
                                "collecting": self._collecting,
                                "sequence": self._current_sequence
                            }
                        )
                    }
                )
            
            # Check critical components
            storage_health = await self._storage.health() if self._storage else None
            storage_ok = storage_health and storage_health.status == HealthStatus.OK
            
            # Build component statuses focusing on critical components
            components = {
                "storage": ComponentHealth(
                    status=HealthStatus.OK if storage_ok else HealthStatus.ERROR,
                    error=storage_health.error if storage_health else "Storage not initialized",
                    details={"connected": storage_ok}
                ),
                "collector": ComponentHealth(
                    status=HealthStatus.OK if self.is_running else HealthStatus.ERROR,
                    error=None if self.is_running else "Collector not running",
                    details={
                        "collecting": self._collecting,
                        "sequence": self._current_sequence
                    }
                )
            }
            
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
                mode=self._mode,
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg, mode=self._mode)

    async def start_collection(self, sequence_id: str) -> None:
        """Start data collection for a sequence."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
                
            self._collecting = True
            self._current_sequence = sequence_id
            logger.info(f"Started data collection for sequence {sequence_id}")
            
        except Exception as e:
            error_msg = f"Failed to start data collection: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop_collection(self) -> None:
        """Stop current data collection."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )
                
            self._collecting = False
            self._current_sequence = None
            logger.info("Stopped data collection")
            
        except Exception as e:
            error_msg = f"Failed to stop data collection: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )
