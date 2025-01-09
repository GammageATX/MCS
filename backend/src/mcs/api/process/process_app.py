"""Process Service FastAPI Application"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

import yaml
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from mcs.api.process.process_service import ProcessService
from mcs.api.process.endpoints.process_endpoints import router as process_router
from mcs.api.process.endpoints.pattern_endpoints import router as pattern_router
from mcs.api.process.endpoints.parameter_endpoints import router as parameter_router
from mcs.api.process.endpoints.sequence_endpoints import router as sequence_router
from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, HealthStatus


logger = logging.getLogger(__name__)


def load_config(config_path: str = "backend/config/process.yaml") -> Dict:
    """Load service configuration from YAML file."""
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events.
    
    The lifespan context manager handles:
    1. Service initialization during startup
    2. Service preparation after initialization
    3. Service startup after preparation
    4. Service shutdown on application exit
    """
    try:
        logger.info("Starting process service...")
        
        # Get service from app state
        service = app.state.service
        
        # Initialize service
        await service.initialize()
        
        # Prepare service (handle operations requiring running dependencies)
        await service.prepare()
        
        # Start service operations
        await service.start()
        
        logger.info("Process service started successfully")
        
        yield  # Server is running
        
        # Shutdown service
        if hasattr(app.state, "service"):
            await app.state.service.shutdown()
            logger.info("Process service stopped successfully")
            
    except Exception as e:
        error_msg = f"Process service startup failed: {str(e)}"
        logger.error(error_msg)
        if hasattr(app.state, "service"):
            try:
                await app.state.service.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Failed to shutdown process service: {shutdown_error}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=error_msg
        )


def create_process_service() -> FastAPI:
    """Create process service application."""
    # Load config
    config = load_config()
    
    app = FastAPI(
        title="Process Service",
        description="Service for managing process execution and control",
        version=config["version"],
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

    # Create service and store in app state
    service = ProcessService(version=config["version"])
    app.state.service = service

    @app.get("/health", response_model=ServiceHealth)
    async def health() -> ServiceHealth:
        """Get service health status."""
        try:
            # Check if service exists and is initialized
            if not hasattr(app.state, "service"):
                return ServiceHealth(
                    status=HealthStatus.STARTING,
                    service="process",
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
                status=HealthStatus.ERROR,
                service="process",
                version=config["version"],
                is_running=False,
                uptime=0.0,
                error=error_msg,
                mode=config.get("mode", "normal"),
                components={
                    "action": {"status": HealthStatus.ERROR, "error": error_msg},
                    "parameter": {"status": HealthStatus.ERROR, "error": error_msg},
                    "pattern": {"status": HealthStatus.ERROR, "error": error_msg},
                    "sequence": {"status": HealthStatus.ERROR, "error": error_msg},
                    "schema": {"status": HealthStatus.ERROR, "error": error_msg}
                }
            )

    # Include routers
    app.include_router(process_router)  # Base router for /health etc
    app.include_router(pattern_router, prefix="/patterns")
    app.include_router(parameter_router, prefix="/parameters")
    app.include_router(sequence_router, prefix="/sequences")

    # Debug: Print all registered routes
    logger.info("Registered routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            logger.info(f"HTTP Route: {route.path} [{','.join(route.methods)}]")
        else:
            logger.info(f"WebSocket Route: {route.path}")

    return app
