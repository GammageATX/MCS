"""MicroColdSpray System Main Application.

This module serves as the entry point for the MicroColdSpray system.
It handles service orchestration, health monitoring, and system lifecycle.
"""

import sys
import asyncio
import signal
import aiohttp
import uvicorn
import multiprocessing as mp
from pathlib import Path
from typing import Dict, Optional, Any
from importlib import import_module
from datetime import datetime, timedelta
from loguru import logger

from mcs import __version__


class ServiceConfig:
    """Service configuration constants."""
    
    # Service module paths
    MODULES = {
        'config': (
            "mcs.api.config.config_app:create_config_service"
        ),
        'state': (
            "mcs.api.state.state_app:create_state_service"
        ),
        'communication': (
            "mcs.api.communication.communication_app:create_communication_service"
        ),
        'process': (
            "mcs.api.process.process_app:create_process_service"
        ),
        'data_collection': (
            "mcs.api.data_collection.data_collection_app:create_data_collection_service"
        ),
        'ui': "mcs.ui.router:create_app"
    }

    # Service startup order with dependencies
    STARTUP_ORDER = [
        'config',            # Configuration service (port 8001)
        'state',            # State management service (port 8002)
        'communication',     # Hardware communication service (port 8003)
        'process',          # Process control service (port 8004)
        'data_collection',  # Data collection service (port 8005)
        'ui'               # Web interface (port 8000)
    ]

    # Service port mapping
    PORTS = {
        'config': 8001,
        'state': 8002,
        'communication': 8003,
        'process': 8004,
        'data_collection': 8005,
        'ui': 8000
    }

    # Health check endpoints
    HEALTH_ENDPOINTS = {
        'config': 'http://localhost:8001/health',
        'state': 'http://localhost:8002/health',
        'communication': 'http://localhost:8003/health',
        'process': 'http://localhost:8004/health',
        'data_collection': 'http://localhost:8005/health',
        'ui': 'http://localhost:8000/health'
    }

    # Service startup timeouts (seconds)
    STARTUP_TIMEOUT = 30
    HEALTH_CHECK_INTERVAL = 5
    SHUTDOWN_TIMEOUT = 10

    # Service process management
    processes: Dict[str, mp.Process] = {}
    health_check_task: Optional[asyncio.Task] = None
    shutdown_event: Optional[asyncio.Event] = None


def create_service(name: str) -> Any:
    """Create a service instance from module path.
    
    Args:
        name: Service name to create
        
    Returns:
        Created service instance
    """
    try:
        module_path, factory = ServiceConfig.MODULES[name].split(':')
        module = import_module(module_path)
        create_func = getattr(module, factory)
        return create_func()
    except Exception as e:
        logger.error(f"Failed to create service {name}: {str(e)}")
        raise


async def check_service_health(session: aiohttp.ClientSession, name: str) -> bool:
    """Check if a service is healthy via HTTP health check.
    
    Args:
        session: aiohttp client session
        name: Service name to check
        
    Returns:
        True if service is healthy
    """
    try:
        endpoint = ServiceConfig.HEALTH_ENDPOINTS[name]
        async with session.get(endpoint) as response:
            if response.status == 200:
                health_data = await response.json()
                return health_data.get('status') == 'healthy'
    except Exception as e:
        logger.error(f"Health check failed for {name}: {str(e)}")
    return False


async def wait_for_service(
    session: aiohttp.ClientSession,
    name: str,
    timeout: float = ServiceConfig.STARTUP_TIMEOUT
) -> bool:
    """Wait for service to become healthy within timeout.
    
    Args:
        session: aiohttp client session
        name: Service name to wait for
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if service became healthy within timeout
    """
    start_time = datetime.now()
    while (datetime.now() - start_time) < timedelta(seconds=timeout):
        if await check_service_health(session, name):
            return True
        await asyncio.sleep(1)
    return False


async def monitor_service_health() -> None:
    """Monitor health of all services periodically."""
    async with aiohttp.ClientSession() as session:
        while not ServiceConfig.shutdown_event.is_set():
            unhealthy = []
            for name in ServiceConfig.STARTUP_ORDER:
                if not await check_service_health(session, name):
                    unhealthy.append(name)
            
            if unhealthy:
                logger.warning(f"Unhealthy services: {', '.join(unhealthy)}")
            
            try:
                await asyncio.wait_for(
                    ServiceConfig.shutdown_event.wait(),
                    timeout=ServiceConfig.HEALTH_CHECK_INTERVAL
                )
            except asyncio.TimeoutError:
                continue


def start_service(name: str) -> None:
    """Start a service in a new process.
    
    Args:
        name: Service name to start
    """
    try:
        app = create_service(name)
        port = ServiceConfig.PORTS[name]
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=[str(Path(__file__).parent)]
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        logger.error(f"Service {name} failed: {str(e)}")
        sys.exit(1)


async def startup() -> None:
    """Start all services in dependency order."""
    ServiceConfig.shutdown_event = asyncio.Event()
    
    async with aiohttp.ClientSession() as session:
        for name in ServiceConfig.STARTUP_ORDER:
            logger.info(f"Starting {name} service...")
            
            process = mp.Process(
                target=start_service,
                args=(name,),
                name=f"{name}_service"
            )
            process.start()
            ServiceConfig.processes[name] = process
            
            if not await wait_for_service(session, name):
                logger.error(f"Service {name} failed to start")
                await shutdown()
                sys.exit(1)
            
            logger.info(f"Service {name} started successfully")
        
        ServiceConfig.health_check_task = asyncio.create_task(
            monitor_service_health()
        )


async def shutdown() -> None:
    """Shutdown all services gracefully."""
    if ServiceConfig.shutdown_event:
        ServiceConfig.shutdown_event.set()
    
    if ServiceConfig.health_check_task:
        try:
            await asyncio.wait_for(
                ServiceConfig.health_check_task,
                timeout=ServiceConfig.SHUTDOWN_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning("Health check task timed out during shutdown")
    
    for name, process in ServiceConfig.processes.items():
        logger.info(f"Stopping {name} service...")
        process.terminate()
        try:
            process.join(timeout=ServiceConfig.SHUTDOWN_TIMEOUT)
            if process.is_alive():
                process.kill()
        except Exception as e:
            logger.error(f"Error stopping {name} service: {str(e)}")


def handle_signal(signum: int, frame: Any) -> None:
    """Handle system signals for graceful shutdown."""
    logger.info(f"Received signal {signum}")
    asyncio.get_event_loop().run_until_complete(shutdown())
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    logger.info(f"Starting MicroColdSpray System v{__version__}")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start services
    try:
        if __name__ == '__main__':
            # Only set start method in main process
            if sys.platform == 'win32':
                mp.set_start_method('spawn')
            else:
                mp.set_start_method('fork')
        
        asyncio.run(startup())
        # Keep main process running
        signal.pause()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(shutdown())
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
