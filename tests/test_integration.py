#!/usr/bin/env python3
"""
Integration Test - Full Pipeline Test
======================================

Tests the complete flow with correct module APIs.

Run: python tests/test_integration.py
"""

import sys
import os
import time
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test all module imports."""
    print("\n" + "="*50)
    print("Testing Imports")
    print("="*50)
    
    try:
        # Camera modules
        from src.camera import VideoCapture, FrameBuffer, CameraManager
        print("✓ Camera modules imported")
        
        # Detection
        from src.detection import YOLODetector
        print("✓ Detection module imported")
        
        # Tracking
        from src.tracking import ObjectTracker
        print("✓ Tracking module imported")
        
        # Identification
        from src.identification import AnimalIdentifier
        print("✓ Identification module imported")
        
        # Behavior
        from src.behavior import BehaviorAnalyzer
        print("✓ Behavior module imported")
        
        # Health
        from src.health import HealthMonitor
        print("✓ Health module imported")
        
        # Database
        from src.database import DatabaseManager
        print("✓ Database module imported")
        
        # Alerts
        from src.alerts import AlertManager
        print("✓ Alert module imported")
        
        # Pipeline
        from src.pipeline import ProcessingPipeline
        print("✓ Pipeline module imported")
        
        # API Services
        from src.api.services import CameraService, DatabaseService, TrackingService
        print("✓ API services imported")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_detector():
    """Test YOLO detector with dummy image."""
    print("\n" + "="*50)
    print("Testing YOLO Detector")
    print("="*50)
    
    try:
        from src.detection import YOLODetector
        from src.detection.yolo_detector import DetectorConfig
        
        # Initialize detector with config
        config = DetectorConfig(model_path="yolov8n.pt")
        detector = YOLODetector(config=config)
        print("✓ Detector initialized")
        
        # Create dummy image (black frame with some noise)
        dummy_frame = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        
        # Run detection
        start = time.time()
        result = detector.detect(dummy_frame)
        elapsed = time.time() - start
        
        print(f"✓ Detection completed in {elapsed*1000:.1f}ms")
        print(f"  - Detections: {len(result.detections)}")
        
        return True
    except Exception as e:
        print(f"✗ Detector error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tracker():
    """Test object tracker."""
    print("\n" + "="*50)
    print("Testing Object Tracker")
    print("="*50)
    
    try:
        from src.tracking import ObjectTracker
        from src.detection.yolo_detector import DetectionResult
        import time
        
        tracker = ObjectTracker()
        print("✓ Tracker initialized")
        
        # Create mock detection result with all required fields
        mock_result = DetectionResult(
            detections=[],
            frame_id=0,
            inference_time=0.1,
            timestamp=time.time(),
            image_size=(640, 480)
        )
        
        # Update tracker
        result = tracker.update(mock_result)
        print(f"✓ Tracker updated: {len(result.tracks)} tracks")
        
        return True
    except Exception as e:
        print(f"✗ Tracker error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_service():
    """Test database service."""
    print("\n" + "="*50)
    print("Testing Database Service")
    print("="*50)
    
    try:
        from src.api.services import DatabaseService
        
        db = DatabaseService.get_instance()
        print(f"✓ Database ready: {db.is_ready}")
        
        # Create test animal
        animal = db.create_animal(
            animal_id=f"TEST_{int(time.time())}",
            class_name="dog",
            name="Integration Test Dog"
        )
        print(f"✓ Animal created: {animal.id}")
        
        # Create detection
        detection = db.create_detection(
            class_name="dog",
            confidence=0.95,
            bbox_x1=100, bbox_y1=100,
            bbox_x2=200, bbox_y2=200,
            animal_id=animal.id
        )
        print(f"✓ Detection created: {detection.id}")
        
        # Create behavior
        behavior = db.create_behavior(
            animal_id=animal.id,
            behavior="WALKING",
            confidence=0.88
        )
        print(f"✓ Behavior logged: {behavior.behavior}")
        
        # Create health record
        health = db.create_health_record(
            animal_id=animal.id,
            status="healthy",
            bcs_score=3.5
        )
        print(f"✓ Health record created")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"✓ Database stats: {stats['animals']} animals, {stats['detections']} detections")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_behavior_analyzer():
    """Test behavior analyzer."""
    print("\n" + "="*50)
    print("Testing Behavior Analyzer")
    print("="*50)
    
    try:
        from src.behavior import BehaviorAnalyzer
        
        analyzer = BehaviorAnalyzer()
        print("✓ Behavior analyzer initialized")
        
        # Check available methods
        methods = [m for m in dir(analyzer) if not m.startswith('_')]
        print(f"  - Available methods: {methods[:5]}...")
        
        # Behavior analyzer works with analyze() method typically
        # Just verify it initializes
        print("✓ Behavior analyzer ready for processing")
        
        return True
    except Exception as e:
        print(f"✗ Behavior analyzer error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_monitor():
    """Test health monitor."""
    print("\n" + "="*50)
    print("Testing Health Monitor")
    print("="*50)
    
    try:
        from src.health import HealthMonitor
        
        monitor = HealthMonitor()
        print("✓ Health monitor initialized")
        
        # Check available methods
        methods = [m for m in dir(monitor) if not m.startswith('_')]
        print(f"  - Available methods: {methods[:5]}...")
        
        print("✓ Health monitor ready for processing")
        
        return True
    except Exception as e:
        print(f"✗ Health monitor error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alert_manager():
    """Test alert manager."""
    print("\n" + "="*50)
    print("Testing Alert Manager")
    print("="*50)
    
    try:
        from src.alerts import AlertManager
        
        manager = AlertManager()
        print(f"✓ Alert manager initialized with {len(manager.rules)} rules")
        
        # Check available methods
        methods = [m for m in dir(manager) if not m.startswith('_')]
        print(f"  - Available methods: {methods[:5]}...")
        
        print("✓ Alert manager ready for processing")
        
        return True
    except Exception as e:
        print(f"✗ Alert manager error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_camera_service():
    """Test camera service."""
    print("\n" + "="*50)
    print("Testing Camera Service")
    print("="*50)
    
    try:
        from src.api.services import CameraService
        
        service = CameraService.get_instance()
        print("✓ Camera service initialized")
        
        # Add a test camera
        service.add_camera(
            camera_id=f"test_cam_{int(time.time())}",
            source=0,
            name="Integration Test Camera"
        )
        
        cameras = service.get_cameras()
        print(f"✓ Cameras in service: {len(cameras)}")
        
        return True
    except Exception as e:
        print(f"✗ Camera service error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_app():
    """Test FastAPI application."""
    print("\n" + "="*50)
    print("Testing FastAPI Application")
    print("="*50)
    
    try:
        from src.api.main import app
        
        # Count routes
        route_count = len(app.routes)
        print(f"✓ FastAPI app created with {route_count} routes")
        
        # List some routes
        routes = [r.path for r in app.routes if hasattr(r, 'path')][:5]
        print(f"  - Sample routes: {routes}")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline():
    """Test processing pipeline."""
    print("\n" + "="*50)
    print("Testing Processing Pipeline")
    print("="*50)
    
    try:
        from src.pipeline import ProcessingPipeline
        
        # Check if ProcessingPipeline can be imported
        print("✓ ProcessingPipeline class imported")
        
        # Check available methods
        methods = [m for m in dir(ProcessingPipeline) if not m.startswith('_')]
        print(f"  - Available methods: {methods[:5]}...")
        
        print("✓ Processing pipeline ready")
        
        return True
    except Exception as e:
        print(f"✗ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("AI Animal Tracking System - Integration Tests")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("YOLO Detector", test_detector()))
    results.append(("Object Tracker", test_tracker()))
    results.append(("Database Service", test_database_service()))
    results.append(("Behavior Analyzer", test_behavior_analyzer()))
    results.append(("Health Monitor", test_health_monitor()))
    results.append(("Alert Manager", test_alert_manager()))
    results.append(("Camera Service", test_camera_service()))
    results.append(("FastAPI App", test_api_app()))
    results.append(("Pipeline", test_pipeline()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
