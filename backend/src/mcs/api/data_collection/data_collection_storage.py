"""PostgreSQL storage implementation."""

from typing import Dict, Any, List
from datetime import datetime
from fastapi import status
from loguru import logger
import asyncpg

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health


class DataCollectionStorage:
    """PostgreSQL storage implementation."""
    
    def __init__(self, dsn: str = None, pool_config: Dict[str, Any] = None):
        """Initialize with database connection string and pool configuration."""
        self._service_name = "data_storage"
        self._version = "1.0.0"
        self._is_initialized = False
        self._is_prepared = False
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._dsn = dsn
        self._pool_config = pool_config or {
            "min_size": 2,
            "max_size": 10,
            "command_timeout": 60.0
        }
        self._pool = None
        
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
        """Initialize storage service."""
        try:
            if self._is_initialized:
                logger.warning(f"{self.service_name} service already initialized")
                return

            if not self._dsn:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} DSN not configured"
                )

            # Create connection pool
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=int(self._pool_config["min_size"]),
                max_size=int(self._pool_config["max_size"]),
                command_timeout=float(self._pool_config["command_timeout"])
            )

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

            # Verify database connection and schema
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")

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
        """Start storage service."""
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
            # Close database pool
            if self._pool:
                await self._pool.close()
                self._pool = None

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
            # Check critical components
            pool_ok = self._pool is not None
            db_ok = False
            pool_stats = None
            
            if pool_ok:
                try:
                    async with self._pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                        db_ok = True
                        pool_stats = {
                            "min_size": self._pool.get_min_size(),
                            "max_size": self._pool.get_max_size(),
                            "size": len(self._pool._holders),  # Current pool size
                            "free": len(self._pool._queue._queue)  # Available connections
                        }
                except Exception as e:
                    logger.error(f"Database health check failed: {e}")
            
            # Build component statuses focusing on critical components
            components = {
                "database": ComponentHealth(
                    status=HealthStatus.OK if db_ok else HealthStatus.ERROR,
                    error=None if db_ok else "Database connection failed",
                    details=pool_stats
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
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg)

    async def execute(self, query: str, *args) -> None:
        """Execute database query.
        
        Args:
            query: SQL query string
            *args: Query parameters
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            async with self._pool.acquire() as conn:
                await conn.execute(query, *args)

        except Exception as e:
            error_msg = f"Failed to execute query: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute database query and return results.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    message=f"{self.service_name} service not running"
                )

            async with self._pool.acquire() as conn:
                results = await conn.fetch(query, *args)
                return [dict(row) for row in results]

        except Exception as e:
            error_msg = f"Failed to execute query: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
