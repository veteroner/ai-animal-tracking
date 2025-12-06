"""
API Middleware - İstek/Yanıt işleme
"""

import time
import logging
import uuid
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """İstek loglama middleware'i"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Request ID oluştur
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Başlangıç zamanı
        start_time = time.time()
        
        # İstek bilgileri
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Yanıtı al
        try:
            response = await call_next(request)
            
            # İşlem süresi
            process_time = (time.time() - start_time) * 1000
            
            # Log
            logger.info(
                f"[{request_id}] {method} {path} - {response.status_code} "
                f"({process_time:.2f}ms) - {client_ip}"
            )
            
            # Header'a işlem süresini ekle
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {method} {path} - ERROR ({process_time:.2f}ms) - {e}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware'i"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_minute = datetime.now().strftime("%Y-%m-%d-%H-%M")
        key = f"{client_ip}:{current_minute}"
        
        # Sayaç kontrolü
        if key not in self.requests:
            self.requests[key] = 0
            
        self.requests[key] += 1
        
        # Limit kontrolü
        if self.requests[key] > self.requests_per_minute:
            logger.warning(f"Rate limit aşıldı: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Çok fazla istek gönderildi",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            )
            
        # Eski kayıtları temizle
        old_keys = [k for k in self.requests.keys() if not k.endswith(current_minute)]
        for old_key in old_keys:
            del self.requests[old_key]
            
        response = await call_next(request)
        
        # Rate limit bilgisini header'a ekle
        remaining = max(0, self.requests_per_minute - self.requests[key])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware'i"""
    
    def __init__(
        self, 
        app, 
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Preflight request
        if request.method == "OPTIONS":
            response = Response()
            response.status_code = 200
        else:
            response = await call_next(request)
            
        # CORS headers
        origin = request.headers.get("origin", "")
        
        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Hata işleme middleware'i"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.exception(f"[{request_id}] İşlenmeyen hata: {e}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Sunucu hatası oluştu",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "request_id": request_id
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Güvenlik header'ları middleware'i"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Güvenlik header'ları
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Sıkıştırma middleware'i (basit gzip check)"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Yanıt boyutuna göre sıkıştırma öner
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if "gzip" in accept_encoding:
            response.headers["Vary"] = "Accept-Encoding"
            
        return response


def setup_middlewares(app):
    """Tüm middleware'leri kur"""
    # Sıralama önemli - en içteki en son eklenir
    
    # Güvenlik header'ları
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Hata işleme
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
    
    # Loglama
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("API middleware'leri kuruldu")
