"""
Teknova AI Animal Tracking - Hugging Face Spaces Backend
=========================================================

FastAPI backend for animal detection and re-identification.
Deployed on Hugging Face Spaces with GPU support.
"""

import os
import io
import time
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

import numpy as np
import cv2
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("teknova")

# ===========================================
# Configuration
# ===========================================

class Config:
    """App configuration"""
    MODEL_PATH = "yolov8n.pt"
    CONFIDENCE_THRESHOLD = 0.4
    SIMILARITY_THRESHOLD = 0.92
    MAX_GALLERY_SIZE = 500
    
    # COCO Animal Class IDs
    ANIMAL_CLASS_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23}
    ANIMAL_NAMES = {
        14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse',
        18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
        22: 'zebra', 23: 'giraffe'
    }
    
    # Turkish prefixes
    TURKISH_PREFIXES = {
        'cow': 'INEK', 'sheep': 'KOYUN', 'goat': 'KECI',
        'horse': 'AT', 'dog': 'KOPEK', 'cat': 'KEDI',
        'bird': 'KUS', 'elephant': 'FIL', 'bear': 'AYI',
        'zebra': 'ZEBRA', 'giraffe': 'ZURAFA'
    }

# ===========================================
# Models
# ===========================================

class DetectedAnimal(BaseModel):
    track_id: int
    animal_id: str
    class_name: str
    bbox: List[int]
    confidence: float
    re_id_confidence: float
    is_identified: bool
    is_new: bool
    velocity: List[float] = [0.0, 0.0]
    direction: float = 0.0
    health_score: Optional[float] = None
    behavior: Optional[str] = None

class ProcessResult(BaseModel):
    frame_id: int
    timestamp: float
    fps: float
    animal_count: int
    total_registered: int
    new_this_frame: int
    animals: List[DetectedAnimal]
    frame_size: List[int]

class GalleryAnimal(BaseModel):
    animal_id: str
    class_name: str
    first_seen: float
    last_seen: float
    total_detections: int
    best_confidence: float

class GalleryResponse(BaseModel):
    total: int
    animals: List[GalleryAnimal]
    by_class: Dict[str, int]

# ===========================================
# Feature Extractor
# ===========================================

class FeatureExtractor:
    """Extract visual features for animal re-identification"""
    
    def __init__(self, feature_size=(128, 256), color_bins=32):
        self.feature_size = feature_size
        self.color_bins = color_bins
    
    def extract(self, image: np.ndarray, bbox: tuple) -> Optional[np.ndarray]:
        """Extract features from bounding box region"""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        
        try:
            crop = cv2.resize(crop, self.feature_size)
        except:
            return None
        
        features = []
        
        # HSV histogram
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        for i, bins in enumerate([self.color_bins, self.color_bins, self.color_bins//2]):
            hist = cv2.calcHist([hsv], [i], None, [bins], [0, 256 if i > 0 else 180])
            cv2.normalize(hist, hist)
            features.append(hist.flatten())
        
        # Regional histograms (top, middle, bottom)
        h_crop = crop.shape[0]
        for region in [crop[:h_crop//3], crop[h_crop//3:2*h_crop//3], crop[2*h_crop//3:]]:
            hsv_region = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv_region], [0], None, [self.color_bins], [0, 180])
            cv2.normalize(hist, hist)
            features.append(hist.flatten())
        
        # Edge features
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_hist = cv2.calcHist([edges], [0], None, [16], [0, 256])
        cv2.normalize(edge_hist, edge_hist)
        features.append(edge_hist.flatten())
        
        # Combine and normalize
        combined = np.concatenate(features)
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        
        return combined.astype(np.float32)

# ===========================================
# Animal Gallery
# ===========================================

class AnimalGallery:
    """In-memory gallery for animal records"""
    
    def __init__(self):
        self.records: Dict[str, Dict] = {}
        self.features: Dict[str, np.ndarray] = {}
        self.id_counters: Dict[str, int] = {}
        self.class_index: Dict[str, List[str]] = {}
    
    def generate_id(self, class_name: str) -> str:
        prefix = Config.TURKISH_PREFIXES.get(class_name.lower(), class_name.upper()[:4])
        self.id_counters[prefix] = self.id_counters.get(prefix, 0) + 1
        return f"{prefix}_{self.id_counters[prefix]:04d}"
    
    def register(self, features: np.ndarray, class_name: str, confidence: float) -> str:
        animal_id = self.generate_id(class_name)
        
        self.records[animal_id] = {
            "animal_id": animal_id,
            "class_name": class_name,
            "first_seen": time.time(),
            "last_seen": time.time(),
            "total_detections": 1,
            "best_confidence": confidence
        }
        self.features[animal_id] = features.copy()
        
        if class_name not in self.class_index:
            self.class_index[class_name] = []
        self.class_index[class_name].append(animal_id)
        
        logger.info(f"🆕 New animal registered: {animal_id}")
        return animal_id
    
    def search(self, query_features: np.ndarray, class_name: str, top_k: int = 5) -> List[tuple]:
        """Find most similar animals of the same class"""
        if class_name not in self.class_index:
            return []
        
        candidates = self.class_index[class_name]
        if not candidates:
            return []
        
        results = []
        query_norm = query_features / (np.linalg.norm(query_features) + 1e-8)
        
        for animal_id in candidates:
            if animal_id not in self.features:
                continue
            feat = self.features[animal_id]
            feat_norm = feat / (np.linalg.norm(feat) + 1e-8)
            similarity = float(np.dot(query_norm, feat_norm))
            results.append((animal_id, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def update(self, animal_id: str, features: np.ndarray, confidence: float):
        """Update existing animal record"""
        if animal_id not in self.records:
            return
        
        # Exponential moving average for features
        alpha = 0.02
        self.features[animal_id] = (1 - alpha) * self.features[animal_id] + alpha * features
        
        self.records[animal_id]["last_seen"] = time.time()
        self.records[animal_id]["total_detections"] += 1
        if confidence > self.records[animal_id]["best_confidence"]:
            self.records[animal_id]["best_confidence"] = confidence
    
    def get_all(self) -> GalleryResponse:
        """Get all animals in gallery"""
        animals = [GalleryAnimal(**r) for r in self.records.values()]
        by_class = {cls: len(ids) for cls, ids in self.class_index.items()}
        return GalleryResponse(
            total=len(self.records),
            animals=animals,
            by_class=by_class
        )
    
    def reset(self):
        """Clear all records"""
        self.records.clear()
        self.features.clear()
        self.id_counters.clear()
        self.class_index.clear()
        logger.info("🗑️ Gallery reset")
    
    @property
    def size(self) -> int:
        return len(self.records)

# ===========================================
# Animal Detector
# ===========================================

class AnimalDetector:
    """YOLOv8-based animal detector with re-identification"""
    
    def __init__(self):
        self.model = None
        self.extractor = FeatureExtractor()
        self.gallery = AnimalGallery()
        self.frame_count = 0
        self.track_id_counter = 0
    
    def initialize(self):
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(Config.MODEL_PATH)
            logger.info("✅ YOLOv8 model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def process_frame(self, image: np.ndarray) -> ProcessResult:
        """Process a single frame"""
        start_time = time.time()
        self.frame_count += 1
        
        if self.model is None:
            self.initialize()
        
        h, w = image.shape[:2]
        detected_animals = []
        new_this_frame = 0
        used_ids = set()
        
        # Run YOLO detection
        results = self.model(image, verbose=False, conf=Config.CONFIDENCE_THRESHOLD)
        
        # Process each detection
        detections = []
        for result in results:
            if result.boxes is None:
                continue
            
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                
                # Only process animals
                if cls_id not in Config.ANIMAL_CLASS_IDS:
                    continue
                
                class_name = Config.ANIMAL_NAMES.get(cls_id, 'unknown')
                bbox = [int(v) for v in box.xyxy[0].cpu().numpy()]
                confidence = float(box.conf[0].item())
                
                # Extract features
                features = self.extractor.extract(image, bbox)
                if features is None:
                    continue
                
                detections.append({
                    "bbox": bbox,
                    "confidence": confidence,
                    "class_name": class_name,
                    "features": features
                })
        
        # Match detections to gallery (sorted by confidence)
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        
        for det in detections:
            self.track_id_counter += 1
            track_id = self.track_id_counter
            
            # Search gallery
            matches = self.gallery.search(det["features"], det["class_name"])
            
            # Find best unused match
            best_match = None
            for animal_id, similarity in matches:
                if animal_id not in used_ids and similarity >= Config.SIMILARITY_THRESHOLD:
                    best_match = (animal_id, similarity)
                    break
            
            if best_match:
                # Matched existing animal
                animal_id, similarity = best_match
                used_ids.add(animal_id)
                self.gallery.update(animal_id, det["features"], det["confidence"])
                is_new = False
            else:
                # Register new animal
                animal_id = self.gallery.register(
                    det["features"],
                    det["class_name"],
                    det["confidence"]
                )
                used_ids.add(animal_id)
                similarity = 1.0
                is_new = True
                new_this_frame += 1
            
            detected_animals.append(DetectedAnimal(
                track_id=track_id,
                animal_id=animal_id,
                class_name=det["class_name"],
                bbox=det["bbox"],
                confidence=det["confidence"],
                re_id_confidence=similarity,
                is_identified=True,
                is_new=is_new
            ))
        
        # Calculate FPS
        elapsed = time.time() - start_time
        fps = 1.0 / elapsed if elapsed > 0 else 0.0
        
        return ProcessResult(
            frame_id=self.frame_count,
            timestamp=time.time(),
            fps=fps,
            animal_count=len(detected_animals),
            total_registered=self.gallery.size,
            new_this_frame=new_this_frame,
            animals=detected_animals,
            frame_size=[w, h]
        )

# ===========================================
# FastAPI App
# ===========================================

# Global detector instance
detector: Optional[AnimalDetector] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize detector on startup"""
    global detector
    logger.info("🚀 Starting Teknova AI Animal Tracking...")
    detector = AnimalDetector()
    detector.initialize()
    yield
    logger.info("👋 Shutting down...")

app = FastAPI(
    title="Teknova AI Animal Tracking",
    description="AI-powered animal detection and re-identification API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# API Endpoints
# ===========================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Teknova AI Animal Tracking",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "process": "/api/v1/detection/process-frame",
            "gallery": "/api/v1/detection/gallery",
            "reset": "/api/v1/detection/reset"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": detector is not None and detector.model is not None,
        "gallery_size": detector.gallery.size if detector else 0
    }

@app.post("/api/v1/detection/process-frame")
async def process_frame(file: UploadFile = File(...)):
    """Process uploaded image for animal detection"""
    global detector
    
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Process
        result = detector.process_frame(image)
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/detection/gallery")
async def get_gallery():
    """Get all registered animals"""
    global detector
    
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    return detector.gallery.get_all().model_dump()

@app.post("/api/v1/detection/reset")
async def reset_gallery():
    """Reset animal gallery"""
    global detector
    
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    detector.gallery.reset()
    return {"status": "success", "message": "Gallery reset"}

# ===========================================
# Main
# ===========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
