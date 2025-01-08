"""UI service startup script."""

import uvicorn
from loguru import logger


def main():
    """Start UI service."""
    try:
        # Start server
        uvicorn.run(
            "mcs.ui.router:create_ui_app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True,
            factory=True
        )
    except Exception as e:
        logger.error(f"Failed to start UI service: {e}")
        raise


if __name__ == "__main__":
    main()
