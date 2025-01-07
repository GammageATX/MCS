"""Process Service FastAPI Application

This module defines the FastAPI application for the Process service.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from mcs.api.process.process_service import ProcessService
from mcs.api.process.endpoints import (
    process_router,
    pattern_router,
    parameter_router,
    sequence_router
)
from mcs.utils.errors import create_error


logger = logging.getLogger(__name__)


def load_config(config_path: str = "backend/config/process.yaml") -> Dict:
    """Load service configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict containing service configuration
        
    Raises:
        HTTPException if config file not found or invalid
    """
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "version": "1.0.0",
                "service": {
                    "name": "process",
                    "host": "0.0.0.0",
                    "port": 8004,
                    "log_level": "INFO"
                }
            }
            
        with open(config_path) as f:
            return yaml.safe_load(f)
            
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        raise create_error(
            status_code=500,
            message=f"Failed to load configuration: {str(e)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown events."""
    # Load config
    config = load_config()
    
    # Initialize service
    service = ProcessService(version=config["version"])
    app.state.service = service
    
    try:
        await service.initialize()
        logger.info("Process service initialized successfully")
        yield
    finally:
        await service.shutdown()
        logger.info("Process service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Process Service",
    description="Service for managing process execution and control",
    version="1.0.0",
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
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return create_error(
        status_code=exc.status_code,
        message=str(exc.detail)
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/version")
async def version():
    """Get service version."""
    return {"version": app.state.service.version}


# Include routers
app.include_router(process_router)
app.include_router(pattern_router)
app.include_router(parameter_router)
app.include_router(sequence_router)
