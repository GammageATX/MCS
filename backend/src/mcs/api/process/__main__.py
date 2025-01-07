"""Process Service Entry Point

This module serves as the entry point for the Process service.
"""

import logging
import os
from typing import Dict

import uvicorn
import yaml

from mcs.api.process.process_app import create_process_service  # noqa: F401 - used in string form for uvicorn
from mcs.utils.errors import create_error


logger = logging.getLogger(__name__)


def load_config(config_path: str = "backend/config/process.yaml") -> Dict:
    """Load service configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict containing service configuration
        
    Raises:
        HTTPException if config file not found or invalid
    """
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "version": "1.0.0",
                "service": {
                    "name": "process",
                    "host": "0.0.0.0",
                    "port": 8004,
                    "log_level": "INFO"
                }
            }
            
        with open(config_path) as f:
            return yaml.safe_load(f)
            
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        raise create_error(
            status_code=500,
            message=f"Failed to load configuration: {str(e)}"
        )


def main():
    """Run the Process service."""
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Load config
    config = load_config()
    service_config = config.get("service", {})
    
    # Get host/port from environment or config
    host = os.getenv("HOST", service_config.get("host", "0.0.0.0"))
    port = int(os.getenv("PORT", service_config.get("port", 8004)))

    # Run service
    uvicorn.run(
        "mcs.api.process.process_app:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["backend/src"],
        factory=True
    )


if __name__ == "__main__":
    main()
