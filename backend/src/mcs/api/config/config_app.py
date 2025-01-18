"""Configuration API application."""

import os
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import json

from mcs.utils.errors import create_error  # noqa: F401 - used in error handlers and endpoints
from mcs.utils.health import ServiceHealth, HealthStatus
from mcs.api.config.config_service import ConfigService
from mcs.api.config.endpoints.config_endpoints import router as config_router


def load_config() -> Dict[str, Any]:
    """Load configuration from file.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        config_path = os.path.join("backend", "config", "config.json")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "version": "1.0.0",
                "mode": "normal",
                "components": {
                    "file": {
                        "version": "1.0.0",
                        "base_path": os.path.join("backend", "config")
                    },
                    "format": {
                        "version": "1.0.0",
                        "enabled_formats": ["json"]
                    },
                    "schema": {
                        "version": "1.0.0",
                        "schema_path": os.path.join("backend", "config", "schemas")
                    }
                }
            }

        with open(config_path, "r") as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to load configuration: {str(e)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        logger.info("Starting config service...")
        
        # Get service from app state
        service = app.state.config_service
        
        # Initialize service
        await service.initialize()
        
        # Prepare service after initialization
        await service.prepare()
        
        # Start service operations
        await service.start()
        
        logger.info("Config service started successfully")
        
        yield  # Server is running
        
        # Shutdown
        if hasattr(app.state, "config_service"):
            await app.state.config_service.shutdown()
            logger.info("Config service stopped")
            
    except Exception as e:
        error_msg = f"Config service startup failed: {e}"
        logger.error(error_msg)
        if hasattr(app.state, "config_service"):
            try:
                await app.state.config_service.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Failed to shutdown config service: {shutdown_error}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=error_msg
        )


def create_config_service() -> FastAPI:
    """Create configuration service application.
    
    Returns:
        FastAPI: Application instance
    """
    # Load config
    config = load_config()
    
    app = FastAPI(
        title="Config API",
        description="API for managing configurations",
        version=config["version"],
        lifespan=lifespan,
        docs_url="/",  # Serve Swagger UI at root
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add error handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )
    
    # Create service and store in app state FIRST
    service = ConfigService(version=config["version"])
    app.state.config_service = service
    
    # THEN include router so it has access to the service
    app.include_router(config_router)
    
    @app.get("/health", response_model=ServiceHealth)
    async def health() -> ServiceHealth:
        """Get service health status."""
        try:
            # Check if service exists and is initialized
            if not hasattr(app.state, "config_service"):
                return ServiceHealth(
                    status=HealthStatus.STARTING,
                    service="config",
                    version=config["version"],
                    is_running=False,
                    uptime=0.0,
                    error="Service initializing",
                    components={}
                )
            
            return await app.state.config_service.health()
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ServiceHealth(
                status=HealthStatus.ERROR,
                service="config",
                version=config["version"],
                is_running=False,
                uptime=0.0,
                error=error_msg,
                components={
                    "file": {"status": HealthStatus.ERROR, "error": error_msg},
                    "format": {"status": HealthStatus.ERROR, "error": error_msg},
                    "schema": {"status": HealthStatus.ERROR, "error": error_msg}
                }
            )

    @app.post(
        "/start",
        responses={
            status.HTTP_409_CONFLICT: {"description": "Service already running"},
            status.HTTP_400_BAD_REQUEST: {"description": "Service not initialized"},
            status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service failed to start"}
        }
    )
    async def start():
        """Start service operations.
        
        If the service is not initialized, it will be initialized and prepared first.
        """
        try:
            service = app.state.config_service
            
            # Initialize and prepare if needed
            if not service.is_initialized:
                logger.info("Service needs initialization, initializing first...")
                await service.initialize()
                await service.prepare()
            
            # Start service operations
            await service.start()
            return {"status": "started"}
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=str(e)
            )

    @app.post(
        "/stop",
        responses={
            status.HTTP_409_CONFLICT: {"description": "Service not running"},
            status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service failed to stop"}
        }
    )
    async def stop():
        """Stop service operations and cleanup resources."""
        try:
            await app.state.config_service.shutdown()
            return {"status": "stopped"}
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=str(e)
            )
    
    return app
