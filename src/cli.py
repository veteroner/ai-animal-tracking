#!/usr/bin/env python3
"""
AI Hayvan Takip Sistemi - CLI Tool.

Bu modül komut satırından sistem kullanımı için CLI araçları sunar.
"""

import sys
import click
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Proje root'unu path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Logging setup
def setup_logging(verbose: bool = False):
    """Logging'i ayarla."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


@click.group()
@click.version_option(version="1.0.0", prog_name="AI Hayvan Takip Sistemi")
@click.option("-v", "--verbose", is_flag=True, help="Detaylı çıktı")
@click.pass_context
def cli(ctx, verbose):
    """
    🐾 AI Hayvan Takip Sistemi CLI
    
    Bu araç ile sistemi komut satırından kontrol edebilirsiniz.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


# ============================================================
# KAMERA KOMUTLARI
# ============================================================

@cli.group()
def camera():
    """📷 Kamera yönetimi komutları."""
    pass


@camera.command("list")
@click.pass_context
def camera_list(ctx):
    """Tüm kameraları listele."""
    try:
        from src.database import SessionLocal
        from src.database.models import Camera
        
        session = SessionLocal()
        cameras = session.query(Camera).all()
        
        if not cameras:
            click.echo("Kayıtlı kamera bulunamadı.")
            return
        
        click.echo("\n📷 Kayıtlı Kameralar:")
        click.echo("-" * 50)
        
        for cam in cameras:
            status_icon = "🟢" if cam.is_active else "🔴"
            click.echo(f"{status_icon} {cam.name} (ID: {cam.id})")
            click.echo(f"   URL: {cam.url}")
            click.echo(f"   Konum: {cam.location or 'Belirtilmemiş'}")
            click.echo()
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@camera.command("add")
@click.option("--name", "-n", required=True, help="Kamera adı")
@click.option("--url", "-u", required=True, help="Kamera URL'i")
@click.option("--location", "-l", help="Kamera konumu")
def camera_add(name, url, location):
    """Yeni kamera ekle."""
    try:
        from src.database import SessionLocal
        from src.database.models import Camera
        
        session = SessionLocal()
        
        camera = Camera(
            name=name,
            url=url,
            location=location,
            is_active=True,
            created_at=datetime.now()
        )
        
        session.add(camera)
        session.commit()
        
        click.echo(f"✅ Kamera eklendi: {name} (ID: {camera.id})")
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@camera.command("test")
@click.argument("camera_id", type=int)
def camera_test(camera_id):
    """Kamera bağlantısını test et."""
    try:
        import cv2
        from src.database import SessionLocal
        from src.database.models import Camera
        
        session = SessionLocal()
        camera = session.query(Camera).filter(Camera.id == camera_id).first()
        
        if not camera:
            click.echo(f"❌ Kamera bulunamadı: ID {camera_id}")
            return
        
        click.echo(f"🔄 Kamera test ediliyor: {camera.name}...")
        
        cap = cv2.VideoCapture(camera.url)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                click.echo(f"✅ Bağlantı başarılı!")
                click.echo(f"   Çözünürlük: {frame.shape[1]}x{frame.shape[0]}")
            else:
                click.echo("⚠️ Bağlantı var ama frame okunamadı")
            cap.release()
        else:
            click.echo("❌ Kameraya bağlanılamadı")
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


# ============================================================
# DETECTION KOMUTLARI
# ============================================================

@cli.group()
def detect():
    """🔍 Detection komutları."""
    pass


@detect.command("image")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--model", "-m", default="yolov8n.pt", help="Model dosyası")
@click.option("--confidence", "-c", default=0.5, type=float, help="Güven eşiği")
@click.option("--output", "-o", help="Çıktı dosyası")
@click.option("--show", is_flag=True, help="Sonucu göster")
def detect_image(image_path, model, confidence, output, show):
    """Görüntüde hayvan tespiti yap."""
    try:
        import cv2
        import numpy as np
        from src.detection import YOLODetector, DetectorConfig
        
        click.echo(f"🔄 Görüntü analiz ediliyor: {image_path}")
        
        # Model yükle
        config = DetectorConfig(
            model_path=model,
            confidence_threshold=confidence
        )
        detector = YOLODetector(config)
        
        # Görüntüyü oku
        image = cv2.imread(image_path)
        if image is None:
            click.echo("❌ Görüntü okunamadı")
            return
        
        # Detection yap
        result = detector.detect(image)
        
        click.echo(f"\n📊 Sonuçlar:")
        click.echo(f"   Toplam tespit: {result.count}")
        click.echo(f"   Hayvan sayısı: {result.animal_count}")
        click.echo(f"   İşlem süresi: {result.inference_time:.2f}ms")
        
        if result.detections:
            click.echo("\n🐾 Tespit edilen hayvanlar:")
            for i, det in enumerate(result.detections, 1):
                if det.is_animal:
                    click.echo(f"   {i}. {det.class_name}: {det.confidence:.1%}")
        
        # Çıktı kaydet
        if output:
            from src.video import FrameAnnotator
            annotator = FrameAnnotator()
            
            annotated = annotator.annotate_detections(
                image,
                [{"bbox": d.bbox, "class_name": d.class_name, "confidence": d.confidence}
                 for d in result.detections]
            )
            
            cv2.imwrite(output, annotated)
            click.echo(f"\n💾 Çıktı kaydedildi: {output}")
        
        # Göster
        if show:
            cv2.imshow("Detection Result", image if not output else annotated)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@detect.command("video")
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--model", "-m", default="yolov8n.pt", help="Model dosyası")
@click.option("--confidence", "-c", default=0.5, type=float, help="Güven eşiği")
@click.option("--output", "-o", help="Çıktı video dosyası")
@click.option("--skip-frames", default=1, type=int, help="Her N frame'de bir işle")
def detect_video(video_path, model, confidence, output, skip_frames):
    """Videoda hayvan tespiti yap."""
    try:
        import cv2
        from src.detection import YOLODetector, DetectorConfig
        from src.video import VideoRecorder, VideoConfig
        
        click.echo(f"🔄 Video analiz ediliyor: {video_path}")
        
        # Video aç
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            click.echo("❌ Video açılamadı")
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        click.echo(f"   Toplam frame: {total_frames}")
        click.echo(f"   FPS: {fps}")
        
        # Detector yükle
        config = DetectorConfig(model_path=model, confidence_threshold=confidence)
        detector = YOLODetector(config)
        
        # Recorder (opsiyonel)
        recorder = None
        if output:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            video_config = VideoConfig(output_dir=str(Path(output).parent))
            recorder = VideoRecorder(video_config)
            recorder.start_recording(filename=Path(output).name, resolution=(width, height))
        
        # İşle
        frame_count = 0
        detection_count = 0
        
        with click.progressbar(length=total_frames, label="İşleniyor") as bar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                if frame_count % skip_frames == 0:
                    result = detector.detect(frame)
                    detection_count += result.animal_count
                    
                    if recorder:
                        detections = [
                            {"bbox": d.bbox, "class_name": d.class_name, "confidence": d.confidence}
                            for d in result.detections
                        ]
                        recorder.write_frame(frame, detections=detections)
                elif recorder:
                    recorder.write_frame(frame, annotate=False)
                
                bar.update(1)
        
        cap.release()
        
        if recorder:
            recorder.stop_recording()
        
        click.echo(f"\n📊 Sonuçlar:")
        click.echo(f"   İşlenen frame: {frame_count}")
        click.echo(f"   Toplam hayvan tespiti: {detection_count}")
        
        if output:
            click.echo(f"   Çıktı: {output}")
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


# ============================================================
# DATABASE KOMUTLARI
# ============================================================

@cli.group()
def db():
    """💾 Veritabanı komutları."""
    pass


@db.command("stats")
def db_stats():
    """Veritabanı istatistiklerini göster."""
    try:
        from src.database import SessionLocal
        from src.database.models import Camera, Animal, Detection, Alert
        
        session = SessionLocal()
        
        click.echo("\n📊 Veritabanı İstatistikleri:")
        click.echo("-" * 40)
        
        click.echo(f"   Kameralar: {session.query(Camera).count()}")
        click.echo(f"   Hayvanlar: {session.query(Animal).count()}")
        click.echo(f"   Tespitler: {session.query(Detection).count()}")
        click.echo(f"   Uyarılar: {session.query(Alert).count()}")
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@db.command("init")
@click.option("--drop", is_flag=True, help="Mevcut tabloları sil ve yeniden oluştur")
def db_init(drop):
    """Veritabanını başlat."""
    try:
        from src.database import DatabaseManager, Base
        
        db_manager = DatabaseManager()
        
        if drop:
            click.confirm("⚠️ Tüm veriler silinecek. Devam?", abort=True)
            db_manager.drop_tables()
            click.echo("🗑️ Tablolar silindi")
        
        # Tablolar DatabaseManager.__init__ içinde otomatik oluşturulur
        click.echo("✅ Veritabanı tabloları oluşturuldu")
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@db.command("export")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", required=True, help="Çıktı dosyası")
@click.option("--table", "-t", type=click.Choice(["animals", "detections", "alerts"]), required=True)
def db_export(format, output, table):
    """Veritabanı verilerini dışa aktar."""
    try:
        from src.database import SessionLocal
        from src.database.models import Animal, Detection, Alert
        from src.export.exporters import CSVExporter, JSONExporter
        
        session = SessionLocal()
        
        # Tabloyu seç
        model_map = {
            "animals": Animal,
            "detections": Detection,
            "alerts": Alert
        }
        
        model = model_map[table]
        records = session.query(model).all()
        
        # Dict'e dönüştür
        data = []
        for record in records:
            if hasattr(record, 'to_dict'):
                data.append(record.to_dict())
            else:
                data.append({c.name: getattr(record, c.name) for c in record.__table__.columns})
        
        # Export et
        output_dir = str(Path(output).parent)
        filename = Path(output).name
        
        if format == "json":
            exporter = JSONExporter(output_dir=output_dir)
        else:
            exporter = CSVExporter(output_dir=output_dir)
        
        exporter.export(data, filename=filename)
        
        click.echo(f"✅ {len(data)} kayıt dışa aktarıldı: {output}")
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


# ============================================================
# API KOMUTLARI
# ============================================================

@cli.group()
def api():
    """🌐 API sunucu komutları."""
    pass


@api.command("start")
@click.option("--host", "-h", default="0.0.0.0", help="Host adresi")
@click.option("--port", "-p", default=8000, type=int, help="Port numarası")
@click.option("--reload", is_flag=True, help="Auto-reload aktif")
def api_start(host, port, reload):
    """API sunucusunu başlat."""
    try:
        import uvicorn
        
        click.echo(f"🚀 API sunucusu başlatılıyor: http://{host}:{port}")
        click.echo("   Durdurmak için Ctrl+C")
        
        uvicorn.run(
            "src.api:app",
            host=host,
            port=port,
            reload=reload
        )
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


@api.command("docs")
@click.option("--port", "-p", default=8000, type=int, help="Port numarası")
def api_docs(port):
    """API dökümantasyonunu aç."""
    import webbrowser
    
    url = f"http://localhost:{port}/docs"
    click.echo(f"🌐 API dökümantasyonu açılıyor: {url}")
    webbrowser.open(url)


# ============================================================
# BENCHMARK KOMUTLARI
# ============================================================

@cli.command("benchmark")
@click.option("--output", "-o", help="Rapor çıktı dosyası")
def benchmark(output):
    """Sistem performans testini çalıştır."""
    try:
        from scripts.benchmark import BenchmarkSuite
        
        click.echo("🚀 Benchmark başlatılıyor...")
        
        suite = BenchmarkSuite()
        report = suite.run_all()
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            click.echo(f"\n💾 Rapor kaydedildi: {output}")
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


# ============================================================
# SİSTEM DURUMU KOMUTLARI
# ============================================================

@cli.command("status")
def status():
    """Sistem durumunu göster."""
    try:
        click.echo("\n🐾 AI Hayvan Takip Sistemi - Durum")
        click.echo("=" * 50)
        
        # Python version
        import platform
        click.echo(f"\n📌 Python: {platform.python_version()}")
        
        # Modül durumları
        click.echo("\n📦 Modüller:")
        
        modules = [
            ("src.detection", "Detection"),
            ("src.tracking", "Tracking"),
            ("src.identification", "Identification"),
            ("src.behavior", "Behavior"),
            ("src.health", "Health"),
            ("src.feeding", "Feeding"),
            ("src.database", "Database"),
            ("src.api", "API"),
            ("src.export", "Export"),
            ("src.video", "Video"),
            ("src.alerts", "Alerts"),
            ("src.notifications", "Notifications"),
        ]
        
        for module_name, display_name in modules:
            try:
                __import__(module_name)
                click.echo(f"   ✅ {display_name}")
            except ImportError as e:
                click.echo(f"   ❌ {display_name}: {e}")
        
        # GPU durumu
        click.echo("\n🖥️ GPU:")
        try:
            import torch
            if torch.cuda.is_available():
                click.echo(f"   ✅ CUDA: {torch.cuda.get_device_name(0)}")
            else:
                click.echo("   ⚠️ CUDA mevcut değil (CPU kullanılacak)")
        except ImportError:
            click.echo("   ⚠️ PyTorch yüklü değil")
        
        # Veritabanı
        click.echo("\n💾 Veritabanı:")
        try:
            from sqlalchemy import text
            from src.database import DatabaseManager
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            click.echo("   ✅ Bağlantı başarılı")
        except Exception as e:
            click.echo(f"   ❌ Bağlantı hatası: {e}")
        
        click.echo("\n" + "=" * 50)
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


# ============================================================
# EXPORT KOMUTLARI
# ============================================================

@cli.group()
def export():
    """📤 Veri dışa aktarma komutları."""
    pass


@export.command("report")
@click.option("--start-date", help="Başlangıç tarihi (YYYY-MM-DD)")
@click.option("--end-date", help="Bitiş tarihi (YYYY-MM-DD)")
@click.option("--format", "-f", type=click.Choice(["json", "csv", "html"]), default="json")
@click.option("--output", "-o", required=True, help="Çıktı dosyası")
def export_report(start_date, end_date, format, output):
    """Aktivite raporu oluştur."""
    try:
        from src.database import SessionLocal
        from src.database.models import Detection, Animal
        from datetime import datetime
        
        session = SessionLocal()
        
        # Tarih filtreleme
        query = session.query(Detection)
        
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Detection.timestamp >= start)
        
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Detection.timestamp <= end)
        
        detections = query.all()
        
        # Rapor oluştur
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date or "All",
                "end": end_date or "All"
            },
            "summary": {
                "total_detections": len(detections),
                "unique_animals": len(set(d.animal_id for d in detections if d.animal_id)),
            },
            "detections": [
                {
                    "id": d.id,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                    "animal_id": d.animal_id,
                    "confidence": d.confidence
                }
                for d in detections
            ]
        }
        
        # Kaydet
        if format == "json":
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            with open(output, 'w', newline='', encoding='utf-8') as f:
                if report["detections"]:
                    writer = csv.DictWriter(f, fieldnames=report["detections"][0].keys())
                    writer.writeheader()
                    writer.writerows(report["detections"])
        
        click.echo(f"✅ Rapor oluşturuldu: {output}")
        click.echo(f"   Toplam tespit: {report['summary']['total_detections']}")
        
        session.close()
        
    except Exception as e:
        click.echo(f"❌ Hata: {e}", err=True)


def main():
    """CLI giriş noktası."""
    cli()


if __name__ == "__main__":
    main()
