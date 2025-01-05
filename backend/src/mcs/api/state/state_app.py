"""State service application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from mcs.utils.errors import create_error  # noqa: F401 - used in error handlers and endpoints
from mcs.utils.health import ServiceHealth, HealthStatus, create_error_health
from mcs.api.state.state_service import StateService, load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        logger.info("Starting state service...")
        
        # Get service from app state
        service = app.state.service
        
        # Initialize and start service
        await service.initialize()
        await service.start()
        
        logger.info("State service started successfully")
        
        yield  # Server is running
        
        # Shutdown
        logger.info("Stopping state service...")
        if hasattr(app.state, "service") and app.state.service.is_running:
            await app.state.service.stop()
            logger.info("State service stopped successfully")
        
    except Exception as e:
        logger.error(f"State service startup failed: {e}")
        # Don't raise here - let the service start in degraded mode
        # The health check will show which components failed
        yield
        # Still try to stop service if it exists
        if hasattr(app.state, "service"):
            try:
                await app.state.service.stop()
            except Exception as stop_error:
                logger.error(f"Failed to stop state service: {stop_error}")


def create_state_service() -> FastAPI:
    """Create state service application.
    
    Returns:
        FastAPI: Application instance
    """
    # Load config
    config = load_config()
    version = config.get("version", "1.0.0")
    
    app = FastAPI(
        title="State Service",
        description="Service for managing system state",
        version=version,
        docs_url="/docs",
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
    
    # Create service
    service = StateService()
    app.state.service = service
    
    @app.get("/health", response_model=ServiceHealth)
    async def health() -> ServiceHealth:
        """Get service health status."""
        try:
            # Check if service exists and is initialized
            if not hasattr(app.state, "service"):
                return ServiceHealth(
                    status=HealthStatus.STARTING,
                    service="state",
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
            return create_error_health("state", version, error_msg)
    
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
    
    @app.get("/state")
    async def get_state():
        """Get current state."""
        return {
            "state": app.state.service.current_state,
            "timestamp": app.state.service.uptime
        }
    
    @app.get("/transitions")
    async def get_transitions():
        """Get valid state transitions."""
        return await app.state.service.get_valid_transitions()
    
    @app.post("/transition/{new_state}")
    async def transition(new_state: str):
        """Transition to new state."""
        return await app.state.service.transition_to(new_state)
    
    @app.get("/history")
    async def get_history(limit: int = None):
        """Get state history."""
        return await app.state.service.get_history(limit)
    
    return app
