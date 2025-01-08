"""MicroColdSpray backend startup script."""

import os
import sys
import uvicorn
import asyncio
import importlib
import aiohttp
from loguru import logger
from typing import Dict, List, Tuple, Any
from datetime import datetime


def create_app_from_path(app_path: str) -> Any:
    """Create app instance from module path.
    
    Args:
        app_path: Module path in format 'module.path:app' or 'module.path:create_app'
        
    Returns:
        FastAPI application instance
    """
    try:
        module_path, app_name = app_path.split(":")
        module = importlib.import_module(module_path)
        app_obj = getattr(module, app_name)
        
        # If it's a function that creates the app, call it
        if callable(app_obj) and not isinstance(app_obj, type):
            return app_obj()
        # If it's already an app instance, return it
        return app_obj
    except Exception as e:
        logger.error(f"Failed to create app from path {app_path}: {e}")
        raise


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

    def __init__(self, dev_mode: bool = False):
        """Initialize server manager.
        
        Args:
            dev_mode: Enable development mode with autoreload
        """
        self.servers: Dict[str, uvicorn.Server] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self._shutdown = asyncio.Event()
        self.dev_mode = dev_mode

    async def start_server(self, app: Any, name: str, port: int) -> bool:
        """Start a server in the background.
        
        Args:
            app: FastAPI application or factory function path
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
                log_level="info",
                reload=self.dev_mode,
                reload_dirs=["backend/src/mcs"] if self.dev_mode else None,
                factory=self.dev_mode,  # Enable factory mode for hot reload
                workers=1
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
        """Check if a service is healthy via HTTP endpoint.
        
        Args:
            app: Service application instance (unused, kept for API compatibility)
            name: Service name
            port: Service port
            timeout: Maximum time to wait for health in seconds
            
        Returns:
            bool: True if service is healthy, False otherwise
        """
        start_time = datetime.now()
        url = f"http://localhost:{port}/health"
        
        async with aiohttp.ClientSession() as session:
            while (datetime.now() - start_time).total_seconds() < timeout:
                try:
                    async with session.get(url, timeout=2) as response:
                        # For UI, just check it responds
                        if name == "UI":
                            return response.status != 500  # As long as it's not a server error
                            
                        # For services, check basic health response
                        if response.status == 200:
                            data = await response.json()
                            if data.get("status", "").lower() == "ok":
                                return True
                            logger.warning(f"{name} reported unhealthy status: {data.get('status')}")
                except Exception as e:
                    logger.warning(f"Health check failed for {name} service: {e}")
                await asyncio.sleep(1)
            
            logger.error(f"{name} service failed to become healthy within {timeout} seconds")
            return False

    async def start_service(self, app: Any, name: str, port: int, dependencies: List[Tuple[str, int]] = None) -> bool:
        """Start a service and verify its startup.
        
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

            # Wait for startup to complete
            await asyncio.sleep(2)  # Give service time to initialize
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

        # Check if running in development mode
        dev_mode = os.environ.get("MCS_DEV_MODE", "").lower() in ("true", "1", "yes")
        if dev_mode:
            logger.info("Running in development mode with autoreload enabled")

        # Define service dependencies
        dependencies: Dict[str, List[Tuple[str, int]]] = {
            "ui": [("config", 8001)],
            "process": [("config", 8001)],
            "data_collection": [("config", 8001)],
            "communication": [("config", 8001)]
        }

        # Create all service apps with module paths for reloading
        services = [
            # Core services first (no dependencies)
            ("mcs.api.config.config_app:create_config_service", "Config", 8001, []),
            # Services with dependencies
            ("mcs.api.communication.communication_app:create_communication_service", "Communication", 8003, dependencies["communication"]),
            ("mcs.api.process.process_app:create_process_service", "Process", 8004, dependencies["process"]),
            ("mcs.api.data_collection.data_collection_app:create_data_collection_service", "Data Collection", 8005, dependencies["data_collection"]),
            # UI last as it depends on other services
            ("mcs.ui.router:create_ui_app", "UI", 8000, dependencies["ui"])
        ]

        # Create server manager with dev mode setting
        manager = ServerManager(dev_mode=dev_mode)

        # Start services in order
        running_services = []
        failed_services = []
        service_instances = []
        
        for app_path, name, port, deps in services:
            # In dev mode, pass the module path directly to uvicorn
            # In prod mode, create the app instance first
            app = app_path if dev_mode else create_app_from_path(app_path)
            if await manager.start_service(app, name, port, deps):
                running_services.append((name, port))
                service_instances.append((app, name, port))
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
        
        # Initial health check
        logger.info("Checking initial health of all services...")
        unhealthy_services = []
        for app, name, port in service_instances:
            if not await manager.check_health(app, name, port, timeout=10):
                unhealthy_services.append(name)
        
        if unhealthy_services:
            logger.warning(f"Services starting with health issues: {', '.join(unhealthy_services)}")
            logger.warning("System will continue running - services can be restarted individually")
        else:
            logger.info("All services initially healthy")

        # Start periodic health monitoring
        async def monitor_health():
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                logger.debug("Performing periodic health check...")
                for app, name, port in service_instances:
                    try:
                        if not await manager.check_health(app, name, port, timeout=5):
                            logger.warning(f"Service {name} unhealthy")
                    except Exception as e:
                        logger.warning(f"Health check failed for {name}: {e}")

        # Start health monitoring in background
        monitor_task = asyncio.create_task(monitor_health())
        
        try:
            # Wait for servers or shutdown
            await manager.run_until_shutdown()
        finally:
            # Cancel health monitoring
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

    except Exception:
        logger.exception("Failed to start MCS services")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        sys.exit(0)
