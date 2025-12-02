"""
CLI unit testleri.
"""

import pytest
from click.testing import CliRunner


class TestCLIBasics:
    """CLI temel testleri."""
    
    def test_cli_version(self):
        """Version komutu testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output
    
    def test_cli_help(self):
        """Help komutu testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "AI Hayvan Takip Sistemi" in result.output


class TestCameraCommands:
    """Kamera komutları testleri."""
    
    def test_camera_help(self):
        """Camera help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["camera", "--help"])
        
        assert result.exit_code == 0
        assert "Kamera yönetimi" in result.output
    
    def test_camera_list_help(self):
        """Camera list help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["camera", "list", "--help"])
        
        assert result.exit_code == 0


class TestDetectCommands:
    """Detection komutları testleri."""
    
    def test_detect_help(self):
        """Detect help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["detect", "--help"])
        
        assert result.exit_code == 0
        assert "Detection komutları" in result.output
    
    def test_detect_image_help(self):
        """Detect image help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["detect", "image", "--help"])
        
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--confidence" in result.output


class TestDBCommands:
    """Veritabanı komutları testleri."""
    
    def test_db_help(self):
        """DB help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "--help"])
        
        assert result.exit_code == 0
        assert "Veritabanı komutları" in result.output
    
    def test_db_stats_help(self):
        """DB stats help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "stats", "--help"])
        
        assert result.exit_code == 0


class TestAPICommands:
    """API komutları testleri."""
    
    def test_api_help(self):
        """API help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["api", "--help"])
        
        assert result.exit_code == 0
        assert "API sunucu" in result.output
    
    def test_api_start_help(self):
        """API start help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["api", "start", "--help"])
        
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output


class TestStatusCommand:
    """Status komutu testleri."""
    
    def test_status_help(self):
        """Status help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        
        assert result.exit_code == 0


class TestExportCommands:
    """Export komutları testleri."""
    
    def test_export_help(self):
        """Export help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])
        
        assert result.exit_code == 0
        assert "dışa aktarma" in result.output
    
    def test_export_report_help(self):
        """Export report help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "report", "--help"])
        
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output" in result.output


class TestBenchmarkCommand:
    """Benchmark komutu testleri."""
    
    def test_benchmark_help(self):
        """Benchmark help testi."""
        from src.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["benchmark", "--help"])
        
        assert result.exit_code == 0
        assert "--output" in result.output
