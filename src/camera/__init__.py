"""
AI Animal Tracking System - Camera Module
==========================================

Kamera yönetimi ve video yakalama modülü.
"""

from src.camera.video_capture import (
    VideoCapture,
    CameraConfig,
    FrameInfo,
    CameraType,
    CameraState,
)
from src.camera.camera_manager import CameraManager, CameraInfo
from src.camera.frame_buffer import FrameBuffer, BufferedFrame

__all__ = [
    "VideoCapture",
    "CameraConfig",
    "FrameInfo",
    "CameraType",
    "CameraState",
    "CameraManager",
    "CameraInfo",
    "FrameBuffer",
    "BufferedFrame",
]
