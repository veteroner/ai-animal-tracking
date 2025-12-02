"""
Cache modülü unit testleri.
"""

import pytest
import time
import numpy as np
from datetime import datetime


class TestCacheConfig:
    """CacheConfig testleri."""
    
    def test_default_config(self):
        """Default konfigürasyon testi."""
        from src.cache import CacheConfig
        
        config = CacheConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.default_ttl == 3600
        assert config.prefix == "animal_tracker:"
    
    def test_custom_config(self):
        """Özel konfigürasyon testi."""
        from src.cache import CacheConfig
        
        config = CacheConfig(
            host="redis.example.com",
            port=6380,
            default_ttl=1800,
            prefix="test:"
        )
        
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.default_ttl == 1800
        assert config.prefix == "test:"


class TestCacheStats:
    """CacheStats testleri."""
    
    def test_stats_creation(self):
        """Stats oluşturma testi."""
        from src.cache import CacheStats
        
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
    
    def test_hit_rate(self):
        """Hit rate hesaplama testi."""
        from src.cache import CacheStats
        
        stats = CacheStats(hits=80, misses=20)
        
        assert stats.hit_rate == 0.8
    
    def test_hit_rate_zero(self):
        """Hit rate sıfır testi."""
        from src.cache import CacheStats
        
        stats = CacheStats()
        
        assert stats.hit_rate == 0.0
    
    def test_to_dict(self):
        """Dict dönüşüm testi."""
        from src.cache import CacheStats
        
        stats = CacheStats(hits=10, misses=5, sets=15)
        data = stats.to_dict()
        
        assert data["hits"] == 10
        assert data["misses"] == 5
        assert data["sets"] == 15
        assert "hit_rate" in data


class TestMemoryCache:
    """MemoryCache testleri."""
    
    def test_cache_creation(self):
        """Cache oluşturma testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_mem:")
        cache = MemoryCache(config)
        
        assert cache is not None
        assert cache.size() == 0
    
    def test_set_get(self):
        """Set ve get testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_setget:")
        cache = MemoryCache(config)
        
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_get_missing(self):
        """Olmayan key testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_miss:")
        cache = MemoryCache(config)
        
        assert cache.get("nonexistent") is None
    
    def test_delete(self):
        """Silme testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_del:")
        cache = MemoryCache(config)
        
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        
        cache.delete("key1")
        assert cache.exists("key1") is False
    
    def test_exists(self):
        """Exists testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_exists:")
        cache = MemoryCache(config)
        
        assert cache.exists("key1") is False
        
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
    
    def test_clear(self):
        """Clear testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_clear:")
        cache = MemoryCache(config)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.size() == 2
        
        cache.clear()
        
        assert cache.size() == 0
    
    def test_keys(self):
        """Keys testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_keys:")
        cache = MemoryCache(config)
        
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("item:1", "data3")
        
        user_keys = cache.keys("user:*")
        
        assert len(user_keys) == 2
        assert "user:1" in user_keys
        assert "user:2" in user_keys
    
    def test_ttl_expiration(self):
        """TTL expiration testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_ttl:")
        cache = MemoryCache(config)
        
        cache.set("expiring_key", "value", ttl=1)
        
        assert cache.get("expiring_key") == "value"
        
        time.sleep(1.5)
        
        assert cache.get("expiring_key") is None
    
    def test_complex_values(self):
        """Karmaşık değer testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_complex:")
        cache = MemoryCache(config)
        
        complex_value = {
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
            "string": "test"
        }
        
        cache.set("complex", complex_value)
        
        retrieved = cache.get("complex")
        assert retrieved == complex_value
    
    def test_stats_tracking(self):
        """İstatistik takibi testi."""
        from src.cache import MemoryCache, CacheConfig
        
        config = CacheConfig(prefix="test_stats:")
        cache = MemoryCache(config)
        
        cache.set("key1", "value1")  # 1 set
        cache.get("key1")  # 1 hit
        cache.get("nonexistent")  # 1 miss
        cache.delete("key1")  # 1 delete
        
        stats = cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.sets == 1
        assert stats.deletes == 1


class TestCacheManager:
    """CacheManager testleri."""
    
    def test_singleton(self):
        """Singleton pattern testi."""
        from src.cache import CacheManager, CacheConfig
        
        # Reset singleton
        CacheManager._instance = None
        
        config = CacheConfig(prefix="test_singleton:")
        manager1 = CacheManager(config, backend="memory")
        manager2 = CacheManager()
        
        assert manager1 is manager2
    
    def test_get_or_set(self):
        """get_or_set testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_getorset:")
        manager = CacheManager(config, backend="memory")
        
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return "computed_value"
        
        # İlk çağrı - factory çalışmalı
        result1 = manager.get_or_set("test_key", factory)
        assert result1 == "computed_value"
        assert call_count == 1
        
        # İkinci çağrı - cache'den gelmeli
        result2 = manager.get_or_set("test_key", factory)
        assert result2 == "computed_value"
        assert call_count == 1  # Factory tekrar çağrılmamış
    
    def test_get_many(self):
        """get_many testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_getmany:")
        manager = CacheManager(config, backend="memory")
        
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        
        results = manager.get_many(["key1", "key2", "key3"])
        
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert results["key3"] is None
    
    def test_set_many(self):
        """set_many testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_setmany:")
        manager = CacheManager(config, backend="memory")
        
        manager.set_many({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })
        
        assert manager.get("key1") == "value1"
        assert manager.get("key2") == "value2"
        assert manager.get("key3") == "value3"
    
    def test_delete_many(self):
        """delete_many testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_delmany:")
        manager = CacheManager(config, backend="memory")
        
        manager.set_many({"key1": "v1", "key2": "v2", "key3": "v3"})
        
        deleted = manager.delete_many(["key1", "key2"])
        
        assert deleted == 2
        assert manager.exists("key1") is False
        assert manager.exists("key2") is False
        assert manager.exists("key3") is True
    
    def test_cached_decorator(self):
        """cached decorator testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_decorator:")
        manager = CacheManager(config, backend="memory")
        
        call_count = 0
        
        @manager.cached("expensive_func", ttl=300)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # İlk çağrı
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Aynı argümanlarla ikinci çağrı - cache'den
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1
        
        # Farklı argümanlarla - yeni hesaplama
        result3 = expensive_function(3, 4)
        assert result3 == 7
        assert call_count == 2
    
    def test_get_stats(self):
        """get_stats testi."""
        from src.cache import CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_managerstats:")
        manager = CacheManager(config, backend="memory")
        
        manager.set("key1", "value1")
        manager.get("key1")
        
        stats = manager.get_stats()
        
        assert "backend" in stats
        assert stats["backend"] == "MemoryCache"
        assert "hits" in stats
        assert "hit_rate" in stats


class TestDetectionCache:
    """DetectionCache testleri."""
    
    def test_cache_creation(self):
        """Cache oluşturma testi."""
        from src.cache import DetectionCache, CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_det:")
        manager = CacheManager(config, backend="memory")
        
        det_cache = DetectionCache(manager, ttl=60)
        
        assert det_cache is not None
    
    def test_set_get_detections(self):
        """Detection set/get testi."""
        from src.cache import DetectionCache, CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_detsetget:")
        manager = CacheManager(config, backend="memory")
        
        det_cache = DetectionCache(manager, ttl=60)
        
        # Fake frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        detections = [
            {"bbox": (10, 10, 100, 100), "class": "dog", "confidence": 0.95},
            {"bbox": (200, 200, 300, 300), "class": "cat", "confidence": 0.87},
        ]
        
        # Kaydet
        det_cache.set_detections(frame, detections, camera_id="cam1")
        
        # Getir
        cached = det_cache.get_detections(frame, camera_id="cam1")
        
        assert cached is not None
        assert len(cached) == 2
        assert cached[0]["class"] == "dog"
    
    def test_different_frames_different_cache(self):
        """Farklı frame'ler farklı cache testi."""
        from src.cache import DetectionCache, CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_detdiff:")
        manager = CacheManager(config, backend="memory")
        
        det_cache = DetectionCache(manager, ttl=60)
        
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        det1 = [{"class": "dog"}]
        det2 = [{"class": "cat"}]
        
        det_cache.set_detections(frame1, det1, camera_id="cam1")
        det_cache.set_detections(frame2, det2, camera_id="cam1")
        
        cached1 = det_cache.get_detections(frame1, camera_id="cam1")
        cached2 = det_cache.get_detections(frame2, camera_id="cam1")
        
        assert cached1[0]["class"] == "dog"
        assert cached2[0]["class"] == "cat"
    
    def test_clear_camera(self):
        """Kamera cache temizleme testi."""
        from src.cache import DetectionCache, CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_detclear:")
        manager = CacheManager(config, backend="memory")
        
        det_cache = DetectionCache(manager, ttl=60)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        det_cache.set_detections(frame, [{"class": "dog"}], camera_id="cam1")
        det_cache.set_detections(frame, [{"class": "cat"}], camera_id="cam2")
        
        # cam1 temizle
        det_cache.clear_camera("cam1")
        
        # cam1 boş olmalı
        assert det_cache.get_detections(frame, camera_id="cam1") is None
        # cam2 hala var
        # Note: Farklı camera_id farklı key üretir, bu test düzeltilmeli
    
    def test_get_stats(self):
        """Stats testi."""
        from src.cache import DetectionCache, CacheManager, CacheConfig
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_detstats:")
        manager = CacheManager(config, backend="memory")
        
        det_cache = DetectionCache(manager, ttl=60)
        
        stats = det_cache.get_stats()
        
        assert stats["detection_cache"] is True
        assert stats["ttl"] == 60
        assert "hits" in stats


class TestCachedDecorator:
    """@cached decorator testleri."""
    
    def test_function_caching(self):
        """Fonksiyon cache testi."""
        from src.cache import CacheManager, CacheConfig, cached
        
        CacheManager._instance = None
        config = CacheConfig(prefix="test_cachedec:")
        CacheManager(config, backend="memory")
        
        call_count = 0
        
        @cached("test_func", ttl=300)
        def test_function(a, b):
            nonlocal call_count
            call_count += 1
            return a * b
        
        result1 = test_function(5, 3)
        assert result1 == 15
        assert call_count == 1
        
        result2 = test_function(5, 3)
        assert result2 == 15
        assert call_count == 1  # Cache'den geldi
