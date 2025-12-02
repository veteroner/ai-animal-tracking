"""
Performance Profiler unit testleri.
"""

import pytest
import time
from datetime import datetime


class TestTimingMetric:
    """TimingMetric sınıfı testleri."""
    
    def test_timing_creation(self):
        """TimingMetric oluşturma testi."""
        from src.core.profiler import TimingMetric
        
        metric = TimingMetric(name="test_metric")
        
        assert metric.name == "test_metric"
        assert metric.count == 0
        assert metric.total == 0.0
    
    def test_record_timing(self):
        """Timing kaydı testi."""
        from src.core.profiler import TimingMetric
        
        metric = TimingMetric(name="test")
        metric.record(10.0)
        metric.record(20.0)
        metric.record(30.0)
        
        assert metric.count == 3
        assert metric.total == 60.0
        assert metric.mean == 20.0
        assert metric.min == 10.0
        assert metric.max == 30.0
    
    def test_percentile(self):
        """Percentile hesaplama testi."""
        from src.core.profiler import TimingMetric
        
        metric = TimingMetric(name="test")
        for i in range(1, 101):
            metric.record(float(i))
        
        assert metric.p95 >= 95.0
        assert metric.p99 >= 99.0
    
    def test_to_dict(self):
        """Dict dönüşüm testi."""
        from src.core.profiler import TimingMetric
        
        metric = TimingMetric(name="test")
        metric.record(50.0)
        
        data = metric.to_dict()
        
        assert data["name"] == "test"
        assert data["count"] == 1
        assert "mean_ms" in data
        assert "p95_ms" in data


class TestCounterMetric:
    """CounterMetric sınıfı testleri."""
    
    def test_counter_creation(self):
        """Counter oluşturma testi."""
        from src.core.profiler import CounterMetric
        
        counter = CounterMetric(name="test_counter")
        
        assert counter.name == "test_counter"
        assert counter.value == 0
    
    def test_increment(self):
        """Increment testi."""
        from src.core.profiler import CounterMetric
        
        counter = CounterMetric(name="test")
        counter.increment()
        counter.increment(5)
        
        assert counter.value == 6
    
    def test_decrement(self):
        """Decrement testi."""
        from src.core.profiler import CounterMetric
        
        counter = CounterMetric(name="test")
        counter.value = 10
        counter.decrement(3)
        
        assert counter.value == 7
    
    def test_reset(self):
        """Reset testi."""
        from src.core.profiler import CounterMetric
        
        counter = CounterMetric(name="test")
        counter.value = 100
        counter.reset()
        
        assert counter.value == 0


class TestGaugeMetric:
    """GaugeMetric sınıfı testleri."""
    
    def test_gauge_creation(self):
        """Gauge oluşturma testi."""
        from src.core.profiler import GaugeMetric
        
        gauge = GaugeMetric(name="test_gauge")
        
        assert gauge.name == "test_gauge"
        assert gauge.value == 0.0
    
    def test_set_value(self):
        """Değer ayarlama testi."""
        from src.core.profiler import GaugeMetric
        
        gauge = GaugeMetric(name="test")
        gauge.set(50.0)
        gauge.set(30.0)
        gauge.set(70.0)
        
        assert gauge.value == 70.0
        assert gauge.min_value == 30.0
        assert gauge.max_value == 70.0
    
    def test_to_dict(self):
        """Dict dönüşüm testi."""
        from src.core.profiler import GaugeMetric
        
        gauge = GaugeMetric(name="test")
        gauge.set(100.0)
        
        data = gauge.to_dict()
        
        assert data["name"] == "test"
        assert data["value"] == 100.0
        assert data["last_updated"] is not None


class TestPerformanceProfiler:
    """PerformanceProfiler sınıfı testleri."""
    
    def test_profiler_singleton(self):
        """Singleton pattern testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler1 = PerformanceProfiler()
        profiler2 = PerformanceProfiler()
        
        assert profiler1 is profiler2
    
    def test_profiler_enable_disable(self):
        """Enable/disable testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        
        profiler.enable()
        assert profiler.is_enabled is True
        
        profiler.disable()
        assert profiler.is_enabled is False
        
        # Temizlik
        profiler.enable()
    
    def test_record_timing(self):
        """Timing kaydetme testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        profiler.record_timing("test_operation", 100.0)
        profiler.record_timing("test_operation", 200.0)
        
        timing = profiler.get_timing("test_operation")
        assert timing is not None
        assert timing.count == 2
        assert timing.mean == 150.0
    
    def test_timer_context_manager(self):
        """Timer context manager testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        with profiler.timer("sleep_test"):
            time.sleep(0.01)  # 10ms
        
        timing = profiler.get_timing("sleep_test")
        assert timing is not None
        assert timing.count == 1
        assert timing.mean >= 10.0  # En az 10ms olmalı
    
    def test_timed_decorator(self):
        """Timed decorator testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        @profiler.timed("decorated_function")
        def test_func():
            time.sleep(0.01)
            return 42
        
        result = test_func()
        
        assert result == 42
        timing = profiler.get_timing("decorated_function")
        assert timing is not None
        assert timing.count == 1
    
    def test_counter_operations(self):
        """Counter işlemleri testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        profiler.increment_counter("api_calls")
        profiler.increment_counter("api_calls")
        profiler.increment_counter("api_calls", 3)
        
        assert profiler.get_counter("api_calls") == 5
    
    def test_gauge_operations(self):
        """Gauge işlemleri testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        profiler.set_gauge("memory_usage", 512.5)
        
        assert profiler.get_gauge("memory_usage") == 512.5
    
    def test_get_summary(self):
        """Summary raporu testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        profiler.record_timing("op1", 50.0)
        profiler.record_timing("op2", 100.0)
        profiler.increment_counter("counter1")
        profiler.set_gauge("gauge1", 10.0)
        
        summary = profiler.get_summary()
        
        assert summary["enabled"] is True
        assert summary["timing_metrics_count"] == 2
        assert summary["counter_metrics_count"] == 1
        assert summary["gauge_metrics_count"] == 1
    
    def test_detect_bottlenecks(self):
        """Bottleneck tespiti testi."""
        from src.core.profiler import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        profiler.reset()
        
        # Yavaş operasyon
        profiler.record_timing("slow_op", 200.0)
        profiler.record_timing("slow_op", 250.0)
        
        # Hızlı operasyon
        profiler.record_timing("fast_op", 10.0)
        profiler.record_timing("fast_op", 15.0)
        
        bottlenecks = profiler.detect_bottlenecks(threshold_ms=100)
        
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["name"] == "slow_op"


class TestCPUProfiler:
    """CPUProfiler sınıfı testleri."""
    
    def test_cpu_profiler_start_stop(self):
        """CPU Profiler start/stop testi."""
        from src.core.profiler import CPUProfiler
        
        cpu_profiler = CPUProfiler()
        
        assert cpu_profiler.is_running is False
        
        cpu_profiler.start()
        assert cpu_profiler.is_running is True
        
        cpu_profiler.stop()
        assert cpu_profiler.is_running is False
    
    def test_cpu_profiler_get_stats(self):
        """CPU Profiler stats testi."""
        from src.core.profiler import CPUProfiler
        
        cpu_profiler = CPUProfiler()
        cpu_profiler.start()
        
        # Biraz iş yap
        total = sum(range(1000))
        
        cpu_profiler.stop()
        
        stats = cpu_profiler.get_stats(limit=5)
        assert isinstance(stats, str)
        assert len(stats) > 0
    
    def test_cpu_profiler_context_manager(self):
        """CPU Profiler context manager testi."""
        from src.core.profiler import CPUProfiler
        
        cpu_profiler = CPUProfiler()
        
        with cpu_profiler.profile(limit=5) as result:
            total = sum(range(1000))
        
        assert "stats" in result
        assert len(result["stats"]) > 0


class TestConvenienceDecorators:
    """Convenience decorator testleri."""
    
    def test_timed_decorator(self):
        """@timed decorator testi."""
        from src.core.profiler import timed, profiler
        
        profiler.reset()
        
        @timed("convenience_timed")
        def sample_function():
            return sum(range(100))
        
        result = sample_function()
        
        assert result == 4950
        timing = profiler.get_timing("convenience_timed")
        assert timing is not None
        assert timing.count == 1
    
    def test_count_calls_decorator(self):
        """@count_calls decorator testi."""
        from src.core.profiler import count_calls, profiler
        
        profiler.reset()
        
        @count_calls("sample_calls")
        def sample_function():
            return "called"
        
        sample_function()
        sample_function()
        sample_function()
        
        assert profiler.get_counter("sample_calls") == 3
