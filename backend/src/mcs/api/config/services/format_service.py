"""Format service implementation."""

from datetime import datetime
from typing import Dict, Any, List
import yaml
import json
from fastapi import status
from loguru import logger

from mcs.utils.errors import create_error
from mcs.utils.health import ServiceHealth, ComponentHealth, HealthStatus, create_error_health


class FormatService:
    """Format service."""

    def __init__(self, enabled_formats: List[str], version: str = "1.0.0"):
        """Initialize service."""
        self._service_name = "format"
        self._version = version
        self._is_running = False
        self._start_time = None
        
        # Initialize components to None
        self._enabled_formats = None
        self._formatters = None
        self._failed_formatters = {}  # Track failed formatters
        
        # Store constructor args for initialization
        self._init_enabled_formats = enabled_formats
        
        logger.info(f"{self.service_name} service initialized")

    async def save_yaml(self, data: Dict[str, Any], preserve_format: bool = False) -> str:
        """Save data as YAML with numeric and string format preservation."""
        try:
            from ruamel.yaml import YAML, scalarstring
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.indent(mapping=2, sequence=2, offset=0)  # Use 2 spaces everywhere
            yaml.preserve_quotes = True
            yaml.allow_unicode = True
            yaml.width = 4096  # Prevent line wrapping

            def preserve_format(d):
                if isinstance(d, dict):
                    return {k: preserve_format(v) for k, v in d.items()}
                elif isinstance(d, list):
                    return [preserve_format(v) for v in d]
                elif isinstance(d, bool):
                    return d
                elif isinstance(d, (int, float)):
                    # Preserve decimal points for floats and whole numbers
                    s = f"{d:.1f}" if isinstance(d, float) or str(d).endswith(".0") else str(d)
                    return scalarstring.DoubleQuotedScalarString(s) if "." in s else d
                elif isinstance(d, str):
                    # Preserve quotes on strings
                    return scalarstring.DoubleQuotedScalarString(d)
                return d

            # Process data to preserve formats
            processed_data = preserve_format(data)
            
            # Convert to string
            import io
            string_stream = io.StringIO()
            yaml.dump(processed_data, string_stream)
            return string_stream.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to save YAML: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to save YAML: {str(e)}"
            )

    async def load_yaml(self, content: str) -> Dict[str, Any]:
        """Load YAML content."""
        try:
            return yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to load YAML: {str(e)}"
            )

    async def save_json(self, data: Dict[str, Any], preserve_format: bool = False) -> str:
        """Save data as JSON with optional format preservation."""
        try:
            if preserve_format:
                return json.dumps(data, indent=2, sort_keys=False)
            else:
                return json.dumps(data)
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to save JSON: {str(e)}"
            )

    async def load_json(self, content: str) -> Dict[str, Any]:
        """Load JSON content."""
        try:
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            raise create_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to load JSON: {str(e)}"
            )

    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._service_name

    @property
    def version(self) -> str:
        """Get service version."""
        return self._version

    @property
    def is_running(self) -> bool:
        """Get service running state."""
        return self._is_running

    @property
    def uptime(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self._start_time).total_seconds() if self._start_time else 0.0

    async def initialize(self) -> None:
        """Initialize service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )
            
            # Initialize enabled formats
            self._enabled_formats = self._init_enabled_formats
            
            # Initialize formatters
            self._formatters = {}
            await self._load_formatters()
            
            logger.info(f"Enabled formats: {', '.join(self._enabled_formats)}")
            logger.info(f"{self.service_name} service initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def _load_formatters(self) -> None:
        """Load formatters for enabled formats."""
        for fmt in self._enabled_formats:
            try:
                self._formatters[fmt] = {}  # Initialize formatter
                # If formatter was previously failed, remove from failed list
                self._failed_formatters.pop(fmt, None)
            except Exception as e:
                logger.error(f"Failed to load formatter {fmt}: {e}")
                self._failed_formatters[fmt] = str(e)

    async def _attempt_recovery(self) -> None:
        """Attempt to recover failed formatters."""
        if self._failed_formatters:
            logger.info(f"Attempting to recover {len(self._failed_formatters)} failed formatters...")
            await self._load_formatters()

    async def start(self) -> None:
        """Start service."""
        try:
            if self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service already running"
                )

            if not self._enabled_formats or not self._formatters:
                raise create_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"{self.service_name} service not initialized"
                )
            
            self._is_running = True
            self._start_time = datetime.now()
            logger.info(f"{self.service_name} service started")
            
        except Exception as e:
            self._is_running = False
            self._start_time = None
            error_msg = f"Failed to start {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def stop(self) -> None:
        """Stop service."""
        try:
            if not self.is_running:
                raise create_error(
                    status_code=status.HTTP_409_CONFLICT,
                    message=f"{self.service_name} service not running"
                )

            self._is_running = False
            self._start_time = None
            logger.info(f"{self.service_name} service stopped")
            
        except Exception as e:
            error_msg = f"Failed to stop {self.service_name} service: {str(e)}"
            logger.error(error_msg)
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message=error_msg
            )

    async def health(self) -> ServiceHealth:
        """Get service health status."""
        try:
            # Check critical components
            components = {}
            
            # Check formatters (critical for parsing)
            formatters_ok = True
            loaded_formatters = []
            failed_formatters = []
            
            for fmt in self._enabled_formats or []:
                is_loaded = fmt in self._formatters
                if is_loaded:
                    loaded_formatters.append(fmt)
                else:
                    failed_formatters.append(fmt)
                    formatters_ok = False
            
            components["formatters"] = ComponentHealth(
                status=HealthStatus.OK if formatters_ok else HealthStatus.ERROR,
                error=None if formatters_ok else f"Failed to load formatters: {', '.join(failed_formatters)}",
                details={
                    "enabled": self._enabled_formats,
                    "loaded": loaded_formatters,
                    "failed": failed_formatters,
                    "recovery_attempts": len(self._failed_formatters)
                }
            )
            
            # Overall status is ERROR if no formatters loaded
            overall_status = HealthStatus.ERROR if not formatters_ok else HealthStatus.OK

            return ServiceHealth(
                status=overall_status,
                service=self.service_name,
                version=self.version,
                is_running=self.is_running,
                uptime=self.uptime,
                error="Critical component failure" if overall_status == HealthStatus.ERROR else None,
                components=components
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return create_error_health(self.service_name, self.version, error_msg)
