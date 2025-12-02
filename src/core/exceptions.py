"""
AI Animal Tracking System - Custom Exceptions
==============================================

Sistem genelinde kullanılan özel exception sınıfları.
"""


class AnimalTrackingError(Exception):
    """Temel exception sınıfı"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# ===========================================
# Kamera Hataları
# ===========================================

class CameraError(AnimalTrackingError):
    """Kamera ile ilgili hatalar"""
    
    def __init__(self, message: str, camera_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.camera_id = camera_id
        self.details["camera_id"] = camera_id


class CameraConnectionError(CameraError):
    """Kamera bağlantı hatası"""
    
    def __init__(self, message: str, camera_id: str = None, source: str = None):
        super().__init__(
            message,
            camera_id=camera_id,
            code="CAMERA_CONNECTION_ERROR"
        )
        self.details["source"] = source


class CameraNotFoundError(CameraError):
    """Kamera bulunamadı hatası"""
    
    def __init__(self, camera_id: str):
        super().__init__(
            f"Camera not found: {camera_id}",
            camera_id=camera_id,
            code="CAMERA_NOT_FOUND"
        )


class CameraTimeoutError(CameraError):
    """Kamera timeout hatası"""
    
    def __init__(self, camera_id: str, timeout: float):
        super().__init__(
            f"Camera timeout after {timeout}s: {camera_id}",
            camera_id=camera_id,
            code="CAMERA_TIMEOUT"
        )
        self.details["timeout"] = timeout


class InvalidFrameError(CameraError):
    """Geçersiz frame hatası"""
    
    def __init__(self, camera_id: str = None):
        super().__init__(
            "Invalid frame received",
            camera_id=camera_id,
            code="INVALID_FRAME"
        )


# ===========================================
# Tespit Hataları
# ===========================================

class DetectionError(AnimalTrackingError):
    """Nesne tespiti ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="DETECTION_ERROR", **kwargs)


class ModelLoadError(DetectionError):
    """Model yükleme hatası"""
    
    def __init__(self, model_path: str, reason: str = None):
        message = f"Failed to load model: {model_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, code="MODEL_LOAD_ERROR")
        self.details["model_path"] = model_path
        self.details["reason"] = reason


class ModelInferenceError(DetectionError):
    """Model inference hatası"""
    
    def __init__(self, message: str = "Inference failed"):
        super().__init__(message, code="MODEL_INFERENCE_ERROR")


class InvalidInputError(DetectionError):
    """Geçersiz input hatası"""
    
    def __init__(self, expected: str, received: str):
        super().__init__(
            f"Invalid input. Expected: {expected}, Received: {received}",
            code="INVALID_INPUT"
        )
        self.details["expected"] = expected
        self.details["received"] = received


# ===========================================
# Takip Hataları
# ===========================================

class TrackingError(AnimalTrackingError):
    """Nesne takibi ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="TRACKING_ERROR", **kwargs)


class TrackNotFoundError(TrackingError):
    """Track bulunamadı hatası"""
    
    def __init__(self, track_id: int):
        super().__init__(
            f"Track not found: {track_id}",
            code="TRACK_NOT_FOUND"
        )
        self.details["track_id"] = track_id


class ReIDError(TrackingError):
    """Re-identification hatası"""
    
    def __init__(self, message: str = "Re-identification failed"):
        super().__init__(message, code="REID_ERROR")


# ===========================================
# Veritabanı Hataları
# ===========================================

class DatabaseError(AnimalTrackingError):
    """Veritabanı ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="DATABASE_ERROR", **kwargs)


class ConnectionError(DatabaseError):
    """Veritabanı bağlantı hatası"""
    
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, code="DB_CONNECTION_ERROR")


class RecordNotFoundError(DatabaseError):
    """Kayıt bulunamadı hatası"""
    
    def __init__(self, model: str, identifier: str):
        super().__init__(
            f"{model} not found: {identifier}",
            code="RECORD_NOT_FOUND"
        )
        self.details["model"] = model
        self.details["identifier"] = identifier


class DuplicateRecordError(DatabaseError):
    """Tekrarlayan kayıt hatası"""
    
    def __init__(self, model: str, field: str, value: str):
        super().__init__(
            f"Duplicate {model}.{field}: {value}",
            code="DUPLICATE_RECORD"
        )
        self.details["model"] = model
        self.details["field"] = field
        self.details["value"] = value


# ===========================================
# Kimlik Hataları
# ===========================================

class IdentificationError(AnimalTrackingError):
    """Hayvan kimlik ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="IDENTIFICATION_ERROR", **kwargs)


class AnimalNotFoundError(IdentificationError):
    """Hayvan bulunamadı hatası"""
    
    def __init__(self, animal_id: str):
        super().__init__(
            f"Animal not found: {animal_id}",
            code="ANIMAL_NOT_FOUND"
        )
        self.details["animal_id"] = animal_id


class DuplicateAnimalError(IdentificationError):
    """Tekrarlayan hayvan hatası"""
    
    def __init__(self, animal_id: str):
        super().__init__(
            f"Animal already exists: {animal_id}",
            code="DUPLICATE_ANIMAL"
        )
        self.details["animal_id"] = animal_id


# ===========================================
# Davranış Hataları
# ===========================================

class BehaviorError(AnimalTrackingError):
    """Davranış analizi ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="BEHAVIOR_ERROR", **kwargs)


class InvalidBehaviorError(BehaviorError):
    """Geçersiz davranış hatası"""
    
    def __init__(self, behavior: str):
        super().__init__(
            f"Invalid behavior type: {behavior}",
            code="INVALID_BEHAVIOR"
        )
        self.details["behavior"] = behavior


# ===========================================
# API Hataları
# ===========================================

class APIError(AnimalTrackingError):
    """API ile ilgili hatalar"""
    
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        super().__init__(message, code="API_ERROR", **kwargs)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Kimlik doğrulama hatası"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401, code="AUTHENTICATION_ERROR")


class AuthorizationError(APIError):
    """Yetkilendirme hatası"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403, code="AUTHORIZATION_ERROR")


class RateLimitError(APIError):
    """Rate limit hatası"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            status_code=429,
            code="RATE_LIMIT_ERROR"
        )
        self.details["retry_after"] = retry_after


class ValidationError(APIError):
    """Validasyon hatası"""
    
    def __init__(self, errors: list):
        super().__init__(
            "Validation failed",
            status_code=422,
            code="VALIDATION_ERROR"
        )
        self.details["errors"] = errors


# ===========================================
# Depolama Hataları
# ===========================================

class StorageError(AnimalTrackingError):
    """Depolama ile ilgili hatalar"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="STORAGE_ERROR", **kwargs)


class FileNotFoundError(StorageError):
    """Dosya bulunamadı hatası"""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"File not found: {file_path}",
            code="FILE_NOT_FOUND"
        )
        self.details["file_path"] = file_path


class StorageFullError(StorageError):
    """Depolama dolu hatası"""
    
    def __init__(self, available_space: int = 0):
        super().__init__(
            "Storage is full",
            code="STORAGE_FULL"
        )
        self.details["available_space"] = available_space


# ===========================================
# Bildirim Hataları
# ===========================================

class NotificationError(AnimalTrackingError):
    """Bildirim ile ilgili hatalar"""
    
    def __init__(self, message: str, channel: str = None, **kwargs):
        super().__init__(message, code="NOTIFICATION_ERROR", **kwargs)
        self.details["channel"] = channel


class EmailError(NotificationError):
    """E-posta hatası"""
    
    def __init__(self, message: str = "Failed to send email"):
        super().__init__(message, channel="email", code="EMAIL_ERROR")


class SMSError(NotificationError):
    """SMS hatası"""
    
    def __init__(self, message: str = "Failed to send SMS"):
        super().__init__(message, channel="sms", code="SMS_ERROR")


# ===========================================
# Konfigürasyon Hataları
# ===========================================

class ConfigurationError(AnimalTrackingError):
    """Konfigürasyon ile ilgili hatalar"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, code="CONFIGURATION_ERROR", **kwargs)
        self.details["config_key"] = config_key


class MissingConfigError(ConfigurationError):
    """Eksik konfigürasyon hatası"""
    
    def __init__(self, config_key: str):
        super().__init__(
            f"Missing required configuration: {config_key}",
            config_key=config_key,
            code="MISSING_CONFIG"
        )


class InvalidConfigError(ConfigurationError):
    """Geçersiz konfigürasyon hatası"""
    
    def __init__(self, config_key: str, reason: str = None):
        message = f"Invalid configuration: {config_key}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, config_key=config_key, code="INVALID_CONFIG")
