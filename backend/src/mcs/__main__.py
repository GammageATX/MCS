"""MicroColdSpray backend startup script."""

import os
import sys
import uvicorn
import asyncio
from loguru import logger

from mcs import (
    create_ui_app,
    create_config_service,
    create_state_service,
    create_process_service,
    create_data_collection_service
)
from mcs.api.communication.communication_app import create_communication_service


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


async def start_service(app, name: str, port: int):
    """Start a service with uvicorn."""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting {name} service on port {port}")
    await server.serve()


async def main():
    """Run all MCS services."""
    try:
        setup_logging()
        logger.info("Starting MCS services...")

        # Create all service apps
        services = [
            (create_ui_app(), "UI", 8000),
            (create_config_service(), "Config", 8001),
            (create_state_service(), "State", 8002),
            (create_communication_service(), "Communication", 8003),
            (create_process_service(), "Process", 8004),
            (create_data_collection_service(), "Data Collection", 8005)
        ]

        # Start all services concurrently
        await asyncio.gather(
            *(start_service(app, name, port) for app, name, port in services)
        )

    except Exception:
        logger.exception("Failed to start MCS services")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
