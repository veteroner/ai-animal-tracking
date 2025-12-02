# tests/unit/test_export.py
"""
Export Module Unit Tests
========================

CSVExporter, JSONExporter ve WebhookSender için unit testler.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestCSVExporter:
    """CSVExporter testleri."""
    
    def test_exporter_initialization(self):
        """Exporter başlatma testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            assert exporter.output_dir == Path(tmpdir)
            assert exporter.delimiter == ","
            assert exporter.encoding == "utf-8"
    
    def test_export_empty_data(self):
        """Boş veri export testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            result = exporter.export([], "test")
            
            assert result is None
    
    def test_export_data(self):
        """Veri export testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            data = [
                {"name": "cow_001", "value": 100},
                {"name": "cow_002", "value": 200},
            ]
            
            filepath = exporter.export(data, "test", timestamp=False)
            
            assert filepath is not None
            assert filepath.exists()
            assert filepath.suffix == ".csv"
    
    def test_export_custom_columns(self):
        """Özel sütunlarla export testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            data = [
                {"a": 1, "b": 2, "c": 3},
                {"a": 4, "b": 5, "c": 6},
            ]
            
            filepath = exporter.export(
                data, 
                "test", 
                columns=["a", "c"],
                timestamp=False
            )
            
            # Dosya içeriğini kontrol et
            with open(filepath) as f:
                content = f.read()
            
            assert "a" in content
            assert "c" in content


class TestJSONExporter:
    """JSONExporter testleri."""
    
    def test_exporter_initialization(self):
        """Exporter başlatma testi."""
        from src.export.exporters import JSONExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JSONExporter(output_dir=tmpdir, indent=4)
            
            assert exporter.indent == 4
    
    def test_export_dict(self):
        """Dict export testi."""
        from src.export.exporters import JSONExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JSONExporter(output_dir=tmpdir)
            
            data = {
                "name": "test",
                "value": 123,
                "nested": {"a": 1, "b": 2}
            }
            
            filepath = exporter.export(data, "test", timestamp=False)
            
            assert filepath.exists()
            
            with open(filepath) as f:
                loaded = json.load(f)
            
            assert loaded["name"] == "test"
            assert loaded["value"] == 123
    
    def test_export_list(self):
        """Liste export testi."""
        from src.export.exporters import JSONExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JSONExporter(output_dir=tmpdir)
            
            data = [
                {"id": 1, "name": "a"},
                {"id": 2, "name": "b"},
            ]
            
            filepath = exporter.export(data, "test", timestamp=False)
            
            with open(filepath) as f:
                loaded = json.load(f)
            
            assert len(loaded) == 2


class TestBaseExporter:
    """BaseExporter testleri."""
    
    def test_generate_filename_with_timestamp(self):
        """Zaman damgalı dosya adı testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            filename = exporter.generate_filename("test", "csv", timestamp=True)
            
            assert filename.startswith("test_")
            assert filename.endswith(".csv")
            # Format: test_YYYYMMDD_HHMMSS.csv
            assert len(filename) > len("test_.csv")
    
    def test_generate_filename_without_timestamp(self):
        """Zaman damgasız dosya adı testi."""
        from src.export.exporters import CSVExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter(output_dir=tmpdir)
            
            filename = exporter.generate_filename("test", "csv", timestamp=False)
            
            assert filename == "test.csv"


class TestWebhookSender:
    """WebhookSender testleri."""
    
    def test_sender_initialization(self):
        """Sender başlatma testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        
        assert sender.async_mode == False or sender.async_mode == True
        assert len(sender._webhooks) == 0
    
    def test_add_webhook(self):
        """Webhook ekleme testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        
        webhook_id = sender.add_webhook(
            url="https://example.com/webhook",
            name="test_webhook"
        )
        
        assert webhook_id == "test_webhook"
        assert "test_webhook" in sender._webhooks
    
    def test_add_webhook_invalid_url(self):
        """Geçersiz URL ile webhook ekleme testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        
        with pytest.raises(ValueError):
            sender.add_webhook(url="not-a-url", name="bad")
    
    def test_remove_webhook(self):
        """Webhook kaldırma testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        sender.add_webhook("https://example.com/webhook", "test")
        
        assert "test" in sender._webhooks
        
        sender.remove_webhook("test")
        
        assert "test" not in sender._webhooks
    
    def test_enable_disable_webhook(self):
        """Webhook etkinleştirme/devre dışı bırakma testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        sender.add_webhook("https://example.com/webhook", "test")
        
        # Varsayılan olarak aktif
        assert sender._webhooks["test"].enabled == True
        
        # Devre dışı bırak
        sender.enable_webhook("test", False)
        assert sender._webhooks["test"].enabled == False
        
        # Tekrar etkinleştir
        sender.enable_webhook("test", True)
        assert sender._webhooks["test"].enabled == True
    
    def test_statistics(self):
        """İstatistik testi."""
        from src.export.webhook import WebhookSender
        
        sender = WebhookSender()
        
        stats = sender.statistics
        
        assert "events_sent" in stats
        assert "events_failed" in stats
        assert "events_dropped" in stats
        assert "webhooks_active" in stats


class TestWebhookEvent:
    """WebhookEvent testleri."""
    
    def test_event_creation(self):
        """Event oluşturma testi."""
        from src.export.webhook import WebhookEvent, WebhookEventType
        
        event = WebhookEvent(
            event_type=WebhookEventType.DETECTION,
            data={"animal_id": "cow_001"}
        )
        
        assert event.event_type == WebhookEventType.DETECTION
        assert event.data["animal_id"] == "cow_001"
        assert event.event_id != ""
    
    def test_event_to_dict(self):
        """Event dict dönüşüm testi."""
        from src.export.webhook import WebhookEvent, WebhookEventType
        
        event = WebhookEvent(
            event_type=WebhookEventType.HEALTH_ALERT,
            data={"severity": "high"}
        )
        
        d = event.to_dict()
        
        assert d["event_type"] == "health_alert"
        assert d["data"]["severity"] == "high"
        assert "timestamp" in d
        assert "event_id" in d


class TestWebhookConfig:
    """WebhookConfig testleri."""
    
    def test_config_creation(self):
        """Config oluşturma testi."""
        from src.export.webhook import WebhookConfig
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            name="test"
        )
        
        assert config.url == "https://example.com/webhook"
        assert config.enabled == True
        assert config.max_retries == 3
    
    def test_config_accepts_event_no_filter(self):
        """Filtresiz event kabul testi."""
        from src.export.webhook import WebhookConfig, WebhookEventType
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            event_types=[]  # Filtre yok
        )
        
        # Hepsini kabul etmeli
        assert config.accepts_event(WebhookEventType.DETECTION) == True
        assert config.accepts_event(WebhookEventType.HEALTH_ALERT) == True
    
    def test_config_accepts_event_with_filter(self):
        """Filtreli event kabul testi."""
        from src.export.webhook import WebhookConfig, WebhookEventType
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            event_types=[WebhookEventType.DETECTION]
        )
        
        assert config.accepts_event(WebhookEventType.DETECTION) == True
        assert config.accepts_event(WebhookEventType.HEALTH_ALERT) == False


# Pytest fixtures
@pytest.fixture
def temp_export_dir():
    """Geçici export dizini."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def csv_exporter(temp_export_dir):
    """CSVExporter instance."""
    from src.export.exporters import CSVExporter
    return CSVExporter(output_dir=temp_export_dir)


@pytest.fixture
def json_exporter(temp_export_dir):
    """JSONExporter instance."""
    from src.export.exporters import JSONExporter
    return JSONExporter(output_dir=temp_export_dir)


@pytest.fixture
def webhook_sender():
    """WebhookSender instance."""
    from src.export.webhook import WebhookSender
    return WebhookSender()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
