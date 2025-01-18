"""Communication API application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from typing import AsyncGenerator

from mcs.utils.errors import create_error  # noqa: F401 - used in error handlers and endpoints
from mcs.utils.health import ServiceHealth, HealthStatus, create_error_health
from mcs.api.communication.endpoints import router as state_router
from mcs.api.communication.endpoints.equipment import router as equipment_router
from mcs.api.communication.endpoints.motion import router as motion_router
from mcs.api.communication.communication_service import CommunicationService, load_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application lifespan events.
    
    The lifespan context manager handles:
    1. Service initialization during startup
    2. Service preparation after initialization
    3. Service startup after preparation
    4. Service shutdown on application exit
    """
    try:
        logger.info("Starting communication service...")
        
        # Get service from app state
        service = app.state.service
        
        # Initialize service
        await service.initialize()
        
        # Prepare service (handle operations requiring running dependencies)
        await service.prepare()
        
        # Start service operations
        await service.start()
        
        yield
        
        # Shutdown service
        await service.shutdown()
        logger.info("Communication service stopped successfully")
        
    except Exception as e:
        error_msg = f"Communication service startup failed: {str(e)}"
        logger.error(error_msg)
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=error_msg
        )


def create_communication_service() -> FastAPI:
    """Create communication service application.
    
    Returns:
        FastAPI: Application instance
    """
    # Load config
    config = load_config()
    version = config.get("version", "1.0.0")
    
    app = FastAPI(
        title="Communication Service",
        description="Service for hardware communication",
        version=version,
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

    # Add routers
    app.include_router(state_router)
    app.include_router(equipment_router)
    app.include_router(motion_router)

    # Create service
    service = CommunicationService(config)
    app.state.service = service

    @app.get("/health", response_model=ServiceHealth)
    async def health() -> ServiceHealth:
        """Get service health status."""
        try:
            if not hasattr(app.state, "service"):
                return ServiceHealth(
                    status=HealthStatus.STARTING,
                    service="communication",
                    version=version,
                    is_running=False,
                    uptime=0.0,
                    error="Service initializing",
                    components={}
                )
            return await app.state.service.health()
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health("communication", version, error_msg)

    @app.post("/start")
    async def start():
        """Start service."""
        await app.state.service.start()
        return {"status": "started"}

    @app.post("/stop")
    async def stop():
        """Stop service."""
        await app.state.service.stop()
        return {"status": "stopped"}

    return app
