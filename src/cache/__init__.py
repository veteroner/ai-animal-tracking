"""
Redis Cache Modülü.

Bu modül detection sonuçları ve diğer verilerin önbelleklenmesi için
Redis tabanlı cache sistemi sağlar.
"""

import json
import hashlib
import logging
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache konfigürasyonu."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    default_ttl: int = 3600  # 1 saat
    max_connections: int = 10
    socket_timeout: float = 5.0
    retry_on_timeout: bool = True
    prefix: str = "animal_tracker:"
    serializer: str = "json"  # json veya pickle


@dataclass
class CacheStats:
    """Cache istatistikleri."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Hit oranı."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict formatına dönüştür."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 4),
            "total_operations": self.hits + self.misses + self.sets + self.deletes,
        }


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Değer getir."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Değer kaydet."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Değer sil."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Key var mı kontrol et."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        pass
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """Key listesi getir."""
        pass


class MemoryCache(CacheBackend):
    """
    In-memory cache backend.
    
    Redis olmadan test ve geliştirme için kullanılabilir.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Memory cache başlat."""
        self.config = config or CacheConfig()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.stats = CacheStats()
        
        logger.info("MemoryCache başlatıldı")
    
    def _make_key(self, key: str) -> str:
        """Prefixli key oluştur."""
        return f"{self.config.prefix}{key}"
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Item expired mı kontrol et."""
        if "expires_at" not in item:
            return False
        return datetime.now() > item["expires_at"]
    
    def get(self, key: str) -> Optional[Any]:
        """Değer getir."""
        full_key = self._make_key(key)
        
        with self._lock:
            if full_key in self._cache:
                item = self._cache[full_key]
                
                if self._is_expired(item):
                    del self._cache[full_key]
                    self.stats.misses += 1
                    return None
                
                self.stats.hits += 1
                return item["value"]
            
            self.stats.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Değer kaydet."""
        full_key = self._make_key(key)
        ttl = ttl or self.config.default_ttl
        
        with self._lock:
            self._cache[full_key] = {
                "value": value,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None,
            }
            self.stats.sets += 1
            return True
    
    def delete(self, key: str) -> bool:
        """Değer sil."""
        full_key = self._make_key(key)
        
        with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                self.stats.deletes += 1
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Key var mı kontrol et."""
        full_key = self._make_key(key)
        
        with self._lock:
            if full_key in self._cache:
                if self._is_expired(self._cache[full_key]):
                    del self._cache[full_key]
                    return False
                return True
            return False
    
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        with self._lock:
            prefix = self.config.prefix
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            return True
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Key listesi getir."""
        import fnmatch
        
        with self._lock:
            full_pattern = self._make_key(pattern)
            matching_keys = []
            
            for key in self._cache:
                if fnmatch.fnmatch(key, full_pattern):
                    # Prefix'i çıkar
                    short_key = key[len(self.config.prefix):]
                    matching_keys.append(short_key)
            
            return matching_keys
    
    def get_stats(self) -> CacheStats:
        """İstatistikleri getir."""
        return self.stats
    
    def size(self) -> int:
        """Cache boyutu."""
        with self._lock:
            return len([k for k in self._cache if k.startswith(self.config.prefix)])


class RedisCache(CacheBackend):
    """
    Redis cache backend.
    
    Production ortamı için Redis tabanlı cache.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Redis cache başlat."""
        self.config = config or CacheConfig()
        self._client = None
        self._pool = None
        self.stats = CacheStats()
        self._connected = False
        
        self._connect()
    
    def _connect(self):
        """Redis'e bağlan."""
        try:
            import redis  # type: ignore[import-not-found]
            
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
            )
            
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Bağlantı testi
            self._client.ping()
            self._connected = True
            
            logger.info(f"Redis'e bağlandı: {self.config.host}:{self.config.port}")
            
        except ImportError:
            logger.warning("redis paketi yüklü değil. 'pip install redis' ile yükleyin.")
            self._connected = False
        except Exception as e:
            logger.warning(f"Redis bağlantı hatası: {e}")
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Bağlantı durumu."""
        return self._connected
    
    def _make_key(self, key: str) -> str:
        """Prefixli key oluştur."""
        return f"{self.config.prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Değeri serialize et."""
        if self.config.serializer == "pickle":
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')
    
    def _deserialize(self, data: bytes) -> Any:
        """Değeri deserialize et."""
        if self.config.serializer == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))
    
    def get(self, key: str) -> Optional[Any]:
        """Değer getir."""
        if not self._connected:
            self.stats.errors += 1
            return None
        
        try:
            full_key = self._make_key(key)
            data = self._client.get(full_key)
            
            if data is None:
                self.stats.misses += 1
                return None
            
            self.stats.hits += 1
            return self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Redis get hatası: {e}")
            self.stats.errors += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Değer kaydet."""
        if not self._connected:
            self.stats.errors += 1
            return False
        
        try:
            full_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl
            
            if ttl > 0:
                self._client.setex(full_key, ttl, data)
            else:
                self._client.set(full_key, data)
            
            self.stats.sets += 1
            return True
            
        except Exception as e:
            logger.error(f"Redis set hatası: {e}")
            self.stats.errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Değer sil."""
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            result = self._client.delete(full_key)
            
            if result:
                self.stats.deletes += 1
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis delete hatası: {e}")
            self.stats.errors += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Key var mı kontrol et."""
        if not self._connected:
            return False
        
        try:
            full_key = self._make_key(key)
            return bool(self._client.exists(full_key))
        except Exception as e:
            logger.error(f"Redis exists hatası: {e}")
            return False
    
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        if not self._connected:
            return False
        
        try:
            pattern = self._make_key("*")
            keys = self._client.keys(pattern)
            
            if keys:
                self._client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis clear hatası: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Key listesi getir."""
        if not self._connected:
            return []
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self._client.keys(full_pattern)
            
            # Prefix'i çıkar
            prefix_len = len(self.config.prefix)
            return [k.decode('utf-8')[prefix_len:] for k in keys]
            
        except Exception as e:
            logger.error(f"Redis keys hatası: {e}")
            return []
    
    def get_stats(self) -> CacheStats:
        """İstatistikleri getir."""
        return self.stats
    
    def info(self) -> Dict[str, Any]:
        """Redis server bilgileri."""
        if not self._connected:
            return {"connected": False}
        
        try:
            info = self._client.info()
            return {
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_connections_received": info.get("total_connections_received"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}


class CacheManager:
    """
    Cache yönetim sınıfı.
    
    Farklı cache backend'lerini yönetir ve cache decorator'ları sağlar.
    """
    
    _instance: Optional["CacheManager"] = None
    
    def __new__(cls, *args, **kwargs) -> "CacheManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        backend: str = "auto"  # auto, redis, memory
    ):
        """
        Cache manager başlat.
        
        Args:
            config: Cache konfigürasyonu
            backend: Backend tipi (auto, redis, memory)
        """
        if self._initialized:
            return
        
        self.config = config or CacheConfig()
        self._backend: Optional[CacheBackend] = None
        
        if backend == "auto":
            # Redis'i dene, yoksa memory kullan
            redis_cache = RedisCache(self.config)
            if redis_cache.is_connected:
                self._backend = redis_cache
                logger.info("Redis backend aktif")
            else:
                self._backend = MemoryCache(self.config)
                logger.info("Memory backend aktif (Redis bağlantısı yok)")
        elif backend == "redis":
            self._backend = RedisCache(self.config)
        else:
            self._backend = MemoryCache(self.config)
        
        self._initialized = True
    
    @property
    def backend(self) -> CacheBackend:
        """Aktif backend."""
        return self._backend
    
    def get(self, key: str) -> Optional[Any]:
        """Değer getir."""
        return self._backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Değer kaydet."""
        return self._backend.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Değer sil."""
        return self._backend.delete(key)
    
    def exists(self, key: str) -> bool:
        """Key var mı kontrol et."""
        return self._backend.exists(key)
    
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        return self._backend.clear()
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Key listesi getir."""
        return self._backend.keys(pattern)
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Değer varsa getir, yoksa factory ile oluştur ve kaydet.
        
        Args:
            key: Cache key
            factory: Değer oluşturucu fonksiyon
            ttl: Time-to-live (saniye)
        
        Returns:
            Cache'deki veya yeni oluşturulan değer
        """
        value = self.get(key)
        
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Birden fazla key için değerleri getir."""
        return {key: self.get(key) for key in keys}
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Birden fazla key-value kaydet."""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success
    
    def delete_many(self, keys: List[str]) -> int:
        """Birden fazla key sil."""
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        stats = self._backend.get_stats()
        return {
            "backend": type(self._backend).__name__,
            **stats.to_dict(),
        }
    
    def cached(
        self,
        key_prefix: str = "",
        ttl: Optional[int] = None,
        key_builder: Optional[Callable[..., str]] = None
    ) -> Callable:
        """
        Cache decorator.
        
        Usage:
            @cache_manager.cached("my_func", ttl=300)
            def my_function(arg1, arg2):
                return expensive_computation(arg1, arg2)
        
        Args:
            key_prefix: Cache key prefix
            ttl: Time-to-live (saniye)
            key_builder: Özel key oluşturucu fonksiyon
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Cache key oluştur
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Default key: prefix:func_name:args_hash
                    args_str = f"{args}:{sorted(kwargs.items())}"
                    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                    cache_key = f"{key_prefix or func.__name__}:{args_hash}"
                
                # Cache'den getir
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Hesapla ve kaydet
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            # Async desteği
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    args_str = f"{args}:{sorted(kwargs.items())}"
                    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                    cache_key = f"{key_prefix or func.__name__}:{args_hash}"
                
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = await func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        
        return decorator


class DetectionCache:
    """
    Detection sonuçları için özelleştirilmiş cache.
    
    Frame hash'ine göre detection sonuçlarını önbelleğe alır.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None, ttl: int = 60):
        """
        Detection cache başlat.
        
        Args:
            cache_manager: Cache manager instance
            ttl: Cache süresi (saniye)
        """
        self.cache = cache_manager or CacheManager()
        self.ttl = ttl
        self._key_prefix = "detection:"
    
    def _frame_hash(self, frame) -> str:
        """Frame için hash oluştur."""
        import numpy as np
        
        if frame is None:
            return "none"
        
        # Boyutu küçült ve hash al (performans için)
        small = frame[::10, ::10] if len(frame.shape) >= 2 else frame
        return hashlib.md5(small.tobytes()).hexdigest()
    
    def get_detections(self, frame, camera_id: str = "default") -> Optional[List[Dict]]:
        """
        Frame için cache'deki detection'ları getir.
        
        Args:
            frame: Video frame
            camera_id: Kamera ID
        
        Returns:
            Detection listesi veya None
        """
        frame_hash = self._frame_hash(frame)
        key = f"{self._key_prefix}{camera_id}:{frame_hash}"
        return self.cache.get(key)
    
    def set_detections(
        self,
        frame,
        detections: List[Dict],
        camera_id: str = "default"
    ) -> bool:
        """
        Frame için detection'ları cache'e kaydet.
        
        Args:
            frame: Video frame
            detections: Detection listesi
            camera_id: Kamera ID
        
        Returns:
            Başarılı mı?
        """
        frame_hash = self._frame_hash(frame)
        key = f"{self._key_prefix}{camera_id}:{frame_hash}"
        return self.cache.set(key, detections, self.ttl)
    
    def clear_camera(self, camera_id: str) -> int:
        """Belirli kamera için cache'i temizle."""
        keys = self.cache.keys(f"{self._key_prefix}{camera_id}:*")
        return self.cache.delete_many(keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        return {
            "detection_cache": True,
            "ttl": self.ttl,
            **self.cache.get_stats(),
        }


# Global instances
cache_manager = CacheManager()
detection_cache = DetectionCache(cache_manager)


# Convenience decorator
def cached(key_prefix: str = "", ttl: Optional[int] = None):
    """
    Cache decorator.
    
    Usage:
        @cached("expensive_operation", ttl=300)
        def my_function(arg1, arg2):
            return expensive_computation(arg1, arg2)
    """
    return cache_manager.cached(key_prefix, ttl)
