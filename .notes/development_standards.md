# Development Standards

## Service Implementation Pattern

### Base Service Structure
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        logger.info("Starting service...")
        service = app.state.service
        await service.initialize()
        await service.start()
        yield
        if service.is_running:
            await service.stop()
    except Exception as e:
        logger.error(f"Service startup failed: {e}")
        yield

def create_service() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Service Name",
        description="Service description",
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
    
    return app
```

### Service Lifecycle Methods

#### Initialization
1. `__init__`
   - Set basic properties only
   - No component creation or config loading
   ```python
   self._service_name: str
   self._version: str = "1.0.0"
   self._is_running: bool = False
   self._start_time: Optional[datetime] = None
   ```

2. `initialize()`
   - Load configuration
   - Create component services
   - Initialize in dependency order
   ```python
   async def initialize(self):
       await self._load_config()
       await self._create_components()
       await self._initialize_components()
   ```

3. `start()`
   - Check prerequisites
   - Start components in order
   - Set service state
   ```python
   async def start(self):
       if self.is_running:
           raise create_error(
               status_code=status.HTTP_409_CONFLICT,
               message="Service already running"
           )
       # Start components
       self._is_running = True
   ```

#### Shutdown
```python
async def stop(self):
    """Stop service."""
    try:
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_409_CONFLICT,
                message="Service not running"
            )
        # 1. Unregister from external services
        # 2. Clear callbacks
        # 3. Reset state
        self._is_running = False
        self._start_time = None
    except Exception as e:
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to stop: {str(e)}"
        )
```

### Error Handling
1. Use `create_error` utility:
```python
raise create_error(
    status_code=status.HTTP_400_BAD_REQUEST,
    message="Error description"
)
```

2. Status Codes:
- 400: Bad Request (Client errors)
- 404: Not Found
- 409: Conflict (State conflicts)
- 422: Validation Error
- 500: Internal Error
- 503: Service Unavailable

### Health Checks
```python
async def health(self) -> ServiceHealth:
    """Get service health status."""
    try:
        component_healths = await self._get_component_health()
        return ServiceHealth(
            status="ok" if all(h.status == "ok" for h in component_healths.values()) else "error",
            service=self.service_name,
            version=self.version,
            is_running=self.is_running,
            uptime=self.uptime,
            components=component_healths
        )
    except Exception as e:
        return ServiceHealth(
            status="error",
            service=self.service_name,
            error=str(e)
        )
```

## Component Management

### Dependencies
- Create external clients first
- Initialize services in dependency order
- Handle optional dependencies gracefully

### Self-Healing
1. Track failed components separately
2. Attempt recovery during health checks
3. Continue with partial functionality when possible
4. Log all recovery attempts

## Testing Requirements
1. One test file per service
2. Independent test cases
3. Clear test names
4. Proper cleanup after tests

## Documentation Requirements
1. API Documentation
   - OpenAPI specifications
   - Endpoint documentation
   - Type definitions

2. Code Documentation
   - Clear docstrings
   - Type hints
   - Complex logic explanation

3. Component Documentation
   - Dependencies
   - Configuration options
   - Error scenarios 