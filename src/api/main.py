"""
AI Animal Tracking System - FastAPI Application
===============================================

Ana API uygulması.
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Proje kök dizinini path'e ekle
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.constants import API_VERSION, API_PREFIX
from src.api.routes import (
    cameras_router, 
    animals_router, 
    analytics_router, 
    detection_router,
    behaviors_router,
    health_router,
    export_router
)
from src.api.routes.alerts import router as alerts_router
from src.api.routes.streaming import router as streaming_router
from src.api.routes.reproduction_routes import router as reproduction_router
from src.api.routes.poultry_routes import router as poultry_router

logger = logging.getLogger(__name__)

# ===========================================
# Global State
# ===========================================
app_state = {
    "db_initialized": False,
    "model_loaded": False,
    "startup_time": None,
}


# ===========================================
# Application Lifespan
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü yönetimi"""
    # Startup
    print("🚀 Starting AI Animal Tracking System...")
    app_state["startup_time"] = datetime.now()
    
    # 1. Veritabanı bağlantısı
    try:
        from src.database.connection import get_db
        from src.database.models import Base
        
        db = get_db()
        db.create_tables(Base)
        app_state["db_initialized"] = True
        print("✅ Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        app_state["db_initialized"] = False
    
    # 2. Model yükleme (opsiyonel - cv2 gerektirir)
    try:
        # Lazy model loading - sadece kullanıldığında yüklenecek
        app_state["model_loaded"] = True
        print("✅ Model loading ready (lazy)")
    except Exception as e:
        logger.warning(f"Model loading skipped: {e}")
        app_state["model_loaded"] = False
    
    print(f"✅ API ready at http://0.0.0.0:8000")
    print(f"📚 Docs at http://0.0.0.0:8000/docs")
    
    yield
    
    # Shutdown
    print("👋 Shutting down AI Animal Tracking System...")
    
    # Temizlik işlemleri
    try:
        from src.database.connection import get_db
        get_db().close()
        print("✅ Database connection closed")
    except Exception:
        pass


# ===========================================
# FastAPI Application
# ===========================================

app = FastAPI(
    title="AI Animal Tracking System",
    description="""
    🐄 Yapay Zeka ile Hayvan Takip ve Davranış Analiz Sistemi
    
    ## Özellikler
    
    * **Gerçek Zamanlı Tespit** - YOLOv8 ile hayvan tespiti
    * **Nesne Takibi** - DeepSORT ile sürekli takip
    * **Benzersiz Kimlik** - Her hayvana ID atama
    * **Davranış Analizi** - Yeme, yürüme, dinlenme tespiti
    * **Sağlık İzleme** - Vücut kondisyon skoru, topallama tespiti
    
    ## API Endpoints
    
    Detaylı API dokümantasyonu için `/docs` veya `/redoc` sayfalarını ziyaret edin.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    lifespan=lifespan,
)


# ===========================================
# CORS Middleware
# ===========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da kısıtlanmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Exception Handlers
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "path": str(request.url),
        }
    )


# ===========================================
# Health Check Endpoints
# ===========================================

@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "name": "AI Animal Tracking System",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Sistem sağlık kontrolü.
    
    Returns:
        Sistem durumu ve bileşen bilgileri
    """
    # Uptime hesapla
    uptime = None
    if app_state["startup_time"]:
        uptime = str(datetime.now() - app_state["startup_time"])
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "uptime": uptime,
        "components": {
            "api": "healthy",
            "database": "healthy" if app_state["db_initialized"] else "not_configured",
            "model": "ready" if app_state["model_loaded"] else "not_loaded",
        }
    }


@app.get("/health/live", tags=["Health"])
async def liveness_probe() -> Dict[str, str]:
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness_probe() -> Dict[str, str]:
    """Kubernetes readiness probe"""
    # TODO: Tüm bileşenlerin hazır olduğunu kontrol et
    return {"status": "ready"}


# ===========================================
# API Info
# ===========================================

@app.get(f"{API_PREFIX}/info", tags=["Info"])
async def api_info() -> Dict[str, Any]:
    """API bilgileri"""
    return {
        "name": "AI Animal Tracking API",
        "version": API_VERSION,
        "endpoints": {
            "cameras": f"{API_PREFIX}/cameras",
            "animals": f"{API_PREFIX}/animals",
            "detections": f"{API_PREFIX}/detections",
            "behaviors": f"{API_PREFIX}/behaviors",
            "health": f"{API_PREFIX}/health",
            "analytics": f"{API_PREFIX}/analytics",
            "export": f"{API_PREFIX}/export",
            "reproduction": f"{API_PREFIX}/reproduction",
            "poultry": f"{API_PREFIX}/poultry",
        }
    }


# ===========================================
# Placeholder Routes (TODO: Implement)
# ===========================================

# Routers
app.include_router(cameras_router, prefix=API_PREFIX)
app.include_router(animals_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(streaming_router, prefix=API_PREFIX)
app.include_router(detection_router, prefix=API_PREFIX)
app.include_router(behaviors_router, prefix=API_PREFIX)
app.include_router(health_router, prefix=f"{API_PREFIX}/animals")
app.include_router(export_router, prefix=API_PREFIX)
app.include_router(reproduction_router, prefix=API_PREFIX)
app.include_router(poultry_router, prefix=API_PREFIX)


# ===========================================
# Run Server (Development)
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
