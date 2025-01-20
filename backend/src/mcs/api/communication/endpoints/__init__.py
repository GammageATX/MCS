"""Communication API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/state", tags=["state"])

__all__ = ["router"]
