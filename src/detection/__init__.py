"""
AI Animal Tracking System - Detection Module
=============================================

Hayvan tespiti ve nesne algılama modülü.
"""

from src.detection.yolo_detector import (
    YOLODetector,
    Detection,
    DetectionResult,
    DetectorConfig,
)

__all__ = [
    "YOLODetector",
    "Detection",
    "DetectionResult",
    "DetectorConfig",
]
