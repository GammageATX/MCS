"""MicroColdSpray backend package."""

__version__ = "1.0.0"

from mcs.ui.router import create_ui_app
from mcs.api.config.config_app import create_config_service
from mcs.api.state.state_app import create_state_service
from mcs.api.communication.communication_app import create_communication_service
from mcs.api.process.process_app import create_process_service
from mcs.api.data_collection.data_collection_app import create_data_collection_service

__all__ = [
    "create_ui_app",
    "create_config_service",
    "create_state_service",
    "create_communication_service",
    "create_process_service",
    "create_data_collection_service"
]
