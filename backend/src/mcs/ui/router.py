"""UI application router."""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, Response, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, AnyHttpUrl
from loguru import logger
import aiohttp
import time
from functools import wraps

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus


# Simple cache implementation
_cache: Dict[str, Any] = {}
_cache_times: Dict[str, float] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        logger.info("Starting UI application...")
        ui_app = app.state.ui_app
        await ui_app.initialize()
        await ui_app.start()
        yield
        if ui_app.is_running:
            await ui_app.stop()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        yield


class UIApp:
    """UI application for system monitoring and control."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize UI application."""
        self._app_name = "ui"
        self._version = version
        self._is_running = False
        self._is_initialized = False
        self._start_time = None
        self._api_urls = None

    @property
    def version(self) -> str:
        """Get application version."""
        return self._version

    @property
    def app_name(self) -> str:
        """Get application name."""
        return self._app_name

    @property
    def is_running(self) -> bool:
        """Get application running state."""
        return self._is_running

    @property
    def is_initialized(self) -> bool:
        """Get application initialization state."""
        return self._is_initialized

    @property
    def uptime(self) -> float:
        """Get application uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize application."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.app_name} application already running"
                )

            # Initialize API URLs
            self._api_urls = get_api_urls()

            self._is_initialized = True
            logger.info(f"{self.app_name} application initialized")

        except Exception as e:
            error_msg = f"Failed to initialize {self.app_name} application: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def start(self) -> None:
        """Start application."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.app_name} application already running"
                )

            if not self.is_initialized:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.app_name} application not initialized"
                )

            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.app_name} application started")

        except Exception as e:
            self._is_running = False
            self._start_time = None
            error_msg = f"Failed to start {self.app_name} application: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop(self) -> None:
        """Stop application."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.app_name} application not running"
                )

            self._is_initialized = False
            self._is_running = False
            self._start_time = None
            logger.info(f"{self.app_name} application stopped")

        except Exception as e:
            error_msg = f"Error during {self.app_name} application shutdown: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get application health status."""
        try:
            if not self.is_running:
                return ServiceHealth(
                    status=HealthStatus.ERROR,
                    service=self.app_name,
                    version=self.version,
                    is_running=False,
                    uptime=0.0,
                    error=f"{self.app_name} application not running",
                    mode="normal",
                    components={
                        "main": ComponentHealth(
                            status=HealthStatus.ERROR,
                            error="Service unavailable"
                        )
                    }
                )

            return ServiceHealth(
                status=HealthStatus.OK,
                service=self.app_name,
                version=self.version,
                is_running=True,
                uptime=self.uptime,
                mode="normal",
                error=None,
                components={
                    "main": ComponentHealth(
                        status=HealthStatus.OK,
                        error=None
                    )
                }
            )

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return ServiceHealth(
                status=HealthStatus.ERROR,
                service=self.app_name,
                version=self.version,
                is_running=False,
                uptime=0.0,
                error=error_msg,
                mode="normal",
                components={
                    "main": ComponentHealth(
                        status=HealthStatus.ERROR,
                        error=error_msg
                    )
                }
            )


def cache(expire_seconds: int = 5):
    """Simple cache decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            now = time.time()
            
            # Check if cached and not expired
            if key in _cache and now - _cache_times[key] < expire_seconds:
                return _cache[key]
                
            # Get fresh value
            result = await func(*args, **kwargs)
            _cache[key] = result
            _cache_times[key] = now
            return result
        return wrapper
    return decorator


class DetailedComponentHealth(ComponentHealth):
    """Extended component health with more details."""
    last_check: datetime = Field(default_factory=datetime.now)
    check_count: int = Field(default=0)
    consecutive_failures: int = Field(default=0)


class ApiUrls(BaseModel):
    """API URLs configuration model."""
    ui: AnyHttpUrl = Field("http://localhost:8000", description="UI service URL")
    config: AnyHttpUrl = Field("http://localhost:8001", description="Config service URL")
    state: AnyHttpUrl = Field("http://localhost:8002", description="State service URL")
    communication: AnyHttpUrl = Field("http://localhost:8003", description="Communication service URL")
    process: AnyHttpUrl = Field("http://localhost:8004", description="Process service URL")
    data_collection: AnyHttpUrl = Field("http://localhost:8005", description="Data collection service URL")

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True


class ServiceStatus(BaseModel):
    """Service status model."""
    name: str = Field(..., description="Service name")
    port: int = Field(..., description="Service port")
    status: str = Field(..., description="Service status")
    uptime: float = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="Service version")
    mode: Optional[str] = Field(None, description="Service mode")
    error: Optional[str] = Field(None, description="Error message if any")
    components: Optional[Dict[str, ComponentHealth]] = Field(None, description="Component health statuses")


def get_api_urls() -> ApiUrls:
    """Get API URLs for templates."""
    return ApiUrls()


async def check_service_health(url: str, service_name: str = None) -> ServiceHealth:
    """Check service health status.
    
    Args:
        url: Service base URL
        service_name: Name of the service (optional)
        
    Returns:
        ServiceHealth with status details
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health", timeout=2) as response:
                if response.status == 200:
                    data = await response.json()
                    # Ensure we have a valid ServiceHealth object
                    health = ServiceHealth(**data)
                    
                    # Update running status based on actual service state
                    if health.status == HealthStatus.STARTING:
                        health.is_running = True  # Service is alive but initializing
                    elif health.status == HealthStatus.OK:
                        health.is_running = True  # Service is fully operational
                    elif health.status == HealthStatus.ERROR:
                        health.is_running = False  # Service has errors
                    else:
                        health.is_running = False  # Unknown state
                        
                    return health
                    
                return ServiceHealth(
                    status=HealthStatus.ERROR,
                    service=service_name or "unknown",
                    version="1.0.0",
                    is_running=False,
                    uptime=0.0,
                    mode="normal",
                    error=f"Service returned status {response.status}",
                    components={"main": ComponentHealth(status=HealthStatus.ERROR, error="Service unavailable")}
                )
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to {service_name} service: {e}")
        return ServiceHealth(
            status=HealthStatus.ERROR,
            service=service_name or "unknown",
            version="1.0.0",
            is_running=False,
            uptime=0.0,
            mode="normal",
            error=f"Connection error: {str(e)}",
            components={"main": ComponentHealth(status=HealthStatus.ERROR, error="Connection failed")}
        )
    except Exception as e:
        logger.error(f"Unexpected error checking {service_name} health: {e}")
        return ServiceHealth(
            status=HealthStatus.ERROR,
            service=service_name or "unknown",
            version="1.0.0",
            is_running=False,
            uptime=0.0,
            mode="normal",
            error=str(e),
            components={"main": ComponentHealth(status=HealthStatus.ERROR, error="Unexpected error")}
        )


async def check_dependencies() -> Dict[str, bool]:
    """Check critical service dependencies."""
    dependencies = {
        "config": False,  # Config service is critical
        "state": False    # State service is critical
    }
    api_urls = get_api_urls()
    
    for service in dependencies.keys():
        url = getattr(api_urls, service)
        health = await check_service_health(url, service)
        dependencies[service] = health.status == HealthStatus.OK
        
    return dependencies


def create_ui_app() -> FastAPI:
    """Create UI application.
    
    Returns:
        FastAPI application instance
    """
    try:
        app = FastAPI(
            title="MicroColdSpray Monitor",
            description="System monitoring interface for MicroColdSpray",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
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

        # Add GZip middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Create UI app instance
        ui_app = UIApp(version=app.version)
        app.state.ui_app = ui_app

        # Mount static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"Mounted static files from {static_dir}")
        else:
            logger.warning(f"Static directory not found: {static_dir}")

        # Setup templates
        templates_dir = Path(__file__).parent / "templates"
        if templates_dir.exists():
            templates = Jinja2Templates(directory=str(templates_dir))
            templates.env.globals.update({
                "now": datetime.now,
                "version": app.version
            })
            app.state.templates = templates
            logger.info(f"Initialized templates from {templates_dir}")
        else:
            logger.error(f"Templates directory not found: {templates_dir}")
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

        @app.get('/favicon.ico', include_in_schema=False)
        async def favicon():
            """Serve favicon."""
            favicon_path = static_dir / 'favicon.ico'
            if favicon_path.exists():
                return FileResponse(favicon_path)
            return Response(status_code=404)

        @app.get(
            "/",
            response_class=HTMLResponse,
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
                status.HTTP_404_NOT_FOUND: {"description": "Template not found"}
            }
        )
        async def index(request: Request) -> HTMLResponse:
            """Render monitor page."""
            try:
                # Check dependencies
                dependencies = await check_dependencies()
                
                return request.app.state.templates.TemplateResponse(
                    "monitoring/services.html",
                    {
                        "request": request,
                        "api_urls": ui_app._api_urls.dict(),
                        "page_title": "Service Monitor",
                        "dependencies": dependencies
                    }
                )
            except Exception as e:
                logger.error(f"Failed to render monitor page: {e}")
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=f"Failed to render monitor page: {str(e)}"
                )

        @app.get(
            "/health",
            response_model=ServiceHealth,
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
            }
        )
        async def health(
            ui_app: UIApp = Depends(lambda r: r.app.state.ui_app)
        ) -> ServiceHealth:
            """Get UI application health status."""
            return await ui_app.health()

        @app.get(
            "/monitoring/services/status",
            response_model=Dict[str, ServiceStatus],
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
            }
        )
        @cache(expire_seconds=5)  # Cache for 5 seconds
        async def get_services_status() -> Dict[str, ServiceStatus]:
            """Get status of all services."""
            services: Dict[str, ServiceStatus] = {}
            api_urls = ui_app._api_urls
            
            try:
                for service_name, url in {
                    "ui": api_urls.ui,
                    "config": api_urls.config,
                    "state": api_urls.state,
                    "communication": api_urls.communication,
                    "process": api_urls.process,
                    "data_collection": api_urls.data_collection
                }.items():
                    health = await check_service_health(url, service_name)
                    port = int(str(url).split(":")[-1])  # Handle HttpUrl type
                    
                    # Map health status to display status
                    if health.is_running:
                        display_status = "ok" if health.status == HealthStatus.OK else str(health.status)
                    else:
                        display_status = "stopped"
                    
                    services[service_name] = ServiceStatus(
                        name=service_name,
                        port=port,
                        status=display_status,
                        uptime=health.uptime,
                        version=health.version,
                        mode=health.mode,
                        error=health.error,
                        components=health.components
                    )

                return services
            except Exception as e:
                logger.error(f"Failed to get services status: {e}")
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=f"Failed to get services status: {str(e)}"
                )

        return app

    except Exception as e:
        logger.error(f"Failed to create UI application: {e}")
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to create UI application: {str(e)}"
        )
