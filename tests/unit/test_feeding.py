# tests/unit/test_feeding.py
"""
Feeding Module Unit Tests
=========================

FeedTracker ve FeedEstimator için unit testler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class TestFeedingZone:
    """FeedingZone testleri."""
    
    def test_zone_creation(self):
        """Zone oluşturma testi."""
        from src.feeding.feed_tracker import FeedingZone
        
        zone = FeedingZone(
            zone_id="zone_1",
            name="Yemlik 1",
            bbox=(100, 100, 300, 300)
        )
        
        assert zone.zone_id == "zone_1"
        assert zone.name == "Yemlik 1"
        assert zone.bbox == (100, 100, 300, 300)
    
    def test_zone_contains_inside(self):
        """Zone içinde nokta testi."""
        from src.feeding.feed_tracker import FeedingZone
        
        zone = FeedingZone(
            zone_id="z1",
            name="Test",
            bbox=(0, 0, 100, 100)
        )
        
        # İçerideki nokta
        assert zone.contains((50, 50)) == True
        assert zone.contains((0, 0)) == True
        assert zone.contains((99, 99)) == True
    
    def test_zone_contains_outside(self):
        """Zone dışında nokta testi."""
        from src.feeding.feed_tracker import FeedingZone
        
        zone = FeedingZone(
            zone_id="z1",
            name="Test",
            bbox=(0, 0, 100, 100)
        )
        
        # Dışarıdaki nokta
        assert zone.contains((150, 150)) == False
        assert zone.contains((-10, 50)) == False
        assert zone.contains((50, 150)) == False


class TestFeedingSession:
    """FeedingSession testleri."""
    
    def test_session_creation(self):
        """Session oluşturma testi."""
        from src.feeding.feed_tracker import FeedingSession
        
        session = FeedingSession(
            session_id="s1",
            animal_id="cow_001",
            zone_id="zone_1",
            start_time=datetime.now()
        )
        
        assert session.session_id == "s1"
        assert session.animal_id == "cow_001"
        assert session.zone_id == "zone_1"
        assert session.end_time is None
    
    def test_session_duration(self):
        """Session süre hesaplama testi."""
        from src.feeding.feed_tracker import FeedingSession
        
        start = datetime.now() - timedelta(minutes=10)
        end = datetime.now()
        
        session = FeedingSession(
            session_id="s1",
            animal_id="cow_001",
            zone_id="zone_1",
            start_time=start
        )
        session.end_time = end
        
        # Duration yaklaşık 600 saniye olmalı
        assert 590 <= session.duration <= 610
    
    def test_session_is_active(self):
        """Session aktiflik testi."""
        from src.feeding.feed_tracker import FeedingSession
        
        session = FeedingSession(
            session_id="s1",
            animal_id="cow_001",
            zone_id="zone_1",
            start_time=datetime.now()
        )
        
        # end_time None = aktif
        assert session.is_active == True
        
        # end_time set = tamamlanmış
        session.end_time = datetime.now()
        assert session.is_active == False


class TestFeedTracker:
    """FeedTracker testleri."""
    
    def test_tracker_initialization(self):
        """Tracker başlatma testi."""
        from src.feeding.feed_tracker import FeedTracker
        
        tracker = FeedTracker(
            session_timeout=300,
            min_session_duration=5.0
        )
        
        assert tracker.session_timeout == 300
        assert tracker.min_session_duration == 5.0
        assert len(tracker._zones) == 0
    
    def test_add_zone(self):
        """Zone ekleme testi."""
        from src.feeding.feed_tracker import FeedTracker
        
        tracker = FeedTracker()
        tracker.add_zone(
            zone_id="zone_1",
            name="Yemlik 1",
            bbox=(0, 0, 100, 100)
        )
        
        assert "zone_1" in tracker._zones
        assert tracker._zones["zone_1"].name == "Yemlik 1"
    
    def test_remove_zone(self):
        """Zone kaldırma testi."""
        from src.feeding.feed_tracker import FeedTracker
        
        tracker = FeedTracker()
        tracker.add_zone("z1", "Zone 1", (0, 0, 100, 100))
        tracker.add_zone("z2", "Zone 2", (100, 100, 200, 200))
        
        assert len(tracker._zones) == 2
        
        tracker.remove_zone("z1")
        
        assert len(tracker._zones) == 1
        assert "z2" in tracker._zones
    
    def test_get_zones(self):
        """Zone listesi alma testi."""
        from src.feeding.feed_tracker import FeedTracker
        
        tracker = FeedTracker()
        tracker.add_zone("z1", "Zone 1", (0, 0, 100, 100))
        tracker.add_zone("z2", "Zone 2", (100, 100, 200, 200))
        
        zones = tracker.get_zones()
        
        assert len(zones) == 2


class TestFeedEstimator:
    """FeedEstimator testleri."""
    
    def test_estimator_initialization(self):
        """Estimator başlatma testi."""
        from src.feeding.feed_estimator import FeedEstimator
        
        estimator = FeedEstimator()
        
        assert "cow" in estimator._consumption_rates
        assert "sheep" in estimator._consumption_rates
    
    def test_default_rates(self):
        """Varsayılan tüketim hızları testi."""
        from src.feeding.feed_estimator import FeedEstimator
        
        rates = FeedEstimator.DEFAULT_RATES
        
        assert rates["cow"] == 0.5
        assert rates["sheep"] == 0.1
        assert rates["goat"] == 0.08
    
    def test_set_consumption_rate(self):
        """Tüketim hızı ayarlama testi."""
        from src.feeding.feed_estimator import FeedEstimator
        
        estimator = FeedEstimator()
        estimator.set_consumption_rate("cow", 0.6)
        
        rate = estimator.get_consumption_rate("any", "cow")
        assert rate == 0.6
    
    def test_animal_specific_rate(self):
        """Hayvan bazında özel hız testi."""
        from src.feeding.feed_estimator import FeedEstimator
        
        estimator = FeedEstimator()
        estimator.set_consumption_rate("cow_001", 0.45, is_animal_specific=True)
        
        rate = estimator.get_consumption_rate("cow_001", "cow")
        assert rate == 0.45
    
    def test_estimate_consumption(self):
        """Tüketim tahmini testi."""
        from src.feeding.feed_estimator import FeedEstimator
        from src.feeding.feed_tracker import FeedingSession
        
        estimator = FeedEstimator()
        estimator.set_consumption_rate("cow", 0.5)  # 0.5 kg/dk
        
        # 10 dakikalık seans
        session = FeedingSession(
            session_id="s1",
            animal_id="cow_001",
            zone_id="z1",
            start_time=datetime.now() - timedelta(minutes=10)
        )
        session.end_time = datetime.now()
        
        estimate = estimator.estimate_consumption(
            "cow_001",
            [session],
            species="cow"
        )
        
        # 10 dk * 0.5 kg/dk = 5 kg
        assert 4.9 <= estimate.estimated_kg <= 5.1
    
    def test_add_calibration(self):
        """Kalibrasyon testi."""
        from src.feeding.feed_estimator import FeedEstimator
        
        estimator = FeedEstimator()
        
        # 10 dakika = 600 saniye, gerçek tüketim 4.5 kg
        estimator.add_calibration("cow_001", 600, 4.5)
        
        # Yeni rate = 4.5 / 10 = 0.45 kg/dk
        rate = estimator.get_consumption_rate("cow_001", "cow")
        assert 0.44 <= rate <= 0.46


class TestFeedConsumptionEstimate:
    """FeedConsumptionEstimate testleri."""
    
    def test_estimate_to_dict(self):
        """Estimate dict dönüşüm testi."""
        from src.feeding.feed_estimator import FeedConsumptionEstimate
        
        estimate = FeedConsumptionEstimate(
            animal_id="cow_001",
            period_start=datetime.now() - timedelta(hours=1),
            period_end=datetime.now(),
            estimated_kg=5.5,
            confidence=0.8,
            total_feeding_time_minutes=11.0,
            session_count=2
        )
        
        d = estimate.to_dict()
        
        assert d["animal_id"] == "cow_001"
        assert d["estimated_kg"] == 5.5
        assert d["confidence"] == 0.8
        assert d["session_count"] == 2


# Pytest fixtures
@pytest.fixture
def feed_tracker():
    """FeedTracker instance."""
    from src.feeding.feed_tracker import FeedTracker
    
    tracker = FeedTracker()
    tracker.add_zone("zone_1", (0, 0, 100, 100), "Yemlik 1")
    tracker.add_zone("zone_2", (200, 200, 300, 300), "Yemlik 2")
    return tracker


@pytest.fixture
def feed_estimator():
    """FeedEstimator instance."""
    from src.feeding.feed_estimator import FeedEstimator
    return FeedEstimator()


@pytest.fixture
def sample_session():
    """Örnek FeedingSession."""
    from src.feeding.feed_tracker import FeedingSession
    
    return FeedingSession(
        session_id="test_session",
        animal_id="cow_001",
        zone_id="zone_1",
        start_time=datetime.now() - timedelta(minutes=15)
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
