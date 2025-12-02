"""
AI Animal Tracking System - Camera Routes
==========================================

Kamera yönetimi API endpoint'leri.
CameraService ile gerçek kamera bağlantısı sağlar.
"""

import base64
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import cv2
import numpy as np

from src.api.services import CameraService


router = APIRouter(prefix="/cameras", tags=["Cameras"])


# ===========================================
# Pydantic Models
# ===========================================

class CameraCreate(BaseModel):
    """Kamera oluşturma modeli"""
    id: str = Field(..., description="Benzersiz kamera ID")
    name: str = Field(..., description="Kamera ismi")
    source: str = Field(..., description="Kaynak (index, URL, dosya)")
    type: str = Field(default="usb", description="Kamera tipi (usb, rtsp, http, file)")
    width: int = Field(default=1280, description="Genişlik")
    height: int = Field(default=720, description="Yükseklik")
    fps: int = Field(default=30, description="FPS")
    enabled: bool = Field(default=True, description="Aktif mi")


class CameraResponse(BaseModel):
    """Kamera yanıt modeli"""
    id: str
    name: str
    source: str
    type: str
    state: str
    resolution: Optional[tuple] = None
    fps: float
    is_streaming: bool


class CameraListResponse(BaseModel):
    """Kamera listesi yanıtı"""
    cameras: List[CameraResponse]
    total: int


# ===========================================
# Service instance
# ===========================================

def get_camera_service() -> CameraService:
    """Get camera service instance."""
    return CameraService.get_instance()


# ===========================================
# Endpoints
# ===========================================

@router.get("/", response_model=CameraListResponse)
async def list_cameras():
    """
    Tüm kameraları listele.
    
    Returns:
        Kamera listesi
    """
    service = get_camera_service()
    cameras_data = service.get_cameras()
    
    cameras = [
        CameraResponse(
            id=cam.get("id", ""),
            name=cam.get("name", ""),
            source=str(cam.get("source", "")),
            type="usb",  # TODO: Add type tracking
            state=cam.get("status", "stopped"),
            resolution=cam.get("resolution"),
            fps=cam.get("fps", 0),
            is_streaming=cam.get("is_streaming", False),
        )
        for cam in cameras_data
    ]
    
    return CameraListResponse(cameras=cameras, total=len(cameras))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_camera(camera: CameraCreate):
    """
    Yeni kamera ekle.
    
    Args:
        camera: Kamera bilgileri
        
    Returns:
        Oluşturulan kamera
    """
    service = get_camera_service()
    
    # Source'u uygun formata çevir
    source = camera.source
    if source.isdigit():
        source = int(source)
    
    try:
        result = service.add_camera(
            camera_id=camera.id,
            source=source,
            name=camera.name,
            fps=camera.fps,
            resolution=(camera.width, camera.height)
        )
        return {"message": f"Camera {camera.id} created", "camera": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/{camera_id}")
async def get_camera(camera_id: str):
    """
    Kamera detayları.
    
    Args:
        camera_id: Kamera ID
        
    Returns:
        Kamera bilgileri
    """
    service = get_camera_service()
    camera = service.get_camera(camera_id)
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    return camera


@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    """
    Kamerayı sil.
    
    Args:
        camera_id: Kamera ID
    """
    service = get_camera_service()
    
    if not service.remove_camera(camera_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    return {"message": f"Camera {camera_id} deleted"}


@router.post("/{camera_id}/start")
async def start_camera(camera_id: str):
    """
    Kamerayı başlat.
    
    Args:
        camera_id: Kamera ID
    """
    service = get_camera_service()
    
    if not service.get_camera(camera_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    if not service.start_camera(camera_id):
        status_info = service.get_status(camera_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start camera: {status_info.get('error', 'Unknown error')}"
        )
    
    return {"message": f"Camera {camera_id} started"}


@router.post("/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """
    Kamerayı durdur.
    
    Args:
        camera_id: Kamera ID
    """
    service = get_camera_service()
    
    if not service.get_camera(camera_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    service.stop_camera(camera_id)
    return {"message": f"Camera {camera_id} stopped"}


@router.get("/{camera_id}/status")
async def get_camera_status(camera_id: str):
    """
    Kamera durumu.
    
    Args:
        camera_id: Kamera ID
        
    Returns:
        Kamera durumu
    """
    service = get_camera_service()
    status_info = service.get_status(camera_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    return status_info


@router.get("/{camera_id}/snapshot")
async def get_snapshot(camera_id: str):
    """
    Kameradan snapshot al.
    
    Args:
        camera_id: Kamera ID
        
    Returns:
        Base64 encoded JPEG image
    """
    service = get_camera_service()
    
    camera = service.get_camera(camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )
    
    if not camera.get("is_streaming", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Camera {camera_id} is not streaming"
        )
    
    frame = service.read_frame(camera_id)
    
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read frame from camera"
        )
    
    # Encode to JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "camera_id": camera_id,
        "snapshot": image_base64,
        "format": "jpeg",
        "encoding": "base64"
    }
