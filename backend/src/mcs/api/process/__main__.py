"""Main entry point for process service."""

import os
import sys
import yaml
import uvicorn
from loguru import logger

from mcs.api.process.process_app import create_process_service  # noqa: F401 - used in string form for uvicorn
from mcs.utils.errors import create_error


def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join("logs", "process")
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
        os.path.join(log_dir, "process.log"),
        rotation="1 day",
        retention="30 days",
        format=file_format,
        level="DEBUG",
        enqueue=True,
        compression="zip"
    )


def load_config():
    """Load service configuration."""
    try:
        config_path = os.path.join("backend", "config", "process.yaml")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "service": {
                    "version": "1.0.0",
                    "host": "0.0.0.0",
                    "port": 8004,
                    "history_retention_days": 30
                }
            }

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise create_error(
            status_code=500,
            message=f"Failed to load configuration: {str(e)}"
        )


def main():
    """Run process service."""
    try:
        # Setup logging
        setup_logging()
        
        # Load config
        config = load_config()
        
        # Get service config
        service_config = config.get("service", {})
        host = service_config.get("host", "localhost")
        port = service_config.get("port", 8003)
        
        # Start service
        uvicorn.run(
            "mcs.api.process.process_app:create_process_service",
            host=host,
            port=port,
            reload=False,
            workers=1
        )
        
    except Exception as e:
        logger.error(f"Failed to start process service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
