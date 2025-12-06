"""
AI Animal Tracking System - API Routes
======================================

Router modülü.
"""

from src.api.routes.cameras import router as cameras_router
from src.api.routes.animals import router as animals_router
from src.api.routes.analytics import router as analytics_router
from src.api.routes.detection import router as detection_router
from src.api.routes.behavior_routes import router as behaviors_router
from src.api.routes.health_routes import router as health_router
from src.api.routes.export_routes import router as export_router

__all__ = [
    "cameras_router",
    "animals_router",
    "analytics_router",
    "detection_router",
    "behaviors_router",
    "health_router",
    "export_router",
]
