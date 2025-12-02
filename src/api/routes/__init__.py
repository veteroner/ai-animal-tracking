"""
AI Animal Tracking System - API Routes
======================================

Router modülü.
"""

from src.api.routes.cameras import router as cameras_router
from src.api.routes.animals import router as animals_router
from src.api.routes.analytics import router as analytics_router

__all__ = [
    "cameras_router",
    "animals_router",
    "analytics_router",
]
