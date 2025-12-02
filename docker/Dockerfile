# ===========================================
# AI Animal Tracking System - Dockerfile
# ===========================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="AI Animal Tracking Team"
LABEL version="0.1.0"
LABEL description="AI-powered animal tracking and behavior analysis system"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Requirements dosyasını kopyala ve bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Gerekli dizinleri oluştur
RUN mkdir -p data/videos data/snapshots data/exports data/embeddings \
    models/pretrained models/custom \
    logs

# Non-root user oluştur
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Varsayılan komut
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
