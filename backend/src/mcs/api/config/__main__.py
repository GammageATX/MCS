"""Configuration service startup script."""

import os
import sys
import yaml
import uvicorn
from loguru import logger


def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join("logs", "config")
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
        os.path.join(log_dir, "config_service.log"),
        rotation="1 day",
        retention="30 days",
        format=file_format,
        level="DEBUG",
        enqueue=True,
        compression="zip"
    )


def main():
    """Run configuration service."""
    try:
        # Setup logging
        setup_logging()
        logger.info("Starting configuration service...")
        
        # Load config for service settings
        try:
            with open("backend/config/config.yaml", "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config, using defaults: {e}")
            config = {
                "service": {
                    "host": "0.0.0.0",
                    "port": 8001,
                    "log_level": "INFO"
                }
            }
        
        # Run service using config values
        uvicorn.run(
            "mcs.api.config.config_app:create_config_service",
            host=config["service"]["host"],
            port=config["service"]["port"],
            log_level=config["service"]["log_level"].lower(),
            reload=True,  # Enable auto-reload for development
            reload_dirs=[os.path.dirname(os.path.dirname(__file__))]  # Watch mcs package
        )

    except Exception as e:
        logger.exception(f"Failed to start configuration service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
