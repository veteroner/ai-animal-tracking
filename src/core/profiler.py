"""
Performance Profiling Modülü.

Bu modül sistem bileşenlerinin performansını ölçer ve analiz eder.
Bottleneck'ları tespit etmek ve optimizasyon fırsatlarını belirlemek için kullanılır.
"""

import time
import functools
import logging
import statistics
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metrik türleri."""
    TIMING = "timing"  # Süre ölçümü
    COUNTER = "counter"  # Sayaç
    GAUGE = "gauge"  # Anlık değer
    HISTOGRAM = "histogram"  # Dağılım


@dataclass
class TimingMetric:
    """Zamanlama metriği."""
    name: str
    durations: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    max_samples: int = 1000
    
    def record(self, duration: float) -> None:
        """Süre kaydı ekle."""
        self.durations.append(duration)
        self.timestamps.append(datetime.now())
        
        # Max sample'a ulaşıldığında eski kayıtları temizle
        if len(self.durations) > self.max_samples:
            self.durations = self.durations[-self.max_samples:]
            self.timestamps = self.timestamps[-self.max_samples:]
    
    @property
    def count(self) -> int:
        """Toplam ölçüm sayısı."""
        return len(self.durations)
    
    @property
    def total(self) -> float:
        """Toplam süre (ms)."""
        return sum(self.durations)
    
    @property
    def mean(self) -> float:
        """Ortalama süre (ms)."""
        if not self.durations:
            return 0.0
        return statistics.mean(self.durations)
    
    @property
    def median(self) -> float:
        """Medyan süre (ms)."""
        if not self.durations:
            return 0.0
        return statistics.median(self.durations)
    
    @property
    def min(self) -> float:
        """Minimum süre (ms)."""
        if not self.durations:
            return 0.0
        return min(self.durations)
    
    @property
    def max(self) -> float:
        """Maximum süre (ms)."""
        if not self.durations:
            return 0.0
        return max(self.durations)
    
    @property
    def std_dev(self) -> float:
        """Standart sapma."""
        if len(self.durations) < 2:
            return 0.0
        return statistics.stdev(self.durations)
    
    def percentile(self, p: float) -> float:
        """Yüzdelik dilim hesapla."""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * p / 100)
        return sorted_durations[min(index, len(sorted_durations) - 1)]
    
    @property
    def p95(self) -> float:
        """95. yüzdelik dilim."""
        return self.percentile(95)
    
    @property
    def p99(self) -> float:
        """99. yüzdelik dilim."""
        return self.percentile(99)
    
    def recent(self, seconds: int = 60) -> "TimingMetric":
        """Son N saniyedeki metrikleri döndür."""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        recent_data = [
            (d, t) for d, t in zip(self.durations, self.timestamps)
            if t >= cutoff
        ]
        
        result = TimingMetric(name=self.name, max_samples=self.max_samples)
        for duration, timestamp in recent_data:
            result.durations.append(duration)
            result.timestamps.append(timestamp)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict formatına dönüştür."""
        return {
            "name": self.name,
            "count": self.count,
            "total_ms": round(self.total, 3),
            "mean_ms": round(self.mean, 3),
            "median_ms": round(self.median, 3),
            "min_ms": round(self.min, 3),
            "max_ms": round(self.max, 3),
            "std_dev_ms": round(self.std_dev, 3),
            "p95_ms": round(self.p95, 3),
            "p99_ms": round(self.p99, 3),
        }


@dataclass
class CounterMetric:
    """Sayaç metriği."""
    name: str
    value: int = 0
    
    def increment(self, amount: int = 1) -> None:
        """Sayacı artır."""
        self.value += amount
    
    def decrement(self, amount: int = 1) -> None:
        """Sayacı azalt."""
        self.value -= amount
    
    def reset(self) -> None:
        """Sayacı sıfırla."""
        self.value = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict formatına dönüştür."""
        return {
            "name": self.name,
            "value": self.value,
        }


@dataclass
class GaugeMetric:
    """Anlık değer metriği."""
    name: str
    value: float = 0.0
    min_value: float = float('inf')
    max_value: float = float('-inf')
    last_updated: Optional[datetime] = None
    
    def set(self, value: float) -> None:
        """Değeri ayarla."""
        self.value = value
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict formatına dönüştür."""
        return {
            "name": self.name,
            "value": self.value,
            "min": self.min_value if self.min_value != float('inf') else None,
            "max": self.max_value if self.max_value != float('-inf') else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class PerformanceProfiler:
    """
    Performans profiler sınıfı.
    
    Sistem bileşenlerinin performansını ölçer ve analiz eder.
    """
    
    _instance: Optional["PerformanceProfiler"] = None
    
    def __new__(cls) -> "PerformanceProfiler":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Profiler'ı başlat."""
        if self._initialized:
            return
        
        self._timings: Dict[str, TimingMetric] = {}
        self._counters: Dict[str, CounterMetric] = {}
        self._gauges: Dict[str, GaugeMetric] = {}
        self._enabled = True
        self._start_time = datetime.now()
        self._initialized = True
        
        logger.info("PerformanceProfiler başlatıldı")
    
    def enable(self) -> None:
        """Profiler'ı aktif et."""
        self._enabled = True
        logger.info("Profiler aktif edildi")
    
    def disable(self) -> None:
        """Profiler'ı deaktif et."""
        self._enabled = False
        logger.info("Profiler deaktif edildi")
    
    @property
    def is_enabled(self) -> bool:
        """Profiler aktif mi?"""
        return self._enabled
    
    def reset(self) -> None:
        """Tüm metrikleri sıfırla."""
        self._timings.clear()
        self._counters.clear()
        self._gauges.clear()
        self._start_time = datetime.now()
        logger.info("Profiler metrikleri sıfırlandı")
    
    # Timing methods
    
    def record_timing(self, name: str, duration_ms: float) -> None:
        """Zamanlama kaydı ekle."""
        if not self._enabled:
            return
        
        if name not in self._timings:
            self._timings[name] = TimingMetric(name=name)
        
        self._timings[name].record(duration_ms)
    
    @contextmanager
    def timer(self, name: str):
        """
        Context manager ile zamanlama.
        
        Usage:
            with profiler.timer("my_operation"):
                do_something()
        """
        if not self._enabled:
            yield
            return
        
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.record_timing(name, duration_ms)
    
    def timed(self, name: Optional[str] = None) -> Callable:
        """
        Decorator ile zamanlama.
        
        Usage:
            @profiler.timed("my_function")
            def my_function():
                pass
        """
        def decorator(func: Callable) -> Callable:
            metric_name = name or f"{func.__module__}.{func.__qualname__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)
                
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.record_timing(metric_name, duration_ms)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)
                
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self.record_timing(metric_name, duration_ms)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        
        return decorator
    
    def get_timing(self, name: str) -> Optional[TimingMetric]:
        """Belirli bir zamanlama metriğini getir."""
        return self._timings.get(name)
    
    def get_all_timings(self) -> Dict[str, TimingMetric]:
        """Tüm zamanlama metriklerini getir."""
        return self._timings.copy()
    
    # Counter methods
    
    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Sayacı artır."""
        if not self._enabled:
            return
        
        if name not in self._counters:
            self._counters[name] = CounterMetric(name=name)
        
        self._counters[name].increment(amount)
    
    def decrement_counter(self, name: str, amount: int = 1) -> None:
        """Sayacı azalt."""
        if not self._enabled:
            return
        
        if name not in self._counters:
            self._counters[name] = CounterMetric(name=name)
        
        self._counters[name].decrement(amount)
    
    def get_counter(self, name: str) -> int:
        """Sayaç değerini getir."""
        counter = self._counters.get(name)
        return counter.value if counter else 0
    
    def get_all_counters(self) -> Dict[str, CounterMetric]:
        """Tüm sayaçları getir."""
        return self._counters.copy()
    
    # Gauge methods
    
    def set_gauge(self, name: str, value: float) -> None:
        """Gauge değerini ayarla."""
        if not self._enabled:
            return
        
        if name not in self._gauges:
            self._gauges[name] = GaugeMetric(name=name)
        
        self._gauges[name].set(value)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Gauge değerini getir."""
        gauge = self._gauges.get(name)
        return gauge.value if gauge else None
    
    def get_all_gauges(self) -> Dict[str, GaugeMetric]:
        """Tüm gauge'ları getir."""
        return self._gauges.copy()
    
    # Analysis methods
    
    def get_slowest_operations(self, n: int = 10) -> List[Dict[str, Any]]:
        """En yavaş N operasyonu getir (ortalama süreye göre)."""
        operations = [
            {
                "name": timing.name,
                "mean_ms": timing.mean,
                "count": timing.count,
                "p95_ms": timing.p95,
                "total_ms": timing.total,
            }
            for timing in self._timings.values()
            if timing.count > 0
        ]
        
        return sorted(operations, key=lambda x: x["mean_ms"], reverse=True)[:n]
    
    def get_most_called_operations(self, n: int = 10) -> List[Dict[str, Any]]:
        """En çok çağrılan N operasyonu getir."""
        operations = [
            {
                "name": timing.name,
                "count": timing.count,
                "mean_ms": timing.mean,
                "total_ms": timing.total,
            }
            for timing in self._timings.values()
        ]
        
        return sorted(operations, key=lambda x: x["count"], reverse=True)[:n]
    
    def get_highest_total_time_operations(self, n: int = 10) -> List[Dict[str, Any]]:
        """En fazla toplam süre harcayan N operasyonu getir."""
        operations = [
            {
                "name": timing.name,
                "total_ms": timing.total,
                "count": timing.count,
                "mean_ms": timing.mean,
            }
            for timing in self._timings.values()
            if timing.count > 0
        ]
        
        return sorted(operations, key=lambda x: x["total_ms"], reverse=True)[:n]
    
    def detect_bottlenecks(self, threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """
        Potansiyel bottleneck'ları tespit et.
        
        Ortalama süresi threshold'un üzerinde olan operasyonları döndürür.
        """
        bottlenecks = []
        
        for timing in self._timings.values():
            if timing.mean > threshold_ms:
                bottlenecks.append({
                    "name": timing.name,
                    "mean_ms": timing.mean,
                    "p95_ms": timing.p95,
                    "max_ms": timing.max,
                    "count": timing.count,
                    "severity": "high" if timing.mean > threshold_ms * 2 else "medium",
                })
        
        return sorted(bottlenecks, key=lambda x: x["mean_ms"], reverse=True)
    
    def get_summary(self) -> Dict[str, Any]:
        """Genel performans özeti getir."""
        uptime = datetime.now() - self._start_time
        
        total_timing_samples = sum(t.count for t in self._timings.values())
        total_time_tracked = sum(t.total for t in self._timings.values())
        
        return {
            "enabled": self._enabled,
            "uptime_seconds": uptime.total_seconds(),
            "timing_metrics_count": len(self._timings),
            "counter_metrics_count": len(self._counters),
            "gauge_metrics_count": len(self._gauges),
            "total_timing_samples": total_timing_samples,
            "total_time_tracked_ms": round(total_time_tracked, 3),
            "slowest_operations": self.get_slowest_operations(5),
            "most_called_operations": self.get_most_called_operations(5),
            "bottlenecks": self.detect_bottlenecks(),
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Detaylı performans raporu getir."""
        return {
            "summary": self.get_summary(),
            "timings": {
                name: timing.to_dict()
                for name, timing in self._timings.items()
            },
            "counters": {
                name: counter.to_dict()
                for name, counter in self._counters.items()
            },
            "gauges": {
                name: gauge.to_dict()
                for name, gauge in self._gauges.items()
            },
        }
    
    def print_report(self) -> None:
        """Konsola performans raporu yazdır."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("PERFORMANS RAPORU")
        print("=" * 60)
        
        print(f"\nÇalışma Süresi: {summary['uptime_seconds']:.1f} saniye")
        print(f"Toplam Timing Örnekleri: {summary['total_timing_samples']}")
        print(f"Toplam İzlenen Süre: {summary['total_time_tracked_ms']:.1f} ms")
        
        print("\n--- En Yavaş Operasyonlar ---")
        for i, op in enumerate(summary['slowest_operations'], 1):
            print(f"{i}. {op['name']}: {op['mean_ms']:.2f}ms (ort.), {op['count']} çağrı")
        
        print("\n--- En Çok Çağrılan Operasyonlar ---")
        for i, op in enumerate(summary['most_called_operations'], 1):
            print(f"{i}. {op['name']}: {op['count']} çağrı, {op['mean_ms']:.2f}ms (ort.)")
        
        if summary['bottlenecks']:
            print("\n--- ⚠️ Potansiyel Bottleneck'lar ---")
            for bottleneck in summary['bottlenecks']:
                severity_icon = "🔴" if bottleneck['severity'] == 'high' else "🟡"
                print(f"{severity_icon} {bottleneck['name']}: {bottleneck['mean_ms']:.2f}ms (ort.)")
        
        print("\n" + "=" * 60)


class CPUProfiler:
    """
    cProfile tabanlı CPU profiler.
    
    Fonksiyonların CPU kullanımını detaylı analiz eder.
    """
    
    def __init__(self):
        """CPU Profiler'ı başlat."""
        self._profiler: Optional[cProfile.Profile] = None
        self._is_running = False
    
    def start(self) -> None:
        """Profiling'i başlat."""
        if self._is_running:
            logger.warning("CPU Profiler zaten çalışıyor")
            return
        
        self._profiler = cProfile.Profile()
        self._profiler.enable()
        self._is_running = True
        logger.info("CPU Profiler başlatıldı")
    
    def stop(self) -> None:
        """Profiling'i durdur."""
        if not self._is_running or not self._profiler:
            logger.warning("CPU Profiler çalışmıyor")
            return
        
        self._profiler.disable()
        self._is_running = False
        logger.info("CPU Profiler durduruldu")
    
    @property
    def is_running(self) -> bool:
        """Profiler çalışıyor mu?"""
        return self._is_running
    
    def get_stats(
        self,
        sort_by: str = "cumulative",
        limit: int = 20
    ) -> str:
        """
        Profiling istatistiklerini getir.
        
        Args:
            sort_by: Sıralama kriteri (cumulative, time, calls, name)
            limit: Gösterilecek fonksiyon sayısı
        
        Returns:
            Formatlanmış istatistik string'i
        """
        if not self._profiler:
            return "Profiler henüz çalıştırılmadı"
        
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats(sort_by)
        stats.print_stats(limit)
        
        return stream.getvalue()
    
    def get_callers(self, function_name: str) -> str:
        """Belirli bir fonksiyonu çağıran fonksiyonları getir."""
        if not self._profiler:
            return "Profiler henüz çalıştırılmadı"
        
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.strip_dirs()
        stats.print_callers(function_name)
        
        return stream.getvalue()
    
    def get_callees(self, function_name: str) -> str:
        """Belirli bir fonksiyonun çağırdığı fonksiyonları getir."""
        if not self._profiler:
            return "Profiler henüz çalıştırılmadı"
        
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.strip_dirs()
        stats.print_callees(function_name)
        
        return stream.getvalue()
    
    @contextmanager
    def profile(self, sort_by: str = "cumulative", limit: int = 20):
        """
        Context manager ile profiling.
        
        Usage:
            with cpu_profiler.profile() as stats:
                do_something()
            print(stats)
        """
        self.start()
        result = {"stats": ""}
        try:
            yield result
        finally:
            self.stop()
            result["stats"] = self.get_stats(sort_by, limit)
    
    def save_stats(self, filename: str) -> None:
        """İstatistikleri dosyaya kaydet."""
        if not self._profiler:
            logger.warning("Profiler henüz çalıştırılmadı")
            return
        
        self._profiler.dump_stats(filename)
        logger.info(f"CPU profiling istatistikleri kaydedildi: {filename}")


class MemoryProfiler:
    """
    Bellek kullanımı profiler'ı.
    
    Not: tracemalloc yerine basit memory tracking kullanır.
    """
    
    def __init__(self):
        """Memory Profiler'ı başlat."""
        self._snapshots: List[Dict[str, Any]] = []
        self._is_running = False
    
    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Bellek kullanımı snapshot'ı al."""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        snapshot = {
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent(),
        }
        
        self._snapshots.append(snapshot)
        return snapshot
    
    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Tüm snapshot'ları getir."""
        return self._snapshots.copy()
    
    def compare_snapshots(
        self,
        index1: int = 0,
        index2: int = -1
    ) -> Dict[str, Any]:
        """İki snapshot'ı karşılaştır."""
        if len(self._snapshots) < 2:
            return {"error": "En az 2 snapshot gerekli"}
        
        snap1 = self._snapshots[index1]
        snap2 = self._snapshots[index2]
        
        return {
            "from": snap1["label"] or f"Snapshot {index1}",
            "to": snap2["label"] or f"Snapshot {index2}",
            "rss_diff_mb": snap2["rss_mb"] - snap1["rss_mb"],
            "vms_diff_mb": snap2["vms_mb"] - snap1["vms_mb"],
            "percent_diff": snap2["percent"] - snap1["percent"],
        }
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Mevcut bellek kullanımını getir."""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "total_mb": psutil.virtual_memory().total / (1024 * 1024),
        }
    
    def clear_snapshots(self) -> None:
        """Snapshot'ları temizle."""
        self._snapshots.clear()


# Global profiler instance
profiler = PerformanceProfiler()
cpu_profiler = CPUProfiler()
memory_profiler = MemoryProfiler()


# Convenience decorators
def timed(name: Optional[str] = None) -> Callable:
    """
    Fonksiyon zamanlama decorator'ı.
    
    Usage:
        @timed("my_function")
        def my_function():
            pass
    """
    return profiler.timed(name)


def count_calls(counter_name: str) -> Callable:
    """
    Fonksiyon çağrı sayısı sayacı decorator'ı.
    
    Usage:
        @count_calls("api_requests")
        def handle_request():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler.increment_counter(counter_name)
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            profiler.increment_counter(counter_name)
            return await func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
