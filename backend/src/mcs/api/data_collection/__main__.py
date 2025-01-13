"""Main entry point for data collection service."""

import os
import sys
import json
import uvicorn
from loguru import logger

from mcs.api.data_collection.data_collection_app import create_data_collection_service  # noqa: F401 - used in string form for uvicorn
from mcs.utils.errors import create_error


def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join("logs", "data_collection")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Remove default handler
    logger.remove()
    
    # Get log level from environment or use default
    console_level = os.getenv("MCS_LOG_LEVEL", "INFO").upper()
    file_level = os.getenv("MCS_FILE_LOG_LEVEL", "DEBUG").upper()
    
    # Add console handler with color
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, format=log_format, level=console_level, enqueue=True)
    
    # Add file handler with rotation
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    logger.add(
        os.path.join(log_dir, "data_collection.log"),
        rotation="1 day",
        retention="30 days",
        format=file_format,
        level=file_level,
        enqueue=True,
        compression="zip"
    )


def load_config():
    """Load service configuration."""
    try:
        config_path = os.path.join("backend", "config", "data_collection.json")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "service": {
                    "version": "1.0.0",
                    "host": "0.0.0.0",
                    "port": 8004,
                    "log_level": "INFO",
                    "history_retention_days": 30
                }
            }

        with open(config_path, 'r') as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise create_error(
            status_code=500,
            message=f"Failed to load configuration: {str(e)}"
        )


def main():
    """Run data collection service."""
    try:
        # Setup logging
        setup_logging()
        logger.info("Starting data collection service...")
        
        # Load config
        config = load_config()
        
        # Get config from environment or use defaults
        host = os.getenv("DATA_COLLECTION_HOST", config["service"].get("host", "0.0.0.0"))
        port = int(os.getenv("DATA_COLLECTION_PORT", config["service"].get("port", 8004)))
        
        # Log startup configuration
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info("Mode: development (reload enabled)")
        
        # Run service with standardized configuration
        uvicorn.run(
            "mcs.api.data_collection.data_collection_app:create_data_collection_service",
            host=host,
            port=port,
            reload=True,
            factory=True,
            reload_dirs=["backend/src"],
            log_level="debug"
        )

    except Exception as e:
        logger.exception(f"Failed to start data collection service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
