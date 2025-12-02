# tests/unit/test_detection.py
"""
Detection Module Unit Tests
===========================

YOLODetector ve ilgili sınıflar için unit testler.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestDetection:
    """Detection dataclass testleri."""
    
    def test_detection_creation(self):
        """Detection nesnesi oluşturma testi."""
        from src.detection import Detection
        
        det = Detection(
            bbox=(100, 100, 200, 200),
            confidence=0.95,
            class_id=16,
            class_name="dog",
            center=(150, 150),
            area=10000
        )
        
        assert det.bbox == (100, 100, 200, 200)
        assert det.confidence == 0.95
        assert det.class_id == 16
        assert det.class_name == "dog"
    
    def test_detection_center(self):
        """Detection center testi."""
        from src.detection import Detection
        
        det = Detection(
            bbox=(100, 100, 200, 200),
            confidence=0.9,
            class_id=0,
            class_name="person",
            center=(150, 150),
            area=10000
        )
        
        assert det.center == (150, 150)
    
    def test_detection_area(self):
        """Detection alan testi."""
        from src.detection import Detection
        
        det = Detection(
            bbox=(0, 0, 100, 100),
            confidence=0.9,
            class_id=0,
            class_name="person",
            center=(50, 50),
            area=10000
        )
        
        assert det.area == 10000
    
    def test_detection_is_animal(self):
        """Detection is_animal testi."""
        from src.detection import Detection
        
        # Hayvan (cow = 19)
        det_animal = Detection(
            bbox=(0, 0, 100, 100),
            confidence=0.9,
            class_id=19,
            class_name="cow",
            center=(50, 50),
            area=10000
        )
        assert det_animal.is_animal == True
        
        # Person (0) hayvan değil
        det_person = Detection(
            bbox=(0, 0, 100, 100),
            confidence=0.9,
            class_id=0,
            class_name="person",
            center=(50, 50),
            area=10000
        )
        assert det_person.is_animal == False
    
    def test_detection_to_dict(self):
        """Detection dict dönüşüm testi."""
        from src.detection import Detection
        
        det = Detection(
            bbox=(100, 100, 200, 200),
            confidence=0.95,
            class_id=16,
            class_name="dog",
            center=(150, 150),
            area=10000,
            track_id=5
        )
        
        d = det.to_dict()
        
        assert d["class_name"] == "dog"
        assert d["confidence"] == 0.95
        assert d["track_id"] == 5
        assert "bbox" in d


class TestDetectionResult:
    """DetectionResult testleri."""
    
    def test_detection_result_empty(self):
        """Boş DetectionResult testi."""
        from src.detection import DetectionResult
        
        result = DetectionResult(
            detections=[],
            frame_id=1,
            timestamp=datetime.now(),
            inference_time=10.0,
            image_size=(640, 480)
        )
        
        assert result.count == 0
        assert result.animal_count == 0
    
    def test_detection_result_with_detections(self):
        """Detection'lı result testi."""
        from src.detection import Detection, DetectionResult
        
        detections = [
            Detection(bbox=(0, 0, 100, 100), confidence=0.9, class_id=16, class_name="dog", center=(50,50), area=10000),
            Detection(bbox=(100, 100, 200, 200), confidence=0.8, class_id=15, class_name="cat", center=(150,150), area=10000),
            Detection(bbox=(200, 200, 300, 300), confidence=0.7, class_id=0, class_name="person", center=(250,250), area=10000),
        ]
        
        result = DetectionResult(
            detections=detections,
            frame_id=1,
            timestamp=datetime.now(),
            inference_time=15.0,
            image_size=(640, 480)
        )
        
        assert result.count == 3
        # dog ve cat hayvan, person değil
        assert result.animal_count == 2


class TestYOLODetectorConfig:
    """YOLODetector config testleri."""
    
    def test_default_config(self):
        """Varsayılan config testi."""
        from src.detection.yolo_detector import DetectorConfig
        
        config = DetectorConfig()
        
        assert config.model_path == "yolov8n.pt"
        assert config.confidence_threshold == 0.5
        assert config.iou_threshold == 0.45
        assert config.only_animals == True
    
    def test_custom_config(self):
        """Özel config testi."""
        from src.detection.yolo_detector import DetectorConfig
        
        config = DetectorConfig(
            model_path="yolov8s.pt",
            confidence_threshold=0.7,
            only_animals=False
        )
        
        assert config.model_path == "yolov8s.pt"
        assert config.confidence_threshold == 0.7
        assert config.only_animals == False


class TestAnimalClasses:
    """Hayvan sınıfları testleri."""
    
    def test_coco_animal_classes(self):
        """COCO hayvan sınıfları testi."""
        from src.detection.yolo_detector import COCO_ANIMAL_CLASSES
        
        # Bilinen hayvan ID'leri
        assert 16 in COCO_ANIMAL_CLASSES  # dog
        assert 15 in COCO_ANIMAL_CLASSES  # cat
        assert 17 in COCO_ANIMAL_CLASSES  # horse
        assert 18 in COCO_ANIMAL_CLASSES  # sheep
        assert 19 in COCO_ANIMAL_CLASSES  # cow
        
        # person hayvan değil
        assert 0 not in COCO_ANIMAL_CLASSES
    
    def test_animal_class_names(self):
        """Hayvan sınıf isimleri testi."""
        from src.detection.yolo_detector import COCO_ANIMAL_CLASSES
        
        names = list(COCO_ANIMAL_CLASSES.values())
        
        assert "dog" in names
        assert "cat" in names
        assert "cow" in names
        assert "sheep" in names
        assert "horse" in names


class TestYOLODetectorMocked:
    """Mock ile YOLODetector testleri."""
    
    @patch('src.detection.yolo_detector.YOLO')
    def test_detector_initialization(self, mock_yolo):
        """Detector başlatma testi."""
        from src.detection.yolo_detector import YOLODetector
        
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        detector = YOLODetector(model_path="yolov8n.pt")
        
        mock_yolo.assert_called_once_with("yolov8n.pt")
        assert detector.model == mock_model
    
    @patch('src.detection.yolo_detector.YOLO')
    def test_detector_detect_empty_frame(self, mock_yolo):
        """Boş frame tespit testi."""
        from src.detection.yolo_detector import YOLODetector
        
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        # Mock boş sonuç
        mock_result = MagicMock()
        mock_result.boxes = MagicMock()
        mock_result.boxes.data = MagicMock()
        mock_result.boxes.data.cpu.return_value.numpy.return_value = np.array([])
        mock_model.return_value = [mock_result]
        
        detector = YOLODetector()
        
        # Boş frame ile test
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(frame)
        
        assert result.count == 0


# Pytest fixtures
@pytest.fixture
def sample_frame():
    """Örnek video frame."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_detection():
    """Örnek detection."""
    from src.detection import Detection
    return Detection(
        bbox=(100, 100, 200, 200),
        confidence=0.95,
        class_id=19,
        class_name="cow",
        center=(150, 150),
        area=10000
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
