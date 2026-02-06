# Multi-stage Dockerfile for Language Learning Assistant

# Base image with CUDA support (for GPU)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 as base-gpu

# Base image without CUDA (for CPU-only)
FROM python:3.11-slim as base-cpu

# Choose base based on build argument
ARG USE_GPU=true
FROM base-${USE_GPU} as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . /app/backend

# Create directories for models and temp files
RUN mkdir -p /app/models/stt /app/models/tts /app/models/llm /app/tmp

# Copy frontend
COPY ../frontend /app/frontend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
