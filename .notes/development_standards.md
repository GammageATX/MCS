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

Each service must implement the following lifecycle methods to ensure proper initialization, dependency management, and cleanup:

#### 1. Basic Properties (`__init__`)

- Set basic properties only
- No component creation or config loading

```python
def __init__(self, config: Dict[str, Any]):
    self._service_name: str
    self._version: str = "1.0.0"
    self._is_running: bool = False
    self._start_time: Optional[datetime] = None
    self._config = config
    
    # Initialize service references as None
    self._component1 = None
    self._component2 = None
```

#### 2. One-time Setup (`initialize()`)

- Basic setup that doesn't require running dependencies
- Create service instances
- Load configurations

```python
async def initialize(self) -> None:
    """One-time initialization and basic setup.
    
    The initialize method handles operations that don't require running dependencies:
    1. Creating service instances
    2. Loading configurations
    3. Basic setup
    """
    try:
        # Create core services
        self._component1 = Component1Service(self._config)
        await self._component1.initialize()
        
        # Create remaining services
        self._component2 = Component2Service(self._config)
        
        logger.info(f"{self.service_name} service basic initialization complete")
    except Exception as e:
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to initialize: {str(e)}"
        )
```

#### 3. Dependency Setup (`prepare()`)

- Setup that requires running dependencies
- Start core services needed by others
- Initialize services that need running dependencies

```python
async def prepare(self) -> None:
    """Prepare service for operation.
    
    The prepare method handles operations that require running dependencies:
    1. Starting core services needed by others
    2. Initializing dependent services
    3. Setting up service interconnections
    """
    try:
        # 1. Start core services needed by others
        await self._component1.start()
        
        # 2. Initialize and start dependent services
        await self._component2.initialize()
        await self._component2.start()
        
        # 3. Set up interconnections
        self._component2.set_dependency(self._component1)
        
        logger.info(f"{self.service_name} service preparation complete")
    except Exception as e:
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to prepare: {str(e)}"
        )
```

#### 4. Start Operations (`start()`)

- Begin actual service operations
- Start remaining services
- Set service state

```python
async def start(self) -> None:
    """Start service operations.
    
    The start method handles:
    1. Starting remaining services
    2. Beginning actual operations
    """
    try:
        if self.is_running:
            raise create_error(
                status_code=status.HTTP_409_CONFLICT,
                message="Service already running"
            )

        # Ensure services are prepared
        if not all([self._component1, self._component2]):
            await self.initialize()
            await self.prepare()

        # Set service state
        self._is_running = True
        self._start_time = datetime.now()
        
        logger.info(f"{self.service_name} service started successfully")
    except Exception as e:
        self._is_running = False
        self._start_time = None
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to start: {str(e)}"
        )
```

#### 5. Stop Operations (`stop()`)

- Stop service operations but allow restart
- Stop components in reverse dependency order
- Clear initialized state

```python
async def stop(self) -> None:
    """Stop service components but maintain initialization state.
    
    The stop method:
    1. Stops all services in reverse dependency order
    2. Maintains service references but clears initialized state
    3. Allows restart via start() which will reinitialize
    """
    try:
        if not self.is_running:
            raise create_error(
                status_code=status.HTTP_409_CONFLICT,
                message="Service not running"
            )

        # Stop in reverse dependency order
        if self._component2:
            await self._component2.stop()
        if self._component1:
            await self._component1.stop()

        # Reset service state
        self._is_running = False
        self._start_time = None
        
        # Clear initialized state so start() will reinitialize
        self._component1 = None
        self._component2 = None
        
        logger.info(f"{self.service_name} service stopped")
    except Exception as e:
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to stop: {str(e)}"
        )
```

#### 6. Full Cleanup (`shutdown()`)

- Complete service cleanup
- Stop if running
- Clear all resources

```python
async def shutdown(self) -> None:
    """Shutdown service and cleanup resources.
    
    The shutdown method:
    1. Stops all services if running
    2. Cleans up resources and references
    3. Requires re-initialization to use again
    """
    try:
        # Stop if running
        if self.is_running:
            await self.stop()
        else:
            # Clear service references even if not running
            self._component1 = None
            self._component2 = None

        logger.info(f"{self.service_name} service shutdown complete")
    except Exception as e:
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"Failed to shutdown: {str(e)}"
        )
```

#### FastAPI Integration

Services should use FastAPI's lifespan for proper lifecycle management:

```python
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
        logger.info("Starting service...")
        
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
        logger.info("Service stopped successfully")
        
    except Exception as e:
        error_msg = f"Service startup failed: {str(e)}"
        logger.error(error_msg)
        raise create_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=error_msg
        )
```

This lifecycle pattern ensures:

- Clear separation between initialization and runtime dependencies
- Proper dependency ordering during startup and shutdown
- Clean restart capability
- Proper resource cleanup

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

### Service Deployment Patterns

#### Development Mode

- Uses factory pattern with hot reload
- Enabled via MCS_ENV=development
- Watches source directories for changes

#### Production Mode

- Uses single app instance
- Standard Uvicorn deployment
- No reload functionality

### Service Entry Point Pattern

Each service should have a `__main__.py` that follows this structure:

```python
"""Main entry point for service."""

import os
import sys
import yaml
import uvicorn
from loguru import logger
from mcs.utils.errors import create_error

def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join("logs", "service_name")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Remove default handler
    logger.remove()
    
    # Get log level from environment or use default
    console_level = os.getenv("MCS_LOG_LEVEL", "INFO").upper()
    file_level = os.getenv("MCS_FILE_LOG_LEVEL", "DEBUG").upper()
    
    # Add console handler with color
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, format=log_format, level=console_level, enqueue=True)
    
    # Add file handler with rotation
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    logger.add(
        os.path.join(log_dir, "service.log"),
        rotation="1 day",
        retention="30 days",
        format=file_format,
        level=file_level,
        enqueue=True,
        compression="zip"
    )

def load_config():
    """Load service configuration."""
    try:
        config_path = os.path.join("backend", "config", "service.yaml")
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "service": {
                    "version": "1.0.0",
                    "host": "0.0.0.0",
                    "port": 8000,
                    "history_retention_days": 30
                }
            }

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise create_error(
            status_code=500,
            message=f"Failed to load configuration: {str(e)}"
        )

def main():
    """Run service in development mode."""
    try:
        # Setup logging
        setup_logging()
        logger.info("Starting service in development mode...")
        
        # Load config
        config = load_config()
        service_config = config.get("service", {})
        
        # Get config from environment or use defaults
        host = os.getenv("SERVICE_HOST", service_config.get("host", "0.0.0.0"))
        port = int(os.getenv("SERVICE_PORT", service_config.get("port", 8000)))
        
        # Log startup configuration
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info("Mode: development (reload enabled)")
        
        # Run service with development configuration
        uvicorn.run(
            "mcs.api.service.app:create_service",
            host=host,
            port=port,
            reload=True,
            factory=True,
            reload_dirs=["backend/src"],
            log_level="debug"
        )

    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

## Naming Conventions

### Service Methods
1. State Control Methods
   - Binary state changes: `set_<component>_state(state: bool)`
   - Example: `set_mechanical_pump_state(True)`, `set_shutter_state(False)`

2. Value Control Methods
   - Numeric values: `set_<component>_<value_type>(value: float)`
   - Include units in documentation
   - Example: `set_main_flow_rate(flow_rate: float)  # flow_rate in SLPM`

3. Component Selection
   - Use `set_<component>_state` for component selection
   - Example: `set_nozzle_state(nozzle_id: int)`

### Model Names
1. Request Models
   - Suffix: `Request`
   - Example: `GasFlowRequest`, `VacuumPumpRequest`
   - Include clear field descriptions with units

2. State Models
   - Suffix: `State`
   - Example: `GasState`, `VacuumState`
   - Include units in field descriptions
   - Use `_state` suffix for boolean fields

3. Field Names
   - Boolean states: `<component>_state: bool`
   - Numeric values: `<component>_<value_type>: float`
   - Include units in descriptions
   - Optional values should use Optional[type]

### API Endpoints
1. State Control
   - GET for state retrieval
   - POST for value updates
   - PUT for state changes
   - WebSocket for real-time updates

2. Error Handling
   - Use `create_error` utility
   - Include descriptive error messages
   - Log errors with appropriate level

# Frontend Standards

## UI Framework

Material-UI (MUI) is our chosen UI framework for the following reasons:
- Well-established and mature library with extensive documentation
- Complete component ecosystem
- Consistent design language
- Strong TypeScript support
- Built-in theming system
- Responsive design out of the box

### Component Guidelines

1. **Layout Components**
   - Use MUI Grid and Box for layouts
   - Implement responsive designs using MUI breakpoints
   - Follow Material Design spacing guidelines

2. **Form Components**
   - Use MUI form components (TextField, Select, etc.)
   - Implement proper form validation
   - Show clear error states
   - Use loading states during submissions

3. **Data Display**
   - Use MUI DataGrid for data tables
   - Implement proper loading states
   - Handle empty states gracefully
   - Show error states clearly

4. **Feedback Components**
   - Use Snackbars for notifications
   - Show loading with CircularProgress/LinearProgress
   - Use Dialog for confirmations
   - Display errors with Alert components

5. **Navigation**
   - Use AppBar for main navigation
   - Implement Drawer for side navigation
   - Use Breadcrumbs for nested navigation
   - Handle route transitions smoothly

### Theme Configuration

```typescript
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',  // Main brand color
    },
    secondary: {
      main: '#dc004e',  // Secondary actions
    },
    error: {
      main: '#f44336',  // Error states
    },
    warning: {
      main: '#ff9800',  // Warning states
    },
    success: {
      main: '#4caf50',  // Success states
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  // Add custom theme overrides as needed
});
```

### Best Practices

1. **Component Structure**
   - Keep components focused and single-responsibility
   - Use TypeScript for props definitions
   - Implement proper error boundaries
   - Handle loading and error states

2. **State Management**
   - Use React Query for API state
   - Implement proper caching strategies
   - Handle optimistic updates
   - Manage WebSocket connections efficiently

3. **Performance**
   - Implement proper memoization
   - Use lazy loading for routes
   - Optimize re-renders
   - Monitor bundle size
