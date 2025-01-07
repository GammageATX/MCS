"""MicroColdSpray backend startup script."""

import os
import sys
import uvicorn
import asyncio
from loguru import logger
from typing import Dict, List, Tuple, Any
from datetime import datetime

from mcs import (
    create_ui_app,
    create_config_service,
    create_state_service,
    create_process_service,
    create_data_collection_service
)
from mcs.api.communication.communication_app import create_communication_service
from mcs.utils.health import HealthStatus


def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join("logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Remove default handler
    logger.remove()
    
    # Add console handler with color
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, format=log_format, level="INFO", enqueue=True)
    
    # Add file handler with rotation
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    logger.add(
        os.path.join(log_dir, "mcs.log"),
        rotation="1 day",
        retention="30 days",
        format=file_format,
        level="DEBUG",
        enqueue=True,
        compression="zip"
    )


class ServerManager:
    """Manages multiple Uvicorn servers."""

    def __init__(self):
        """Initialize server manager."""
        self.servers: Dict[str, uvicorn.Server] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._shutdown = asyncio.Event()

    async def start_server(self, app: Any, name: str, port: int) -> bool:
        """Start a server in the background.
        
        Args:
            app: FastAPI application
            name: Service name
            port: Port number
            
        Returns:
            bool: True if server started successfully
        """
        try:
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            self.servers[name] = server
            
            # Create and store server task
            task = asyncio.create_task(server.serve())
            self.tasks[name] = task
            
            # Wait for startup
            await asyncio.sleep(2)  # Give server time to start
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name} server: {e}")
            return False

    async def check_health(self, app: Any, name: str, port: int, timeout: int = 30) -> bool:
        """Check if a service is healthy.
        
        Args:
            app: Service application instance
            name: Service name
            port: Service port
            timeout: Maximum time to wait for health in seconds
            
        Returns:
            bool: True if service is healthy, False otherwise
        """
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                if hasattr(app.state, "service"):
                    health = await app.state.service.health()
                    if health.status == HealthStatus.OK:
                        logger.info(f"{name} service healthy on port {port}")
                        return True
            except Exception as e:
                logger.warning(f"Health check failed for {name} service: {e}")
            await asyncio.sleep(1)
        
        logger.error(f"{name} service failed to become healthy within {timeout} seconds")
        return False

    async def start_service(self, app: Any, name: str, port: int, dependencies: List[Tuple[str, int]] = None) -> bool:
        """Start a service and verify its health.
        
        Args:
            app: Service application instance
            name: Service name
            port: Service port
            dependencies: List of (name, port) tuples for required services
            
        Returns:
            bool: True if service started successfully, False otherwise
        """
        try:
            # Check dependencies first
            if dependencies:
                for dep_name, dep_port in dependencies:
                    logger.info(f"Checking {dep_name} dependency on port {dep_port}")
                    # TODO: Implement dependency health check
                    await asyncio.sleep(1)  # Give dependency time to start

            # Start server
            logger.info(f"Starting {name} service on port {port}")
            if not await self.start_server(app, name, port):
                return False

            # Check health
            if not await self.check_health(app, name, port):
                await self.stop_server(name)
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to start {name} service: {e}")
            return False

    async def stop_server(self, name: str):
        """Stop a server by name."""
        if name in self.servers:
            server = self.servers[name]
            server.should_exit = True
            if name in self.tasks:
                task = self.tasks[name]
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for {name} server to stop")
                del self.tasks[name]
            del self.servers[name]

    async def stop_all(self):
        """Stop all running servers."""
        stop_tasks = []
        for name in list(self.servers.keys()):
            stop_tasks.append(self.stop_server(name))
        if stop_tasks:
            await asyncio.gather(*stop_tasks)

    async def wait_for_servers(self):
        """Wait for all servers to complete."""
        if self.tasks:
            done, pending = await asyncio.wait(
                self.tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )
            # If any server exits, trigger shutdown
            if done:
                self._shutdown.set()

    async def run_until_shutdown(self):
        """Run servers until shutdown is triggered."""
        try:
            await self.wait_for_servers()
        except asyncio.CancelledError:
            logger.info("Received shutdown signal")
        finally:
            await self.stop_all()


async def main():
    """Run all MCS services."""
    try:
        setup_logging()
        logger.info("Starting MCS services...")

        # Define service dependencies
        dependencies: Dict[str, List[Tuple[str, int]]] = {
            "ui": [("config", 8001), ("state", 8002)],
            "process": [("config", 8001), ("state", 8002)],
            "data_collection": [("config", 8001), ("state", 8002)],
            "communication": [("config", 8001), ("state", 8002)]
        }

        # Create all service apps
        services = [
            # Core services first (no dependencies)
            (create_config_service(), "Config", 8001, []),
            (create_state_service(), "State", 8002, []),
            # Services with dependencies
            (create_communication_service(), "Communication", 8003, dependencies["communication"]),
            (create_process_service(), "Process", 8004, dependencies["process"]),
            (create_data_collection_service(), "Data Collection", 8005, dependencies["data_collection"]),
            # UI last as it depends on other services
            (create_ui_app(), "UI", 8000, dependencies["ui"])
        ]

        # Create server manager
        manager = ServerManager()

        # Start services in order
        running_services = []
        failed_services = []
        
        for app, name, port, deps in services:
            if await manager.start_service(app, name, port, deps):
                running_services.append((name, port))
            else:
                failed_services.append(name)
                break

        if failed_services:
            logger.error(f"Failed to start services: {', '.join(failed_services)}")
            await manager.stop_all()
            sys.exit(1)

        logger.info("All MCS services started successfully")
        logger.info("Running services:")
        for name, port in running_services:
            logger.info(f"  - {name}: http://localhost:{port}")
        
        # Wait for servers or shutdown
        await manager.run_until_shutdown()

    except Exception:
        logger.exception("Failed to start MCS services")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        sys.exit(0)
