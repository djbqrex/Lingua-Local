# Multi-stage Dockerfile for Language Learning Assistant

# Base image with CUDA support (for GPU)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 as base-gpu

# Install Python on GPU base
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Base image without CUDA (for CPU-only)
FROM python:3.11-slim as base-cpu

# Default to CPU build
FROM base-cpu as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

# Install system dependencies including FFmpeg dev libraries
# faster-whisper requires av (PyAV) which needs FFmpeg development libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    libsndfile1 \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.docker.txt ./requirements.txt

# Install Python dependencies
# faster-whisper 1.0.3+ uses av>=13.0.0 which builds correctly with modern FFmpeg
# pydub is installed separately with --no-deps (doesn't need av, just ffmpeg CLI)
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt && \
    pip install pydub==0.25.1 --no-deps

# Copy application code
COPY backend /app/backend

# Create directories for models and temp files
RUN mkdir -p /app/models/stt /app/models/tts /app/models/llm /app/tmp

# Copy frontend
COPY frontend /app/frontend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
