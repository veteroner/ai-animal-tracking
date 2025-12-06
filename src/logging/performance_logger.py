"""
Performans Logger

Performans metrikleri ve profiling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import time
import functools
from collections import defaultdict
import statistics


@dataclass
class PerformanceMetric:
    """Performans metriği"""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def finish(self):
        """Metriği bitir"""
        self.end_time = datetime.now()
        delta = self.end_time - self.start_time
        self.duration_ms = delta.total_seconds() * 1000
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "metadata": self.metadata
        }


@dataclass
class PerformanceStats:
    """Performans istatistikleri"""
    name: str
    count: int = 0
    total_ms: float = 0
    min_ms: float = float('inf')
    max_ms: float = 0
    avg_ms: float = 0
    durations: List[float] = field(default_factory=list)
    
    def add_duration(self, duration_ms: float):
        """Süre ekle"""
        self.count += 1
        self.total_ms += duration_ms
        self.min_ms = min(self.min_ms, duration_ms)
        self.max_ms = max(self.max_ms, duration_ms)
        self.avg_ms = self.total_ms / self.count
        self.durations.append(duration_ms)
        
        # Bellek için son 1000 tanesini tut
        if len(self.durations) > 1000:
            self.durations = self.durations[-1000:]
    
    @property
    def median_ms(self) -> float:
        """Median hesapla"""
        if self.durations:
            return statistics.median(self.durations)
        return 0
    
    @property
    def p95_ms(self) -> float:
        """95. persentil"""
        if len(self.durations) >= 20:
            sorted_durations = sorted(self.durations)
            index = int(len(sorted_durations) * 0.95)
            return sorted_durations[index]
        return self.max_ms
    
    @property
    def p99_ms(self) -> float:
        """99. persentil"""
        if len(self.durations) >= 100:
            sorted_durations = sorted(self.durations)
            index = int(len(sorted_durations) * 0.99)
            return sorted_durations[index]
        return self.max_ms
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "count": self.count,
            "total_ms": round(self.total_ms, 2),
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "median_ms": round(self.median_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2)
        }


class PerformanceLogger:
    """Performans logger"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.stats: Dict[str, PerformanceStats] = defaultdict(lambda: PerformanceStats(name=""))
        self.active_metrics: Dict[str, PerformanceMetric] = {}
    
    def start(self, name: str, metadata: Optional[Dict] = None) -> str:
        """Metrik başlat"""
        metric_id = f"{name}_{time.time()}"
        
        metric = PerformanceMetric(
            name=name,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self.active_metrics[metric_id] = metric
        return metric_id
    
    def stop(self, metric_id: str):
        """Metriği durdur"""
        if metric_id not in self.active_metrics:
            return
        
        metric = self.active_metrics.pop(metric_id)
        metric.finish()
        
        # Kaydet
        self.metrics.append(metric)
        
        # İstatistik güncelle
        if metric.name not in self.stats:
            self.stats[metric.name] = PerformanceStats(name=metric.name)
        
        self.stats[metric.name].add_duration(metric.duration_ms)
    
    def measure(self, name: str):
        """Decorator - fonksiyon performansını ölç"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metric_id = self.start(name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.stop(metric_id)
            
            return wrapper
        return decorator
    
    def get_stats(self, name: Optional[str] = None) -> Dict:
        """İstatistikleri al"""
        if name:
            stats = self.stats.get(name)
            return stats.to_dict() if stats else {}
        
        return {
            name: stats.to_dict()
            for name, stats in self.stats.items()
        }
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict]:
        """Son metrikleri al"""
        return [m.to_dict() for m in self.metrics[-limit:]]
    
    def get_slow_operations(self, threshold_ms: float = 1000,
                           limit: int = 50) -> List[Dict]:
        """Yavaş operasyonları listele"""
        slow = [
            m for m in self.metrics
            if m.duration_ms and m.duration_ms >= threshold_ms
        ]
        
        # En yavaştan hızlıya sırala
        slow.sort(key=lambda x: x.duration_ms, reverse=True)
        
        return [m.to_dict() for m in slow[:limit]]
    
    def clear(self):
        """Tüm metrikleri temizle"""
        self.metrics.clear()
        self.stats.clear()
        self.active_metrics.clear()
    
    def summary(self) -> Dict:
        """Özet rapor"""
        if not self.stats:
            return {"message": "Henüz metrik yok"}
        
        total_operations = sum(s.count for s in self.stats.values())
        total_time_s = sum(s.total_ms for s in self.stats.values()) / 1000
        
        # En yavaş operasyonlar
        slowest = sorted(
            self.stats.values(),
            key=lambda s: s.avg_ms,
            reverse=True
        )[:5]
        
        return {
            "total_operations": total_operations,
            "total_time_seconds": round(total_time_s, 2),
            "unique_operations": len(self.stats),
            "slowest_operations": [
                {
                    "name": s.name,
                    "avg_ms": round(s.avg_ms, 2),
                    "count": s.count
                }
                for s in slowest
            ]
        }


# Global instance
_perf_logger: Optional[PerformanceLogger] = None


def get_performance_logger() -> PerformanceLogger:
    """Global performance logger al"""
    global _perf_logger
    if _perf_logger is None:
        _perf_logger = PerformanceLogger()
    return _perf_logger


# Context manager
class Timer:
    """Performans timer context manager"""
    
    def __init__(self, name: str, logger: Optional[PerformanceLogger] = None):
        self.name = name
        self.logger = logger or get_performance_logger()
        self.metric_id = None
    
    def __enter__(self):
        self.metric_id = self.logger.start(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metric_id:
            self.logger.stop(self.metric_id)


# Decorator
def measure_performance(name: Optional[str] = None):
    """Fonksiyon performansını ölç"""
    def decorator(func: Callable):
        metric_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_performance_logger()
            metric_id = logger.start(metric_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                logger.stop(metric_id)
        
        return wrapper
    return decorator
