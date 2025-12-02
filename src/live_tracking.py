"""
AI Animal Tracking System - Live Detection with Re-ID
======================================================

Canlı kamera akışında hayvan tespiti, takibi ve benzersiz kimlik atama.
"""

import cv2
import numpy as np
import time
import json
import asyncio
import logging
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from src.detection.yolo_detector import YOLODetector, DetectionResult
from src.tracking.object_tracker import ObjectTracker, Track, TrackerConfig
from src.identification.animal_identifier import (
    AnimalIdentifier, 
    IdentifierConfig,
    AnimalGallery,
    IdentificationResult
)

logger = logging.getLogger("animal_tracking.live_detection")


@dataclass
class TrackedAnimal:
    """Takip edilen hayvan bilgisi"""
    track_id: int               # Tracker ID (geçici)
    animal_id: str              # Kalıcı benzersiz ID (BOV_0001)
    class_name: str             # Sınıf (inek, koyun vb.)
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    
    # Re-ID bilgisi
    re_id_confidence: float = 0.0
    is_identified: bool = False
    
    # Hareket
    velocity: Tuple[float, float] = (0, 0)
    direction: float = 0.0
    
    # Sağlık tahmini (opsiyonel)
    health_score: Optional[float] = None
    behavior: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "animal_id": self.animal_id,
            "class_name": self.class_name,
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 3),
            "re_id_confidence": round(self.re_id_confidence, 3),
            "is_identified": self.is_identified,
            "velocity": self.velocity,
            "direction": round(self.direction, 1),
            "health_score": self.health_score,
            "behavior": self.behavior
        }


class LiveAnimalTracker:
    """
    Canlı hayvan takip sistemi.
    
    Özellikleri:
    - YOLOv8 ile gerçek zamanlı tespit
    - ByteTrack ile nesne takibi
    - Re-ID ile benzersiz kimlik atama
    - Her kare için JSON çıktı (frontend için)
    
    Kullanım:
        tracker = LiveAnimalTracker()
        
        # Kamera ile
        for frame, results in tracker.process_camera(0):
            print(f"Tespit: {len(results['animals'])} hayvan")
            for animal in results['animals']:
                print(f"  {animal['animal_id']}: {animal['class_name']}")
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        enable_reid: bool = True,
        gallery_path: str = "data/gallery"
    ):
        # YOLO Detector
        self.detector = YOLODetector(model_path=model_path)
        
        # Object Tracker
        tracker_config = TrackerConfig(
            track_high_thresh=confidence_threshold,
            track_buffer=30,
            match_thresh=0.8
        )
        self.tracker = ObjectTracker(config=tracker_config)
        
        # Animal Identifier (Re-ID)
        self.enable_reid = enable_reid
        if enable_reid:
            identifier_config = IdentifierConfig(
                similarity_threshold=0.7,
                save_gallery=True,
                gallery_path=gallery_path
            )
            self.identifier = AnimalIdentifier(config=identifier_config)
        else:
            self.identifier = None
        
        # Track ID -> Animal ID mapping
        self._track_to_animal: Dict[int, str] = {}
        
        # İstatistikler
        self.frame_count = 0
        self.fps = 0.0
        self._last_time = time.time()
        self._fps_history: List[float] = []
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Tek bir frame'i işle.
        
        Args:
            frame: BGR görüntü (OpenCV formatı)
            
        Returns:
            {
                "frame_id": int,
                "timestamp": float,
                "fps": float,
                "animal_count": int,
                "animals": [TrackedAnimal dict listesi],
                "frame_size": [width, height]
            }
        """
        start_time = time.time()
        self.frame_count += 1
        
        # 1. YOLO Detection + Tracking
        detection_result = self.detector.track(frame)
        
        # 2. Object Tracker güncelle
        tracking_result = self.tracker.update(detection_result)
        
        # 3. Her track için Re-ID yap
        tracked_animals: List[TrackedAnimal] = []
        
        for track in tracking_result.confirmed_tracks:
            # Track ID -> Animal ID eşlemesi
            if track.track_id in self._track_to_animal:
                animal_id = self._track_to_animal[track.track_id]
                re_id_conf = 1.0
                is_identified = True
            elif self.enable_reid and self.identifier:
                # Yeni track, Re-ID dene
                id_result = self.identifier.identify(
                    frame, 
                    track.bbox, 
                    track.class_name
                )
                animal_id = id_result.animal_id
                re_id_conf = id_result.similarity_score
                is_identified = not id_result.is_new
                
                # Mapping güncelle
                self._track_to_animal[track.track_id] = animal_id
            else:
                # Re-ID kapalı, track_id kullan
                animal_id = f"{track.class_name[:3].upper()}_{track.track_id:04d}"
                re_id_conf = 0.0
                is_identified = False
                self._track_to_animal[track.track_id] = animal_id
            
            # TrackedAnimal oluştur
            tracked = TrackedAnimal(
                track_id=track.track_id,
                animal_id=animal_id,
                class_name=track.class_name,
                bbox=track.bbox,
                confidence=track.confidence,
                re_id_confidence=re_id_conf,
                is_identified=is_identified,
                velocity=track.velocity or (0, 0),
                direction=track.direction or 0.0
            )
            tracked_animals.append(tracked)
        
        # FPS hesapla
        process_time = time.time() - start_time
        self._fps_history.append(1.0 / process_time if process_time > 0 else 0)
        if len(self._fps_history) > 30:
            self._fps_history.pop(0)
        self.fps = sum(self._fps_history) / len(self._fps_history)
        
        h, w = frame.shape[:2]
        
        return {
            "frame_id": self.frame_count,
            "timestamp": time.time(),
            "fps": round(self.fps, 1),
            "animal_count": len(tracked_animals),
            "animals": [a.to_dict() for a in tracked_animals],
            "frame_size": [w, h]
        }
    
    def draw_detections(
        self, 
        frame: np.ndarray, 
        result: Dict[str, Any],
        show_id: bool = True,
        show_trajectory: bool = True,
        show_bbox: bool = True
    ) -> np.ndarray:
        """
        Frame üzerine tespit sonuçlarını çiz.
        
        Args:
            frame: BGR görüntü
            result: process_frame() çıktısı
            show_id: ID etiketini göster
            show_trajectory: Hareket izini göster
            show_bbox: Bounding box göster
            
        Returns:
            Çizimli frame
        """
        output = frame.copy()
        
        # Renk paleti (sınıfa göre)
        colors = {
            'cow': (0, 255, 0),      # Yeşil
            'cattle': (0, 255, 0),
            'inek': (0, 255, 0),
            'sheep': (255, 165, 0),  # Turuncu
            'koyun': (255, 165, 0),
            'goat': (255, 0, 255),   # Mor
            'keçi': (255, 0, 255),
            'horse': (0, 165, 255),  # Turuncu-kırmızı
            'at': (0, 165, 255),
            'default': (0, 255, 255) # Sarı
        }
        
        for animal in result['animals']:
            x1, y1, x2, y2 = animal['bbox']
            class_name = animal['class_name'].lower()
            animal_id = animal['animal_id']
            confidence = animal['confidence']
            
            # Renk seç
            color = colors.get(class_name, colors['default'])
            
            # Bounding Box
            if show_bbox:
                cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # ID ve sınıf etiketi
            if show_id:
                label = f"{animal_id}"
                conf_text = f"{confidence*100:.0f}%"
                
                # Etiket arka planı
                (label_w, label_h), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                
                # Üst etiket (ID)
                cv2.rectangle(
                    output, 
                    (x1, y1 - label_h - 10), 
                    (x1 + label_w + 10, y1),
                    color, -1
                )
                cv2.putText(
                    output, label,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2
                )
                
                # Alt etiket (güven)
                cv2.putText(
                    output, conf_text,
                    (x1 + 5, y2 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                )
        
        # FPS göster
        cv2.putText(
            output, f"FPS: {result['fps']:.1f}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
        
        # Hayvan sayısı
        cv2.putText(
            output, f"Hayvan: {result['animal_count']}",
            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
        
        return output
    
    def process_camera(
        self, 
        source: int | str = 0,
        output_path: Optional[str] = None,
        show_window: bool = True,
        max_frames: Optional[int] = None
    ):
        """
        Kamera veya video dosyasını işle.
        
        Args:
            source: Kamera indeksi veya video dosya yolu
            output_path: Çıktı video dosya yolu (opsiyonel)
            show_window: OpenCV penceresi göster
            max_frames: Maksimum frame sayısı
            
        Yields:
            (frame, result) çiftleri
        """
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            raise RuntimeError(f"Kaynak açılamadı: {source}")
        
        # Video writer
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        
        frame_num = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_num += 1
                if max_frames and frame_num > max_frames:
                    break
                
                # Frame işle
                result = self.process_frame(frame)
                
                # Çizimleri ekle
                output_frame = self.draw_detections(frame, result)
                
                # Kaydet
                if writer:
                    writer.write(output_frame)
                
                # Göster
                if show_window:
                    cv2.imshow("AI Animal Tracking", output_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                yield frame, result
                
        finally:
            cap.release()
            if writer:
                writer.release()
            if show_window:
                cv2.destroyAllWindows()
    
    def get_gallery_info(self) -> Dict[str, Any]:
        """Tanınan hayvanlar hakkında bilgi döndür"""
        if not self.identifier:
            return {"enabled": False, "count": 0, "animals": []}
        
        gallery = self.identifier.gallery
        return {
            "enabled": True,
            "count": gallery.size,
            "animals": [
                {
                    "animal_id": aid,
                    "class_name": gallery.get(aid).class_name if gallery.get(aid) else "unknown"
                }
                for aid in gallery.animal_ids
            ]
        }
    
    def export_gallery(self, path: str):
        """Galeriyi dosyaya kaydet"""
        if self.identifier:
            self.identifier.save_gallery(path)
    
    def import_gallery(self, path: str):
        """Galeriyi dosyadan yükle"""
        if self.identifier:
            self.identifier.load_gallery(path)


# WebSocket için JSON encoder
def animal_to_json(result: Dict[str, Any]) -> str:
    """Result dict'i JSON string'e çevir"""
    return json.dumps(result, ensure_ascii=False)


# Test fonksiyonu
if __name__ == "__main__":
    import sys
    
    # Kamera veya video
    source = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    tracker = LiveAnimalTracker(enable_reid=True)
    
    print("AI Animal Tracking başlatılıyor...")
    print("Çıkmak için 'q' tuşuna basın")
    
    for frame, result in tracker.process_camera(source, show_window=True):
        if result['animal_count'] > 0:
            print(f"\rFrame {result['frame_id']}: {result['animal_count']} hayvan | FPS: {result['fps']:.1f}", end="")
    
    print("\n\nGaleri bilgisi:")
    print(json.dumps(tracker.get_gallery_info(), indent=2, ensure_ascii=False))
