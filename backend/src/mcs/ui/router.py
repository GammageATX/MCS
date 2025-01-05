"""Service UI router."""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
from fastapi import FastAPI, Request, status, Response
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
from mcs.utils.health import ServiceHealth, ComponentHealth


# Simple cache implementation
_cache: Dict[str, Any] = {}
_cache_times: Dict[str, float] = {}


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
    validation: AnyHttpUrl = Field("http://localhost:8006", description="Validation service URL")

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
                    if health.status == "starting":
                        health.is_running = True  # Service is alive but initializing
                    elif health.status == "ok":
                        health.is_running = True  # Service is fully operational
                    elif health.status == "error":
                        health.is_running = False  # Service has errors
                    else:
                        health.is_running = False  # Unknown state
                        
                    return health
                    
                return ServiceHealth(
                    status="error",
                    service=service_name or "unknown",
                    version="1.0.0",
                    is_running=False,
                    uptime=0.0,
                    error=f"Service returned status {response.status}",
                    mode="normal",
                    components={"main": ComponentHealth(status="error", error="Service unavailable")}
                )
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to {service_name} service: {e}")
        return ServiceHealth(
            status="error",
            service=service_name or "unknown",
            version="1.0.0",
            is_running=False,
            uptime=0.0,
            error=f"Connection error: {str(e)}",
            mode="normal",
            components={"main": ComponentHealth(status="error", error="Connection failed")}
        )
    except Exception as e:
        logger.error(f"Unexpected error checking {service_name} health: {e}")
        return ServiceHealth(
            status="error",
            service=service_name or "unknown",
            version="1.0.0",
            is_running=False,
            uptime=0.0,
            error=str(e),
            mode="normal",
            components={"main": ComponentHealth(status="error", error="Unexpected error")}
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
        dependencies[service] = health.status == "ok"
        
    return dependencies


def create_app() -> FastAPI:
    """Create FastAPI application."""
    try:
        app = FastAPI(
            title="MicroColdSpray Service Monitor",
            description="Service monitoring interface for MicroColdSpray system",
            version="1.0.0",
            docs_url="/docs",
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

        # Add GZip middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Setup templates
        templates_dir = Path(__file__).parent / "templates"
        if not templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")
        templates = Jinja2Templates(directory=templates_dir)
        templates.env.globals.update({
            "now": datetime.now,
            "version": app.version
        })

        # Setup static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
        else:
            logger.warning(f"Static directory not found: {static_dir}")

        # Store start time for uptime calculation
        start_time = datetime.now()

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
            """Render service monitor page."""
            try:
                # Check dependencies
                dependencies = await check_dependencies()
                
                return templates.TemplateResponse(
                    "monitoring/services.html",
                    {
                        "request": request,
                        "api_urls": get_api_urls().dict(),
                        "page_title": "Service Monitor",
                        "dependencies": dependencies
                    }
                )
            except Exception as e:
                logger.error(f"Failed to render service monitor page: {e}")
                raise create_error(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=f"Failed to render service monitor page: {str(e)}"
                )

        @app.get(
            "/health",
            response_model=ServiceHealth,
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
            }
        )
        async def health() -> ServiceHealth:
            """Get UI service health status."""
            try:
                uptime = (datetime.now() - start_time).total_seconds()
                return ServiceHealth(
                    status="ok",
                    service="ui",
                    version=app.version,
                    is_running=True,
                    uptime=uptime,
                    error=None,
                    components={"main": ComponentHealth(status="ok", error=None)}
                )
            except Exception as e:
                error_msg = f"Health check failed: {str(e)}"
                logger.error(error_msg)
                return ServiceHealth(
                    status="error",
                    service="ui",
                    version=app.version,
                    is_running=False,
                    uptime=0.0,
                    error=error_msg,
                    components={"main": ComponentHealth(status="error", error=error_msg)}
                )

        @app.get(
            "/monitoring/services/status",
            response_model=Dict[str, ServiceStatus],
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
            }
        )
        @cache(expire=5)  # Cache for 5 seconds
        async def get_services_status() -> Dict[str, ServiceStatus]:
            """Get status of all services."""
            services: Dict[str, ServiceStatus] = {}
            api_urls = get_api_urls()
            
            try:
                for service_name, url in {
                    "ui": api_urls.ui,
                    "config": api_urls.config,
                    "state": api_urls.state,
                    "communication": api_urls.communication,
                    "process": api_urls.process,
                    "data_collection": api_urls.data_collection,
                    "validation": api_urls.validation
                }.items():
                    health = await check_service_health(url, service_name)
                    port = int(str(url).split(":")[-1])  # Handle HttpUrl type
                    
                    # Map service status to display status
                    display_status = "ok"  # Default to ok
                    if health.is_running:
                        display_status = "ok"
                    elif health.status == "starting":
                        display_status = "starting"
                    elif health.status == "error":
                        display_status = "error"
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
