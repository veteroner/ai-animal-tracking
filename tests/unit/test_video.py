"""
Video modülü unit testleri.
"""

import pytest
import numpy as np
import tempfile
import os
from datetime import datetime
from pathlib import Path


class TestVideoConfig:
    """VideoConfig testleri."""
    
    def test_default_config(self):
        """Default konfigürasyon testi."""
        from src.video import VideoConfig
        
        config = VideoConfig()
        
        assert config.fps == 30.0
        assert config.quality == 95
        assert config.buffer_size == 100
    
    def test_custom_config(self):
        """Özel konfigürasyon testi."""
        from src.video import VideoConfig, VideoFormat, VideoCodec
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(
                output_dir=tmpdir,
                format=VideoFormat.AVI,
                codec=VideoCodec.MJPEG,
                fps=60.0,
                quality=80
            )
            
            assert config.format == VideoFormat.AVI
            assert config.codec == VideoCodec.MJPEG
            assert config.fps == 60.0
            assert config.quality == 80
    
    def test_quality_bounds(self):
        """Quality değerinin sınırlandırılması testi."""
        from src.video import VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config1 = VideoConfig(output_dir=tmpdir, quality=150)
            assert config1.quality == 100  # Max 100
            
            config2 = VideoConfig(output_dir=tmpdir, quality=-10)
            assert config2.quality == 0  # Min 0


class TestAnnotationStyle:
    """AnnotationStyle testleri."""
    
    def test_default_style(self):
        """Default stil testi."""
        from src.video import AnnotationStyle
        
        style = AnnotationStyle()
        
        assert style.bbox_thickness == 2
        assert style.show_confidence is True
        assert style.show_class_name is True
        assert style.show_track_id is True
    
    def test_custom_style(self):
        """Özel stil testi."""
        from src.video import AnnotationStyle
        
        style = AnnotationStyle(
            bbox_color=(255, 0, 0),
            bbox_thickness=3,
            show_confidence=False
        )
        
        assert style.bbox_color == (255, 0, 0)
        assert style.bbox_thickness == 3
        assert style.show_confidence is False


class TestFrameAnnotator:
    """FrameAnnotator testleri."""
    
    def test_annotator_creation(self):
        """Annotator oluşturma testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        
        assert annotator is not None
        assert annotator.style is not None
    
    def test_get_color_for_class(self):
        """Sınıf rengi testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        
        # Aynı sınıf için tutarlı renk
        color1 = annotator.get_color_for_class("dog")
        color2 = annotator.get_color_for_class("dog")
        
        assert color1 == color2
        
        # Farklı sınıflar farklı renk olabilir
        color3 = annotator.get_color_for_class("cat")
        # Renkler tuple olmalı
        assert isinstance(color1, tuple)
        assert len(color1) == 3
    
    def test_annotate_detection(self):
        """Detection annotation testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        
        # Test frame oluştur (beyaz frame - annotation görünür olsun)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        original = frame.copy()
        
        annotated = annotator.annotate_detection(
            frame=frame,
            bbox=(100, 100, 200, 200),
            class_name="dog",
            confidence=0.95,
            track_id=1
        )
        
        # Frame boyutu değişmemeli
        assert annotated.shape == original.shape
        # Dönen frame orijinaliyle aynı referans olmalı (in-place modification)
        assert annotated is frame
    
    def test_annotate_detections(self):
        """Çoklu detection annotation testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        detections = [
            {"bbox": (50, 50, 150, 150), "class_name": "dog", "confidence": 0.9},
            {"bbox": (200, 200, 300, 300), "class_name": "cat", "confidence": 0.85},
        ]
        
        annotated = annotator.annotate_detections(frame, detections)
        
        assert annotated.shape == frame.shape
    
    def test_add_timestamp(self):
        """Timestamp ekleme testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        timestamped = annotator.add_timestamp(frame)
        
        assert timestamped.shape == frame.shape
    
    def test_add_info_overlay(self):
        """Info overlay testi."""
        from src.video import FrameAnnotator
        
        annotator = FrameAnnotator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        info = {
            "FPS": 30,
            "Detections": 5,
            "Tracks": 3
        }
        
        with_overlay = annotator.add_info_overlay(frame, info)
        
        assert with_overlay.shape == frame.shape


class TestRecordingInfo:
    """RecordingInfo testleri."""
    
    def test_recording_info_creation(self):
        """RecordingInfo oluşturma testi."""
        from src.video import RecordingInfo
        
        info = RecordingInfo(
            filename="test.mp4",
            filepath="/tmp/test.mp4",
            start_time=datetime.now(),
            resolution=(1920, 1080),
            fps=30.0
        )
        
        assert info.filename == "test.mp4"
        assert info.frame_count == 0
        assert info.detection_count == 0
    
    def test_to_dict(self):
        """Dict dönüşüm testi."""
        from src.video import RecordingInfo
        
        info = RecordingInfo(
            filename="test.mp4",
            filepath="/tmp/test.mp4",
            start_time=datetime.now(),
            resolution=(1920, 1080),
            fps=30.0,
            frame_count=100,
            duration_seconds=3.33
        )
        
        data = info.to_dict()
        
        assert data["filename"] == "test.mp4"
        assert data["frame_count"] == 100
        assert data["resolution"] == "1920x1080"
        assert "start_time" in data


class TestVideoRecorder:
    """VideoRecorder testleri."""
    
    def test_recorder_initialization(self):
        """Recorder başlatma testi."""
        from src.video import VideoRecorder, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            recorder = VideoRecorder(config)
            
            assert recorder.is_recording is False
            assert recorder.current_recording is None
    
    def test_start_stop_recording(self):
        """Kayıt başlatma/durdurma testi."""
        from src.video import VideoRecorder, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            recorder = VideoRecorder(config)
            
            # Kaydı başlat
            filepath = recorder.start_recording(resolution=(640, 480))
            
            assert recorder.is_recording is True
            assert recorder.current_recording is not None
            assert filepath.endswith(".mp4")
            
            # Birkaç frame yaz
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(10):
                recorder.write_frame(frame)
            
            # Kaydı durdur
            import time
            time.sleep(0.2)  # Buffer'ın yazılması için bekle
            
            info = recorder.stop_recording()
            
            assert recorder.is_recording is False
            assert info is not None
            assert info.frame_count > 0
    
    def test_write_frame_with_detections(self):
        """Detection'lı frame yazma testi."""
        from src.video import VideoRecorder, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            recorder = VideoRecorder(config)
            
            recorder.start_recording(resolution=(640, 480))
            
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = [
                {"bbox": (50, 50, 150, 150), "class_name": "dog", "confidence": 0.9}
            ]
            
            result = recorder.write_frame(frame, detections=detections, annotate=True)
            
            assert result is True
            
            import time
            time.sleep(0.1)
            
            recorder.stop_recording()
    
    def test_get_statistics(self):
        """İstatistik testi."""
        from src.video import VideoRecorder, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            recorder = VideoRecorder(config)
            
            stats = recorder.get_statistics()
            
            assert "total_recordings" in stats
            assert "is_recording" in stats
            assert "buffer_usage" in stats


class TestVideoClipExtractor:
    """VideoClipExtractor testleri."""
    
    def test_extractor_initialization(self):
        """Extractor başlatma testi."""
        from src.video import VideoClipExtractor, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            extractor = VideoClipExtractor(config)
            
            assert extractor is not None
    
    def test_add_frame_to_buffer(self):
        """Buffer'a frame ekleme testi."""
        from src.video import VideoClipExtractor, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            extractor = VideoClipExtractor(config)
            
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Frame ekle
            extractor.add_frame(frame)
            extractor.add_frame(frame)
            
            # Buffer'da frame olmalı
            assert len(extractor._frame_buffer) == 2
    
    def test_clear_buffer(self):
        """Buffer temizleme testi."""
        from src.video import VideoClipExtractor, VideoConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VideoConfig(output_dir=tmpdir)
            extractor = VideoClipExtractor(config)
            
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            extractor.add_frame(frame)
            extractor.add_frame(frame)
            
            extractor.clear_buffer()
            
            assert len(extractor._frame_buffer) == 0


class TestVideoPlayer:
    """VideoPlayer testleri."""
    
    def test_player_initialization(self):
        """Player başlatma testi."""
        from src.video import VideoPlayer
        
        player = VideoPlayer()
        
        assert player._is_playing is False
        assert player.total_frames == 0
    
    def test_get_info_without_video(self):
        """Video olmadan bilgi alma testi."""
        from src.video import VideoPlayer
        
        player = VideoPlayer()
        
        info = player.get_info()
        
        assert info == {}


class TestVideoFormat:
    """VideoFormat enum testleri."""
    
    def test_video_formats(self):
        """Video format değerleri testi."""
        from src.video import VideoFormat
        
        assert VideoFormat.MP4.value == "mp4"
        assert VideoFormat.AVI.value == "avi"
        assert VideoFormat.MKV.value == "mkv"
        assert VideoFormat.MOV.value == "mov"


class TestVideoCodec:
    """VideoCodec enum testleri."""
    
    def test_video_codecs(self):
        """Video codec değerleri testi."""
        from src.video import VideoCodec
        
        assert VideoCodec.H264.value == "avc1"
        assert VideoCodec.MJPEG.value == "MJPG"
        assert VideoCodec.XVID.value == "XVID"
