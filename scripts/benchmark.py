#!/usr/bin/env python3
"""
Sistem Benchmark Scripti.

Bu script sistemin temel bileşenlerinin performansını ölçer
ve bir benchmark raporu oluşturur.
"""

import sys
import time
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import numpy as np

# Proje root'unu path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.profiler import (
    profiler,
    cpu_profiler,
    memory_profiler,
    timed
)


class BenchmarkSuite:
    """Benchmark test suite."""
    
    def __init__(self):
        """Benchmark suite başlat."""
        self.results: Dict[str, Any] = {}
        self.start_time: datetime = datetime.now()
    
    def run_all(self) -> Dict[str, Any]:
        """Tüm benchmark'ları çalıştır."""
        print("\n" + "=" * 60)
        print("🚀 AI HAYVAN TAKİP SİSTEMİ - BENCHMARK")
        print("=" * 60)
        
        memory_profiler.take_snapshot("benchmark_start")
        
        # Detection benchmarks
        self._benchmark_detection_models()
        
        # Tracking benchmarks
        self._benchmark_tracking()
        
        # Database benchmarks
        self._benchmark_database()
        
        # Pipeline benchmarks
        self._benchmark_pipeline()
        
        # Export benchmarks
        self._benchmark_export()
        
        # Memory snapshot
        memory_profiler.take_snapshot("benchmark_end")
        
        # Final report
        return self._generate_report()
    
    def _benchmark_detection_models(self):
        """Detection model benchmark'ları."""
        print("\n📸 Detection Model Benchmark...")
        
        try:
            from src.detection import Detection, DetectionResult
            
            # Detection oluşturma benchmark
            iterations = 10000
            start = time.perf_counter()
            
            for i in range(iterations):
                detection = Detection(
                    bbox=(0, 0, 100, 100),
                    confidence=0.95,
                    class_id=16,
                    class_name="dog",
                    center=(50, 50),
                    area=10000
                )
            
            duration = (time.perf_counter() - start) * 1000
            per_item = duration / iterations
            
            self.results["detection_creation"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_item_ms": round(per_item, 6),
                "items_per_second": round(1000 / per_item, 0)
            }
            
            print(f"  ✓ Detection oluşturma: {per_item:.4f}ms/item ({iterations} iterasyon)")
            
            # DetectionResult benchmark
            detections = [
                Detection(
                    bbox=(i*10, i*10, i*10+100, i*10+100),
                    confidence=0.9,
                    class_id=16,
                    class_name="dog",
                    center=(i*10+50, i*10+50),
                    area=10000
                )
                for i in range(10)
            ]
            
            iterations = 5000
            start = time.perf_counter()
            
            for i in range(iterations):
                result = DetectionResult(
                    detections=detections,
                    frame_id=i,
                    timestamp=datetime.now(),
                    inference_time=15.0,
                    image_size=(640, 480)
                )
            
            duration = (time.perf_counter() - start) * 1000
            per_item = duration / iterations
            
            self.results["detection_result_creation"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_item_ms": round(per_item, 6),
                "detections_per_result": 10
            }
            
            print(f"  ✓ DetectionResult oluşturma: {per_item:.4f}ms/item")
            
        except Exception as e:
            print(f"  ✗ Detection benchmark hatası: {e}")
            self.results["detection_creation"] = {"error": str(e)}
    
    def _benchmark_tracking(self):
        """Tracking benchmark'ları."""
        print("\n🎯 Tracking Benchmark...")
        
        try:
            from src.tracking import Track, TrackState, ObjectTracker
            
            # Track oluşturma benchmark
            iterations = 10000
            start = time.perf_counter()
            
            for i in range(iterations):
                track = Track(
                    track_id=i,
                    bbox=(0, 0, 100, 100),
                    state=TrackState.TENTATIVE
                )
            
            duration = (time.perf_counter() - start) * 1000
            per_item = duration / iterations
            
            self.results["track_creation"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_item_ms": round(per_item, 6),
            }
            
            print(f"  ✓ Track oluşturma: {per_item:.4f}ms/item")
            
            # ObjectTracker benchmark
            tracker = ObjectTracker()
            
            # Fake detections
            from src.detection import Detection
            
            iterations = 100
            detections_per_frame = 5
            
            fake_detections = [
                Detection(
                    bbox=(i*50, i*50, i*50+100, i*50+100),
                    confidence=0.9,
                    class_id=16,
                    class_name="dog",
                    center=(i*50+50, i*50+50),
                    area=10000
                )
                for i in range(detections_per_frame)
            ]
            
            start = time.perf_counter()
            
            for i in range(iterations):
                # Not: update fonksiyonun varlığını kontrol et
                if hasattr(tracker, 'update'):
                    tracker.update(fake_detections)
            
            duration = (time.perf_counter() - start) * 1000
            per_frame = duration / iterations
            
            self.results["tracker_update"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_frame_ms": round(per_frame, 4),
                "fps_capacity": round(1000 / per_frame, 1) if per_frame > 0 else 0
            }
            
            print(f"  ✓ Tracker update: {per_frame:.2f}ms/frame ({self.results['tracker_update']['fps_capacity']} FPS kapasitesi)")
            
        except Exception as e:
            print(f"  ✗ Tracking benchmark hatası: {e}")
            self.results["track_creation"] = {"error": str(e)}
    
    def _benchmark_database(self):
        """Database benchmark'ları."""
        print("\n💾 Database Benchmark...")
        
        try:
            # In-memory SQLite ile test
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from src.database.models import Base, Animal, Detection as DBDetection
            
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Insert benchmark
            iterations = 1000
            start = time.perf_counter()
            
            for i in range(iterations):
                animal = Animal(
                    animal_id=f"animal_{i}",
                    species="dog",
                    first_seen=datetime.now()
                )
                session.add(animal)
            
            session.commit()
            
            duration = (time.perf_counter() - start) * 1000
            per_item = duration / iterations
            
            self.results["db_insert"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_item_ms": round(per_item, 4),
                "items_per_second": round(1000 / per_item, 0)
            }
            
            print(f"  ✓ DB Insert: {per_item:.4f}ms/item ({self.results['db_insert']['items_per_second']}/s)")
            
            # Query benchmark
            iterations = 500
            start = time.perf_counter()
            
            for i in range(iterations):
                results = session.query(Animal).filter(Animal.species == "dog").limit(10).all()
            
            duration = (time.perf_counter() - start) * 1000
            per_query = duration / iterations
            
            self.results["db_query"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_query_ms": round(per_query, 4),
                "queries_per_second": round(1000 / per_query, 0)
            }
            
            print(f"  ✓ DB Query: {per_query:.4f}ms/query ({self.results['db_query']['queries_per_second']}/s)")
            
            session.close()
            
        except Exception as e:
            print(f"  ✗ Database benchmark hatası: {e}")
            self.results["db_insert"] = {"error": str(e)}
    
    def _benchmark_pipeline(self):
        """Pipeline benchmark'ları."""
        print("\n⚡ Pipeline Benchmark...")
        
        try:
            # Fake frame processing simulation
            iterations = 100
            frame_size = (640, 480, 3)
            
            # NumPy operations benchmark
            start = time.perf_counter()
            
            for i in range(iterations):
                # Fake frame
                frame = np.random.randint(0, 255, frame_size, dtype=np.uint8)
                
                # Resize simulation
                resized = frame[::2, ::2]  # Basit downscale
                
                # Color conversion simulation
                gray = frame.mean(axis=2)
            
            duration = (time.perf_counter() - start) * 1000
            per_frame = duration / iterations
            
            self.results["frame_preprocessing"] = {
                "iterations": iterations,
                "total_ms": round(duration, 3),
                "per_frame_ms": round(per_frame, 2),
                "fps_capacity": round(1000 / per_frame, 1) if per_frame > 0 else 0
            }
            
            print(f"  ✓ Frame preprocessing: {per_frame:.2f}ms/frame ({self.results['frame_preprocessing']['fps_capacity']} FPS)")
            
        except Exception as e:
            print(f"  ✗ Pipeline benchmark hatası: {e}")
            self.results["frame_preprocessing"] = {"error": str(e)}
    
    def _benchmark_export(self):
        """Export benchmark'ları."""
        print("\n📤 Export Benchmark...")
        
        try:
            from src.export.exporters import CSVExporter, JSONExporter
            import tempfile
            import os
            
            # Test data
            test_data = [
                {"id": i, "name": f"item_{i}", "value": i * 1.5, "timestamp": datetime.now().isoformat()}
                for i in range(1000)
            ]
            
            # CSV Export benchmark
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                csv_path = f.name
            
            exporter = CSVExporter(output_dir=os.path.dirname(csv_path))
            
            iterations = 50
            start = time.perf_counter()
            
            for i in range(iterations):
                exporter.export(test_data, filename=f"benchmark_{i}.csv")
            
            duration = (time.perf_counter() - start) * 1000
            per_export = duration / iterations
            
            self.results["csv_export"] = {
                "iterations": iterations,
                "records_per_export": 1000,
                "total_ms": round(duration, 3),
                "per_export_ms": round(per_export, 2),
            }
            
            print(f"  ✓ CSV Export (1000 kayıt): {per_export:.2f}ms/export")
            
            # Cleanup
            import glob
            for f in glob.glob(os.path.join(os.path.dirname(csv_path), "benchmark_*.csv")):
                os.remove(f)
            
            # JSON Export benchmark
            exporter = JSONExporter(output_dir=os.path.dirname(csv_path))
            
            start = time.perf_counter()
            
            for i in range(iterations):
                exporter.export(test_data, filename=f"benchmark_{i}.json")
            
            duration = (time.perf_counter() - start) * 1000
            per_export = duration / iterations
            
            self.results["json_export"] = {
                "iterations": iterations,
                "records_per_export": 1000,
                "total_ms": round(duration, 3),
                "per_export_ms": round(per_export, 2),
            }
            
            print(f"  ✓ JSON Export (1000 kayıt): {per_export:.2f}ms/export")
            
            # Cleanup
            for f in glob.glob(os.path.join(os.path.dirname(csv_path), "benchmark_*.json")):
                os.remove(f)
            
        except Exception as e:
            print(f"  ✗ Export benchmark hatası: {e}")
            self.results["csv_export"] = {"error": str(e)}
    
    def _generate_report(self) -> Dict[str, Any]:
        """Benchmark raporu oluştur."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Memory comparison
        memory_diff = memory_profiler.compare_snapshots(0, -1)
        
        report = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "benchmarks": self.results,
            "memory": {
                "start": memory_profiler.get_snapshots()[0] if memory_profiler.get_snapshots() else None,
                "end": memory_profiler.get_snapshots()[-1] if memory_profiler.get_snapshots() else None,
                "diff": memory_diff
            },
            "profiler_summary": profiler.get_summary()
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 BENCHMARK ÖZETİ")
        print("=" * 60)
        
        print(f"\nToplam Süre: {duration:.2f} saniye")
        
        if "memory" in report and report["memory"]["diff"]:
            print(f"Bellek Değişimi: {report['memory']['diff'].get('rss_diff_mb', 0):.2f} MB")
        
        print("\n--- Performans Sonuçları ---")
        
        for name, result in self.results.items():
            if "error" not in result:
                if "per_item_ms" in result:
                    print(f"  • {name}: {result['per_item_ms']:.4f}ms/item")
                elif "per_frame_ms" in result:
                    print(f"  • {name}: {result['per_frame_ms']:.2f}ms/frame")
                elif "per_export_ms" in result:
                    print(f"  • {name}: {result['per_export_ms']:.2f}ms/export")
        
        print("\n" + "=" * 60)
        
        return report


def main():
    """Ana benchmark fonksiyonu."""
    suite = BenchmarkSuite()
    report = suite.run_all()
    
    # Raporu dosyaya kaydet
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Rapor kaydedildi: {report_file}")
    
    return report


if __name__ == "__main__":
    main()
