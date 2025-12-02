"""
AI Animal Tracking System - Main Entry Point
=============================================

Ana uygulama giriş noktası.
Komut satırından çalıştırma için kullanılır.

Kullanım:
    python -m src.main --camera 0
    python -m src.main --camera "rtsp://192.168.1.100:554/stream"
    python -m src.main --camera "http://192.168.1.100:8080/video"
"""

import argparse
import sys
import signal
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# Proje kök dizinini path'e ekle
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.utils import setup_logging, get_logger, FPSCounter, get_device
from src.core.constants import COCO_ANIMAL_CLASSES, VISUALIZATION_COLORS


# Global logger
logger = get_logger("main")


class AnimalTrackingApp:
    """Ana uygulama sınıfı"""
    
    def __init__(
        self,
        camera_source: str = "0",
        model_name: str = "yolov8n.pt",
        confidence: float = 0.5,
        show_display: bool = True,
        save_video: bool = False,
        output_path: Optional[str] = None,
    ):
        """
        Args:
            camera_source: Kamera kaynağı (index, URL, dosya yolu)
            model_name: YOLO model ismi
            confidence: Minimum güven skoru
            show_display: Görüntüyü göster
            save_video: Video kaydet
            output_path: Çıkış video yolu
        """
        self.camera_source = camera_source
        self.model_name = model_name
        self.confidence = confidence
        self.show_display = show_display
        self.save_video = save_video
        self.output_path = output_path
        
        self.running = False
        self.cap = None
        self.model = None
        self.tracker = None
        self.writer = None
        self.fps_counter = FPSCounter()
        
        # Device seçimi
        self.device = get_device("auto")
        logger.info(f"Using device: {self.device}")
    
    def _init_camera(self) -> bool:
        """Kamerayı başlat"""
        logger.info(f"Initializing camera: {self.camera_source}")
        
        # Kamera kaynağını belirle
        source = self.camera_source
        if source.isdigit():
            source = int(source)
        
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera: {self.camera_source}")
            return False
        
        # Kamera bilgilerini al
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        logger.info(f"Camera opened: {width}x{height} @ {fps}fps")
        
        # Video writer başlat
        if self.save_video:
            self._init_video_writer(width, height, fps)
        
        return True
    
    def _init_video_writer(self, width: int, height: int, fps: int):
        """Video writer başlat"""
        if self.output_path is None:
            from src.core.utils import get_timestamp_filename
            output_dir = ROOT_DIR / "data" / "videos"
            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_path = str(output_dir / f"output_{get_timestamp_filename()}.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        logger.info(f"Video writer initialized: {self.output_path}")
    
    def _init_model(self) -> bool:
        """YOLO modelini yükle"""
        logger.info(f"Loading model: {self.model_name}")
        
        try:
            from ultralytics import YOLO
            
            # Model yolu
            model_path = ROOT_DIR / "models" / "pretrained" / self.model_name
            
            if not model_path.exists():
                logger.info(f"Downloading model: {self.model_name}")
                self.model = YOLO(self.model_name)
            else:
                self.model = YOLO(str(model_path))
            
            # Test inference
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def _init_tracker(self) -> bool:
        """Tracker'ı başlat (basit centroid tracker)"""
        logger.info("Initializing tracker...")
        
        # Basit takip için dictionary
        self.tracker = {
            "tracks": {},
            "next_id": 1,
            "max_disappeared": 50,
        }
        
        return True
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Tek bir frame'i işle.
        
        Args:
            frame: Input frame
            
        Returns:
            İşlenmiş frame
        """
        # YOLO ile tespit
        results = self.model(
            frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )
        
        # Sonuçları çiz
        annotated_frame = frame.copy()
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            for i, box in enumerate(boxes):
                # Koordinatlar
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                
                # Sadece hayvanları filtrele
                if cls_id not in COCO_ANIMAL_CLASSES:
                    continue
                
                cls_name = COCO_ANIMAL_CLASSES.get(cls_id, f"class_{cls_id}")
                
                # Renk seç
                color = VISUALIZATION_COLORS[i % len(VISUALIZATION_COLORS)]
                
                # Bounding box çiz
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # Label
                label = f"{cls_name}: {conf:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                # Label background
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )
                
                # Label text
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
        
        # FPS göster
        fps = self.fps_counter.update()
        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        return annotated_frame
    
    def run(self):
        """Ana döngüyü başlat"""
        logger.info("Starting Animal Tracking System...")
        
        # Bileşenleri başlat
        if not self._init_camera():
            return
        
        if not self._init_model():
            self.cleanup()
            return
        
        if not self._init_tracker():
            self.cleanup()
            return
        
        self.running = True
        logger.info("System ready. Press 'q' to quit.")
        
        try:
            while self.running:
                # Frame oku
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    # Video dosyası için başa dön
                    if not str(self.camera_source).startswith(("http", "rtsp")):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Frame'i işle
                processed_frame = self._process_frame(frame)
                
                # Video kaydet
                if self.writer is not None:
                    self.writer.write(processed_frame)
                
                # Görüntüle
                if self.show_display:
                    cv2.imshow("Animal Tracking System", processed_frame)
                    
                    # Klavye kontrolü
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        logger.info("Quit requested")
                        break
                    elif key == ord("s"):
                        # Snapshot kaydet
                        self._save_snapshot(processed_frame)
                    elif key == ord("r"):
                        # FPS counter sıfırla
                        self.fps_counter.reset()
                        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            self.cleanup()
    
    def _save_snapshot(self, frame: np.ndarray):
        """Snapshot kaydet"""
        from src.core.utils import get_timestamp_filename
        
        output_dir = ROOT_DIR / "data" / "snapshots"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / f"snapshot_{get_timestamp_filename()}.jpg"
        cv2.imwrite(str(filename), frame)
        logger.info(f"Snapshot saved: {filename}")
    
    def cleanup(self):
        """Kaynakları temizle"""
        logger.info("Cleaning up...")
        self.running = False
        
        if self.cap is not None:
            self.cap.release()
        
        if self.writer is not None:
            self.writer.release()
        
        cv2.destroyAllWindows()
        logger.info("Cleanup complete")
    
    def stop(self):
        """Uygulamayı durdur"""
        self.running = False


def signal_handler(signum, frame):
    """Sinyal handler'ı"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def parse_args():
    """Komut satırı argümanlarını parse et"""
    parser = argparse.ArgumentParser(
        description="AI Animal Tracking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --camera 0                              # USB webcam
  %(prog)s --camera "rtsp://192.168.1.100:554"     # IP kamera (RTSP)
  %(prog)s --camera "http://192.168.1.100:8080/video"  # Telefon (IP Webcam)
  %(prog)s --camera video.mp4                      # Video dosyası
        """
    )
    
    parser.add_argument(
        "--camera", "-c",
        type=str,
        default="0",
        help="Camera source (index, URL, or file path)"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="yolov8n.pt",
        help="YOLO model name (default: yolov8n.pt)"
    )
    
    parser.add_argument(
        "--confidence", "-conf",
        type=float,
        default=0.5,
        help="Detection confidence threshold (default: 0.5)"
    )
    
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable video display"
    )
    
    parser.add_argument(
        "--save-video", "-s",
        action="store_true",
        help="Save output video"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output video path"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    return parser.parse_args()


def main():
    """Ana fonksiyon"""
    # Argümanları parse et
    args = parse_args()
    
    # Logging ayarla
    setup_logging(log_level=args.log_level)
    
    # Sinyal handler'larını ayarla
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Uygulamayı başlat
    app = AnimalTrackingApp(
        camera_source=args.camera,
        model_name=args.model,
        confidence=args.confidence,
        show_display=not args.no_display,
        save_video=args.save_video,
        output_path=args.output,
    )
    
    app.run()


if __name__ == "__main__":
    main()
