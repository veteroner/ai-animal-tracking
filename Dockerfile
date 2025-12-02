# AI Animal Tracking System - Dockerfile
# ==========================================
# Multi-stage build for production deployment

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Production
# ==========================================
FROM python:3.9-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs /app/models

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Download YOLO model during build
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" || true

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# Stage 3: Development
# ==========================================
FROM production as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    httpx \
    black \
    flake8 \
    mypy

# Development command with reload
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
