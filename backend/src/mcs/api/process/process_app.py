"""Process Service FastAPI Application"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import json
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from mcs.api.process.process_service import ProcessService
from mcs.api.process.endpoints.process_endpoints import router as process_router
from mcs.api.process.endpoints.pattern_endpoints import router as pattern_router
from mcs.api.process.endpoints.parameter_endpoints import router as parameter_router
from mcs.api.process.endpoints.sequence_endpoints import router as sequence_router
from mcs.api.process.endpoints.schema_endpoints import router as schema_router
from mcs.utils.errors import create_error


def load_config(config_path: str = "backend/config/process.json") -> Dict[str, Any]:
    """Load service configuration.

    Args:
        config_path: Path to config file

    Returns:
        Dict[str, Any]: Configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return json.load(f)


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
    
    # Create service instance with version from config
    service = ProcessService(version=config.get("version", "1.0.0"))
    app.state.service = service
    
    # Add routes
    app.include_router(process_router)
    app.include_router(pattern_router)
    app.include_router(parameter_router)
    app.include_router(sequence_router)
    app.include_router(schema_router)
    
    return app
