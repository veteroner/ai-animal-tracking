#!/usr/bin/env python3
"""
AI Animal Tracking System - Quick Demo
=======================================

Webcam ile hızlı test scripti.
Hayvan ve nesne tespiti + tracking gösterir.

Kullanım:
    python demo.py                  # Webcam (varsayılan)
    python demo.py --source 0       # Webcam index
    python demo.py --source video.mp4   # Video dosyası
    python demo.py --animals-only   # Sadece hayvanlar
"""

import argparse
import sys
import time
import logging
from pathlib import Path

import cv2
import numpy as np

# Project path
sys.path.insert(0, str(Path(__file__).parent))

from src.detection import YOLODetector, Detection, DetectionResult
from src.tracking import ObjectTracker, TrackingResult


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("demo")


def draw_trajectory(
    frame: np.ndarray,
    track,
    color: tuple = (0, 255, 255),
    max_points: int = 50
) -> np.ndarray:
    """Track trajectory'sini çiz"""
    if len(track.history) < 2:
        return frame
    
    points = track.history[-max_points:]
    
    for i in range(1, len(points)):
        alpha = i / len(points)  # Fade effect
        thickness = max(1, int(3 * alpha))
        pt1 = tuple(points[i-1])
        pt2 = tuple(points[i])
        cv2.line(frame, pt1, pt2, color, thickness)
    
    return frame


def draw_info_panel(
    frame: np.ndarray,
    detection_result: DetectionResult,
    tracking_result: TrackingResult,
) -> np.ndarray:
    """Bilgi paneli çiz"""
    h, w = frame.shape[:2]
    
    # Yarı saydam arka plan
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (300, 130), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    
    # Bilgiler
    fps = 1000 / detection_result.inference_time if detection_result.inference_time > 0 else 0
    
    info_lines = [
        f"FPS: {fps:.1f}",
        f"Inference: {detection_result.inference_time:.1f} ms",
        f"Detections: {detection_result.count}",
        f"Animals: {detection_result.animal_count}",
        f"Active Tracks: {tracking_result.count}",
    ]
    
    y = 35
    for line in info_lines:
        cv2.putText(frame, line, (20, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y += 20
    
    return frame


def draw_help(frame: np.ndarray) -> np.ndarray:
    """Yardım metni çiz"""
    h, w = frame.shape[:2]
    
    help_text = "Q:Quit | A:Animals | T:Trajectory | R:Reset"
    cv2.putText(frame, help_text, (10, h - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame


def main():
    parser = argparse.ArgumentParser(description="AI Animal Tracking Demo")
    parser.add_argument("--source", type=str, default="0",
                       help="Video source (webcam index, file path, or RTSP URL)")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                       help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=0.5,
                       help="Detection confidence threshold")
    parser.add_argument("--animals-only", action="store_true",
                       help="Detect only animals")
    parser.add_argument("--no-tracking", action="store_true",
                       help="Disable object tracking")
    parser.add_argument("--save", type=str, default=None,
                       help="Save output to video file")
    
    args = parser.parse_args()
    
    # Source
    source = args.source
    if source.isdigit():
        source = int(source)
    
    logger.info(f"Starting demo with source: {source}")
    
    # Detector
    logger.info("Loading YOLO model...")
    detector = YOLODetector(
        model_path=args.model,
        confidence_threshold=args.confidence,
        only_animals=args.animals_only,
    )
    detector.warmup()
    
    # Tracker
    tracker = ObjectTracker() if not args.no_tracking else None
    
    # Video capture
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        logger.error(f"Failed to open video source: {source}")
        return 1
    
    # Video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    
    logger.info(f"Video: {frame_width}x{frame_height} @ {fps} FPS")
    
    # Video writer
    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.save, fourcc, fps, (frame_width, frame_height))
        logger.info(f"Saving output to: {args.save}")
    
    # State
    animals_only = args.animals_only
    show_trajectory = True
    
    logger.info("Press 'Q' to quit, 'A' to toggle animals only, 'T' for trajectory, 'R' to reset")
    
    try:
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                if isinstance(source, str) and not source.startswith("rtsp"):
                    # Video file ended
                    break
                continue
            
            frame_count += 1
            
            # Detection
            if tracker and not args.no_tracking:
                detection_result = detector.track(frame)
            else:
                classes = None if not animals_only else None  # Use config
                detection_result = detector.detect(frame, classes=classes)
            
            # Tracking
            if tracker:
                tracking_result = tracker.update(detection_result)
            else:
                tracking_result = TrackingResult(
                    tracks=[],
                    frame_id=frame_count,
                    timestamp=time.time(),
                )
            
            # Draw
            output = detector.draw_detections(frame, detection_result)
            
            # Trajectory
            if show_trajectory and tracker:
                for track in tracking_result.tracks:
                    output = draw_trajectory(output, track)
            
            # Info panel
            output = draw_info_panel(output, detection_result, tracking_result)
            output = draw_help(output)
            
            # Display
            cv2.imshow("AI Animal Tracking Demo", output)
            
            # Save
            if writer:
                writer.write(output)
            
            # Key handling
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                break
            elif key == ord('a'):
                animals_only = not animals_only
                detector.config.only_animals = animals_only
                logger.info(f"Animals only: {animals_only}")
            elif key == ord('t'):
                show_trajectory = not show_trajectory
                logger.info(f"Show trajectory: {show_trajectory}")
            elif key == ord('r'):
                if tracker:
                    tracker.reset()
                    detector.reset_tracker()
                    logger.info("Tracker reset")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        # Stats
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        print("\n" + "="*50)
        print("Session Statistics")
        print("="*50)
        print(f"Total frames: {frame_count}")
        print(f"Elapsed time: {elapsed:.2f} seconds")
        print(f"Average FPS: {avg_fps:.2f}")
        print()
        print("Detector Stats:")
        for k, v in detector.statistics.items():
            print(f"  {k}: {v}")
        
        if tracker:
            print()
            print("Tracker Stats:")
            for k, v in tracker.statistics.items():
                print(f"  {k}: {v}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
