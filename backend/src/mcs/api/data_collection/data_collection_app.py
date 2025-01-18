"""Data collection API application."""

import os
import json
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from mcs.api.data_collection.data_collection_router import router
from mcs.api.data_collection.data_collection_service import DataCollectionService
from mcs.utils.errors import create_error  # noqa: F401 - used in error handlers and endpoints
from mcs.utils.health import ServiceHealth


def load_config() -> Dict[str, Any]:
    """Load configuration from file.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        config_path = os.path.join("backend", "config", "data_collection.json")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "version": "1.0.0",
                "service": {
                    "name": "data_collection",
                    "host": "0.0.0.0",
                    "port": 8005,
                    "log_level": "INFO",
                    "history_retention_days": 30
                },
                "components": {
                    "database": {
                        "version": "1.0.0",
                        "host": "localhost",
                        "port": 5432,
                        "user": "mcs_user",
                        "password": "mcs_password",
                        "database": "mcs_db",
                        "pool": {
                            "min_size": 2,
                            "max_size": 10,
                            "command_timeout": 60.0
                        }
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
        logger.info("Starting data collection service...")
        
        # Get service from app state
        service = app.state.service
        
        # Initialize service
        await service.initialize()
        
        # Prepare service after initialization
        await service.prepare()
        
        # Start service operations
        await service.start()
        
        logger.info("Data collection service started successfully")
        
        yield  # Server is running
        
        # Shutdown
        if hasattr(app.state, "service"):
            await app.state.service.shutdown()
            logger.info("Data collection service stopped")
            
    except Exception as e:
        error_msg = f"Data collection service startup failed: {e}"
        logger.error(error_msg)
        if hasattr(app.state, "service"):
            try:
                await app.state.service.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Failed to shutdown data collection service: {shutdown_error}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=error_msg
        )


def create_data_collection_service() -> FastAPI:
    """Create data collection application.
    
    Returns:
        FastAPI: Application instance
    """
    # Load config
    config = load_config()
    
    app = FastAPI(
        title="Data Collection API",
        description="API for collecting spray data",
        version=config["version"],
        docs_url="/",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
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
    
    # Create service with version from config
    service = DataCollectionService(version=config["version"])
    app.state.service = service
    
    # Add routes
    app.include_router(router)
    
    @app.get("/health", response_model=ServiceHealth)
    async def health() -> ServiceHealth:
        """Get API health status."""
        try:
            # Check if service exists and is initialized
            if not hasattr(app.state, "service"):
                return ServiceHealth(
                    status="starting",
                    service="data_collection",
                    version=config["version"],
                    is_running=False,
                    uptime=0.0,
                    error="Service initializing",
                    mode=config.get("mode", "normal"),
                    components={}
                )
            
            return await app.state.service.health()
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ServiceHealth(
                status="error",
                service="data_collection",
                version=config["version"],
                is_running=False,
                uptime=0.0,
                error=error_msg,
                mode=config.get("mode", "normal"),
                components={
                    "storage": {"status": "error", "error": error_msg},
                    "collector": {"status": "error", "error": error_msg}
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
            service = app.state.service
            
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
            await app.state.service.shutdown()
            return {"status": "stopped"}
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=str(e)
            )
    
    return app
