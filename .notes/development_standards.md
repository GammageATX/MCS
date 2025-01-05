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

def create_example_service() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Each service should follow the naming pattern create_*_service(),
    except for the UI service which uses create_app().
    """
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
        # 1. Stop components
        # 2. Clear state
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
        # Basic service health check
        return create_simple_health(
            service_name=self.service_name,
            version=self.version,
            is_running=self.is_running,
            uptime=self.uptime
        )
    except Exception as e:
        return create_error_health(
            service_name=self.service_name,
            version=self.version,
            error_msg=str(e)
        )
```

For services with critical components:

```python
async def health(self) -> ServiceHealth:
    """Get service health status."""
    try:
        # Check critical components
        components = {
            "component_name": ComponentHealth(
                status=HealthStatus.OK if component.is_connected else HealthStatus.ERROR,
                error=None if component.is_connected else "Component disconnected"
            )
            for component in self._critical_components
        }
        
        # Overall status is error if any critical component is in error
        overall_status = HealthStatus.ERROR if any(
            c.status == HealthStatus.ERROR for c in components.values()
        ) else HealthStatus.OK
        
        return ServiceHealth(
            status=overall_status,
            service=self.service_name,
            version=self.version,
            is_running=self.is_running,
            uptime=self.uptime,
            error=None if overall_status == HealthStatus.OK else "Critical component error",
            components=components
        )
    except Exception as e:
        return create_error_health(self.service_name, self.version, str(e))
```

## Component Management

### Dependencies

- Create external clients first
- Initialize services in dependency order
- Handle optional dependencies gracefully

### Component Status

- Simple connected/disconnected tracking
- No automatic recovery attempts
- Clear status indication
- Maintain operation of available components

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
