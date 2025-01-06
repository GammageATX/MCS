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
