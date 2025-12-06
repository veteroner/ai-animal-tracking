"""
Önbellek Yöneticisi

In-memory ve Redis tabanlı cache yönetimi.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
import functools
import hashlib
import json
import pickle
from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Önbellek backend temel sınıfı"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Değeri al"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Değeri kaydet"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Değeri sil"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Değer var mı kontrol et"""
        pass
    
    @abstractmethod
    def clear(self):
        """Tüm cache'i temizle"""
        pass


@dataclass
class CacheEntry:
    """Önbellek girişi"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Süre dolmuş mu?"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Yaş (saniye)"""
        return (datetime.now() - self.created_at).total_seconds()


class MemoryCache(CacheBackend):
    """In-memory cache"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # İstatistikler
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Değeri al"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Süre kontrolü
        if entry.is_expired:
            del self.cache[key]
            self.misses += 1
            return None
        
        # İstatistik güncelle
        entry.hit_count += 1
        self.hits += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Değeri kaydet"""
        # Boyut kontrolü - eviction gerekirse
        if key not in self.cache and len(self.cache) >= self.max_size:
            self._evict()
        
        # TTL hesapla
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        elif self.default_ttl:
            expires_at = datetime.now() + timedelta(seconds=self.default_ttl)
        
        # Giriş oluştur
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Değeri sil"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Değer var mı?"""
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        if entry.is_expired:
            del self.cache[key]
            return False
        
        return True
    
    def clear(self):
        """Tümünü temizle"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _evict(self):
        """En az kullanılandan çıkar (LFU)"""
        if not self.cache:
            return
        
        # En az hit alan ve en eski
        min_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].hit_count, -self.cache[k].age_seconds)
        )
        
        del self.cache[min_key]
        self.evictions += 1
    
    def cleanup_expired(self) -> int:
        """Süresi dolmuş kayıtları temizle"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """İstatistikleri al"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate * 100, 2),
            "evictions": self.evictions
        }


class CacheManager:
    """Önbellek yöneticisi"""
    
    def __init__(self, backend: Optional[CacheBackend] = None,
                 namespace: str = "default"):
        self.backend = backend or MemoryCache()
        self.namespace = namespace
    
    def _make_key(self, key: str) -> str:
        """Namespace'li key oluştur"""
        return f"{self.namespace}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Değeri al"""
        full_key = self._make_key(key)
        value = self.backend.get(full_key)
        return value if value is not None else default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Değeri kaydet"""
        full_key = self._make_key(key)
        self.backend.set(full_key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Değeri sil"""
        full_key = self._make_key(key)
        return self.backend.delete(full_key)
    
    def exists(self, key: str) -> bool:
        """Değer var mı?"""
        full_key = self._make_key(key)
        return self.backend.exists(full_key)
    
    def get_or_set(self, key: str, factory: Callable[[], Any],
                   ttl: Optional[int] = None) -> Any:
        """Al, yoksa oluştur ve kaydet"""
        value = self.get(key)
        
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        
        return value
    
    def remember(self, key: str, ttl: int):
        """Decorator - sonucu cache'le"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Cache key oluştur
                cache_key = self._generate_cache_key(key, args, kwargs)
                
                # Cache'den dene
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Hesapla ve kaydet
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def _generate_cache_key(self, base_key: str, args: tuple, 
                           kwargs: dict) -> str:
        """Args ve kwargs'tan cache key oluştur"""
        # Serialize edilebilir yap
        try:
            args_str = json.dumps(args, sort_keys=True)
            kwargs_str = json.dumps(kwargs, sort_keys=True)
        except:
            # JSON serialize edilemiyorsa str kullan
            args_str = str(args)
            kwargs_str = str(kwargs)
        
        # Hash oluştur
        combined = f"{base_key}:{args_str}:{kwargs_str}"
        hash_key = hashlib.md5(combined.encode()).hexdigest()
        
        return f"{base_key}:{hash_key}"
    
    def clear(self):
        """Cache'i temizle"""
        self.backend.clear()
    
    def get_stats(self) -> Dict:
        """İstatistikleri al"""
        if hasattr(self.backend, 'get_stats'):
            return self.backend.get_stats()
        return {}


# Decorator fonksiyonu
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Fonksiyon sonucunu cache'le"""
    def decorator(func: Callable):
        cache = CacheManager()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Cache key
            func_name = func.__name__
            base_key = f"{key_prefix}{func_name}" if key_prefix else func_name
            
            cache_key = cache._generate_cache_key(base_key, args, kwargs)
            
            # Cache'den dene
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Hesapla ve kaydet
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache(namespace: str = "default") -> CacheManager:
    """Global cache instance al"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(namespace=namespace)
    return _cache_instance
