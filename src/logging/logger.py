"""
Gelişmiş Logger

Yapılandırılabilir loglama sistemi.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import sys
import json
from pathlib import Path


class LogLevel(Enum):
    """Log seviyesi"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogEntry:
    """Log girişi"""
    timestamp: datetime
    level: LogLevel
    message: str
    logger_name: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    extra: Dict[str, Any] = None
    exception: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Dict formatına çevir"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "message": self.message,
            "logger": self.logger_name,
            "module": self.module,
            "function": self.function,
            "line": self.line_number,
            "extra": self.extra,
            "exception": self.exception
        }
    
    def to_json(self) -> str:
        """JSON formatına çevir"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def format_text(self) -> str:
        """Metin formatı"""
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_str = self.level.name.ljust(8)
        
        text = f"[{timestamp_str}] {level_str} {self.logger_name}: {self.message}"
        
        if self.module:
            text += f" ({self.module}"
            if self.function:
                text += f".{self.function}"
            if self.line_number:
                text += f":{self.line_number}"
            text += ")"
        
        if self.exception:
            text += f"\n{self.exception}"
        
        return text


class LogHandler:
    """Log handler temel sınıfı"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level
    
    def should_log(self, entry: LogEntry) -> bool:
        """Bu log kaydedilmeli mi?"""
        return entry.level.value >= self.level.value
    
    def handle(self, entry: LogEntry):
        """Log'u işle"""
        if self.should_log(entry):
            self.emit(entry)
    
    def emit(self, entry: LogEntry):
        """Log'u yaz (alt sınıflar implement eder)"""
        raise NotImplementedError


class ConsoleHandler(LogHandler):
    """Konsol handler"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, 
                 use_color: bool = True):
        super().__init__(level)
        self.use_color = use_color
        
        # Renk kodları
        self.colors = {
            LogLevel.DEBUG: "\033[36m",      # Cyan
            LogLevel.INFO: "\033[32m",       # Green
            LogLevel.WARNING: "\033[33m",    # Yellow
            LogLevel.ERROR: "\033[31m",      # Red
            LogLevel.CRITICAL: "\033[35m"    # Magenta
        }
        self.reset = "\033[0m"
    
    def emit(self, entry: LogEntry):
        """Konsola yaz"""
        text = entry.format_text()
        
        if self.use_color and sys.stdout.isatty():
            color = self.colors.get(entry.level, "")
            text = f"{color}{text}{self.reset}"
        
        # ERROR ve üstü stderr'a
        stream = sys.stderr if entry.level.value >= LogLevel.ERROR.value else sys.stdout
        print(text, file=stream)


class FileHandler(LogHandler):
    """Dosya handler"""
    
    def __init__(self, filepath: str, level: LogLevel = LogLevel.INFO,
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        super().__init__(level)
        self.filepath = Path(filepath)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Dizini oluştur
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, entry: LogEntry):
        """Dosyaya yaz"""
        # Dosya boyutu kontrolü
        if self.filepath.exists() and self.filepath.stat().st_size >= self.max_bytes:
            self._rotate()
        
        # Log yaz
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(entry.format_text() + "\n")
    
    def _rotate(self):
        """Dosyayı rotate et"""
        # Eski backup'ları kaydır
        for i in range(self.backup_count - 1, 0, -1):
            old_file = self.filepath.with_suffix(f".{i}")
            new_file = self.filepath.with_suffix(f".{i+1}")
            
            if old_file.exists():
                if new_file.exists():
                    new_file.unlink()
                old_file.rename(new_file)
        
        # Mevcut dosyayı .1 yap
        if self.filepath.exists():
            backup_file = self.filepath.with_suffix(".1")
            if backup_file.exists():
                backup_file.unlink()
            self.filepath.rename(backup_file)


class JSONHandler(LogHandler):
    """JSON formatında dosya handler"""
    
    def __init__(self, filepath: str, level: LogLevel = LogLevel.INFO):
        super().__init__(level)
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, entry: LogEntry):
        """JSON formatında yaz"""
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(entry.to_json() + "\n")


class Logger:
    """Ana logger sınıfı"""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level
        self.handlers: list[LogHandler] = []
        self.propagate = True
    
    def add_handler(self, handler: LogHandler):
        """Handler ekle"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler):
        """Handler kaldır"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def _log(self, level: LogLevel, message: str, 
            extra: Optional[Dict] = None, exc_info: Optional[Exception] = None):
        """Log kaydı oluştur"""
        # Seviye kontrolü
        if level.value < self.level.value:
            return
        
        # Exception bilgisi
        exception_text = None
        if exc_info:
            import traceback
            exception_text = ''.join(traceback.format_exception(
                type(exc_info), exc_info, exc_info.__traceback__
            ))
        
        # Çağrı bilgisi
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back  # 2 seviye yukarı
        
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            logger_name=self.name,
            module=caller_frame.f_globals.get('__name__'),
            function=caller_frame.f_code.co_name,
            line_number=caller_frame.f_lineno,
            extra=extra,
            exception=exception_text
        )
        
        # Handler'lara gönder
        for handler in self.handlers:
            handler.handle(entry)
    
    def debug(self, message: str, **kwargs):
        """Debug log"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info log"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning log"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error log"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical log"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc_info: Exception, **kwargs):
        """Exception log"""
        kwargs['exc_info'] = exc_info
        self._log(LogLevel.ERROR, message, **kwargs)


# Global logger registry
_loggers: Dict[str, Logger] = {}


def get_logger(name: str = "root", level: LogLevel = LogLevel.INFO) -> Logger:
    """Logger al veya oluştur"""
    if name not in _loggers:
        logger = Logger(name, level)
        
        # Default console handler
        console_handler = ConsoleHandler(level=level)
        logger.add_handler(console_handler)
        
        _loggers[name] = logger
    
    return _loggers[name]


def setup_logging(log_dir: str = "logs", 
                 console_level: LogLevel = LogLevel.INFO,
                 file_level: LogLevel = LogLevel.DEBUG):
    """Loglama sistemini ayarla"""
    root_logger = get_logger("root")
    
    # Mevcut handler'ları temizle
    root_logger.handlers.clear()
    
    # Console handler
    console = ConsoleHandler(level=console_level, use_color=True)
    root_logger.add_handler(console)
    
    # File handler
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    file_handler = FileHandler(
        filepath=str(log_path / "app.log"),
        level=file_level
    )
    root_logger.add_handler(file_handler)
    
    # JSON handler (error'lar için)
    json_handler = JSONHandler(
        filepath=str(log_path / "errors.json"),
        level=LogLevel.ERROR
    )
    root_logger.add_handler(json_handler)
    
    return root_logger
