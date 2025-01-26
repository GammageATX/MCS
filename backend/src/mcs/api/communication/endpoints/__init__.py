"""Communication API endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["communication"])

__all__ = ["router"]
