# src/api/routes/streaming.py
"""
WebSocket streaming routes for real-time video and detection.
"""

import asyncio
import base64
import json
import logging
import time
from typing import Dict, Set, Optional, Any
from datetime import datetime

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


# ===========================================
# Connection Manager
# ===========================================

class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, camera_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if camera_id not in self.active_connections:
                self.active_connections[camera_id] = set()
            self.active_connections[camera_id].add(websocket)
        logger.info(f"WebSocket connected for camera: {camera_id}")
    
    async def disconnect(self, websocket: WebSocket, camera_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if camera_id in self.active_connections:
                self.active_connections[camera_id].discard(websocket)
                if not self.active_connections[camera_id]:
                    del self.active_connections[camera_id]
        logger.info(f"WebSocket disconnected for camera: {camera_id}")
    
    async def broadcast(self, camera_id: str, message: dict):
        """Broadcast message to all connections for a camera."""
        if camera_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[camera_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            await self.disconnect(conn, camera_id)
    
    async def send_frame(self, camera_id: str, frame: np.ndarray, detections: list = None):
        """Send frame with optional detections."""
        if camera_id not in self.active_connections:
            return
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        message = {
            "type": "frame",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "frame": frame_b64,
            "detections": detections or []
        }
        
        await self.broadcast(camera_id, message)
    
    def get_connection_count(self, camera_id: str = None) -> int:
        """Get number of active connections."""
        if camera_id:
            return len(self.active_connections.get(camera_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


# ===========================================
# Stream State Manager
# ===========================================

class StreamState:
    """Manages stream state for each camera."""
    
    def __init__(self):
        self.active_streams: Dict[str, dict] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}
    
    def start_stream(self, camera_id: str, source: Any):
        """Mark stream as started."""
        self.active_streams[camera_id] = {
            "source": source,
            "started_at": datetime.now().isoformat(),
            "frame_count": 0,
            "fps": 0.0
        }
    
    def stop_stream(self, camera_id: str):
        """Stop and remove stream."""
        if camera_id in self.active_streams:
            del self.active_streams[camera_id]
        if camera_id in self.stream_tasks:
            self.stream_tasks[camera_id].cancel()
            del self.stream_tasks[camera_id]
    
    def is_streaming(self, camera_id: str) -> bool:
        """Check if camera is streaming."""
        return camera_id in self.active_streams
    
    def get_stats(self, camera_id: str) -> Optional[dict]:
        """Get stream statistics."""
        return self.active_streams.get(camera_id)


stream_state = StreamState()


# ===========================================
# WebSocket Endpoints
# ===========================================

@router.websocket("/ws/{camera_id}")
async def websocket_stream(
    websocket: WebSocket,
    camera_id: str,
    detection: bool = Query(True, description="Enable detection"),
    tracking: bool = Query(True, description="Enable tracking")
):
    """
    WebSocket endpoint for real-time video streaming.
    
    Sends JSON messages with:
    - type: "frame" | "detection" | "alert" | "status"
    - camera_id: Camera identifier
    - timestamp: ISO timestamp
    - frame: Base64 encoded JPEG (for frame type)
    - detections: List of detection objects
    """
    await manager.connect(websocket, camera_id)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "camera_id": camera_id,
            "status": "connected",
            "detection_enabled": detection,
            "tracking_enabled": tracking,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message (commands from client)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Heartbeat timeout
                )
                
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif msg_type == "config":
                    # Update stream configuration
                    detection = message.get("detection", detection)
                    tracking = message.get("tracking", tracking)
                    await websocket.send_json({
                        "type": "config_updated",
                        "detection": detection,
                        "tracking": tracking
                    })
                
                elif msg_type == "snapshot":
                    # Request current frame snapshot
                    await websocket.send_json({
                        "type": "snapshot_pending",
                        "camera_id": camera_id
                    })
                
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket, camera_id)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts.
    
    Broadcasts all system alerts to connected clients.
    """
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "alerts",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("Alert WebSocket disconnected")
    except Exception as e:
        logger.error(f"Alert WebSocket error: {e}")


# ===========================================
# MJPEG Streaming (Alternative)
# ===========================================

async def generate_mjpeg_frames(camera_id: str, source: int = 0):
    """Generate MJPEG frames from camera."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    from src.camera import VideoCapture
    from src.detection import YOLODetector
    
    cap = VideoCapture(source)
    detector = YOLODetector()
    
    try:
        cap.start()
        
        while True:
            frame = cap.read()
            if frame is None:
                await asyncio.sleep(0.1)
                continue
            
            # Detect
            result = detector.detect(frame)
            
            # Draw detections
            for det in result.detections:
                x1, y1, x2, y2 = det.bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{det.class_name}: {det.confidence:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Encode
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except Exception as e:
        logger.error(f"MJPEG stream error: {e}")
    finally:
        cap.stop()


@router.get("/mjpeg/{camera_id}")
async def mjpeg_stream(
    camera_id: str,
    source: int = Query(0, description="Camera source index")
):
    """
    MJPEG stream endpoint for browser-compatible video.
    
    Can be used directly in <img> tag:
    <img src="/api/v1/stream/mjpeg/cam1?source=0" />
    """
    return StreamingResponse(
        generate_mjpeg_frames(camera_id, source),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ===========================================
# Stream Control Endpoints
# ===========================================

@router.get("/status")
async def get_stream_status():
    """Get status of all active streams."""
    return {
        "active_streams": list(stream_state.active_streams.keys()),
        "total_connections": manager.get_connection_count(),
        "streams": {
            cam_id: {
                **stats,
                "connections": manager.get_connection_count(cam_id)
            }
            for cam_id, stats in stream_state.active_streams.items()
        }
    }


@router.get("/status/{camera_id}")
async def get_camera_stream_status(camera_id: str):
    """Get status of a specific camera stream."""
    stats = stream_state.get_stats(camera_id)
    if not stats:
        return {
            "camera_id": camera_id,
            "streaming": False,
            "connections": manager.get_connection_count(camera_id)
        }
    
    return {
        "camera_id": camera_id,
        "streaming": True,
        "connections": manager.get_connection_count(camera_id),
        **stats
    }


@router.post("/start/{camera_id}")
async def start_stream(
    camera_id: str,
    source: int = Query(0, description="Camera source index")
):
    """Start streaming from a camera."""
    if stream_state.is_streaming(camera_id):
        return {"message": f"Camera {camera_id} is already streaming"}
    
    stream_state.start_stream(camera_id, source)
    
    return {
        "message": f"Stream started for camera {camera_id}",
        "camera_id": camera_id,
        "source": source,
        "websocket_url": f"/api/v1/stream/ws/{camera_id}",
        "mjpeg_url": f"/api/v1/stream/mjpeg/{camera_id}?source={source}"
    }


@router.post("/stop/{camera_id}")
async def stop_stream(camera_id: str):
    """Stop streaming from a camera."""
    if not stream_state.is_streaming(camera_id):
        return {"message": f"Camera {camera_id} is not streaming"}
    
    stream_state.stop_stream(camera_id)
    
    # Notify connected clients
    await manager.broadcast(camera_id, {
        "type": "stream_stopped",
        "camera_id": camera_id,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": f"Stream stopped for camera {camera_id}"}
