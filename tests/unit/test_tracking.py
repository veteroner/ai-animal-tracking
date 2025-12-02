# tests/unit/test_tracking.py
"""
Tracking Module Unit Tests
==========================

ObjectTracker ve ilgili sınıflar için unit testler.
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestTrack:
    """Track sınıfı testleri."""
    
    def test_track_creation(self):
        """Track oluşturma testi."""
        from src.tracking import Track
        
        track = Track(
            track_id=1,
            class_id=19,
            class_name="cow",
            bbox=(100, 100, 200, 200),
            center=(150, 150),
            confidence=0.95
        )
        
        assert track.track_id == 1
        assert track.class_name == "cow"
        assert track.confidence == 0.95
    
    def test_track_is_confirmed(self):
        """Track doğrulama durumu testi."""
        from src.tracking import Track, TrackState
        
        track = Track(
            track_id=1,
            class_id=19,
            class_name="cow",
            bbox=(100, 100, 200, 200),
            center=(150, 150),
            confidence=0.95,
            state=TrackState.CONFIRMED
        )
        
        assert track.is_confirmed == True
        
        track.state = TrackState.TENTATIVE
        assert track.is_confirmed == False
    
    def test_track_is_active(self):
        """Track aktiflik testi."""
        from src.tracking import Track, TrackState
        
        track = Track(
            track_id=1,
            class_id=19,
            class_name="cow",
            bbox=(100, 100, 200, 200),
            center=(150, 150),
            confidence=0.95,
            state=TrackState.CONFIRMED
        )
        
        assert track.is_active == True
        
        track.state = TrackState.DELETED
        assert track.is_active == False
    
    def test_track_age(self):
        """Track yaşı testi."""
        from src.tracking import Track
        
        track = Track(
            track_id=1,
            class_id=19,
            class_name="cow",
            bbox=(100, 100, 200, 200),
            center=(150, 150),
            confidence=0.95,
            first_seen_frame=10,
            last_seen_frame=50
        )
        
        assert track.age == 40


class TestTrackState:
    """TrackState testleri."""
    
    def test_track_states(self):
        """Track durumları testi."""
        from src.tracking import TrackState
        
        assert TrackState.TENTATIVE == 1
        assert TrackState.CONFIRMED == 2
        assert TrackState.DELETED == 3


class TestTrackerConfig:
    """TrackerConfig testleri."""
    
    def test_default_config(self):
        """Varsayılan config testi."""
        from src.tracking import TrackerConfig
        
        config = TrackerConfig()
        
        assert config.tracker_type == "bytetrack"
        assert config.track_buffer == 30
        assert config.min_hits == 3
    
    def test_custom_config(self):
        """Özel config testi."""
        from src.tracking import TrackerConfig
        
        config = TrackerConfig(
            tracker_type="botsort",
            track_buffer=60,
            min_hits=5
        )
        
        assert config.tracker_type == "botsort"
        assert config.track_buffer == 60
        assert config.min_hits == 5


class TestTrackingResult:
    """TrackingResult testleri."""
    
    def test_empty_tracking_result(self):
        """Boş TrackingResult testi."""
        from src.tracking import TrackingResult
        
        result = TrackingResult(
            tracks=[],
            frame_id=1,
            timestamp=datetime.now().timestamp()
        )
        
        assert result.count == 0
        assert len(result.tracks) == 0
    
    def test_tracking_result_with_tracks(self):
        """Track'li TrackingResult testi."""
        from src.tracking import Track, TrackingResult
        
        tracks = [
            Track(track_id=1, class_id=19, class_name="cow", bbox=(0, 0, 100, 100), center=(50, 50), confidence=0.9),
            Track(track_id=2, class_id=18, class_name="sheep", bbox=(100, 100, 200, 200), center=(150, 150), confidence=0.85),
        ]
        
        result = TrackingResult(
            tracks=tracks,
            frame_id=1,
            timestamp=datetime.now().timestamp()
        )
        
        assert result.count == 2


class TestObjectTracker:
    """ObjectTracker sınıfı testleri."""
    
    def test_tracker_initialization(self):
        """Tracker başlatma testi."""
        from src.tracking import ObjectTracker
        
        tracker = ObjectTracker()
        
        assert tracker is not None
    
    def test_tracker_reset(self):
        """Tracker reset testi."""
        from src.tracking import ObjectTracker
        
        tracker = ObjectTracker()
        
        tracker.reset()
        
        # Reset sonrası track sayısı 0 olmalı
        stats = tracker.statistics
        assert stats["active_tracks"] == 0
    
    def test_tracker_statistics(self):
        """Tracker istatistik testi."""
        from src.tracking import ObjectTracker
        
        tracker = ObjectTracker()
        
        stats = tracker.statistics
        
        assert "total_tracks_created" in stats
        assert "active_tracks" in stats
        assert "frame_count" in stats


# Pytest fixtures
@pytest.fixture
def sample_tracks():
    """Örnek track listesi."""
    from src.tracking import Track
    return [
        Track(track_id=1, class_id=19, class_name="cow", bbox=(0, 0, 100, 100), center=(50, 50), confidence=0.95),
        Track(track_id=2, class_id=18, class_name="sheep", bbox=(100, 100, 200, 200), center=(150, 150), confidence=0.90),
        Track(track_id=3, class_id=16, class_name="dog", bbox=(200, 200, 300, 300), center=(250, 250), confidence=0.85),
    ]


@pytest.fixture
def tracker():
    """ObjectTracker instance."""
    from src.tracking import ObjectTracker
    return ObjectTracker()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
