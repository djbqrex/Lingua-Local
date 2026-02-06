# Makefile for Language Learning Assistant

.PHONY: help install download-models build up down logs clean test

# Default target
help:
	@echo "Language Learning Assistant - Available Commands"
	@echo "================================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make download-models - Download all required models"
	@echo ""
	@echo "Docker:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start application (CPU)"
	@echo "  make up-gpu         - Start application (GPU)"
	@echo "  make down           - Stop application"
	@echo "  make restart        - Restart application"
	@echo "  make logs           - View application logs"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Run in development mode"
	@echo "  make dev-backend    - Run backend with hot-reload"
	@echo "  make dev-frontend   - Serve frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Remove temporary files"
	@echo "  make clean-models   - Remove downloaded models"
	@echo "  make clean-all      - Remove everything (including models)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make check-health   - Check API health"
	@echo ""

# Installation
install:
	@echo "Installing Python dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Model download
download-models:
	@echo "Downloading models..."
	python3 scripts/download_models.py --all
	@echo "✓ Models downloaded"

download-models-small:
	@echo "Downloading lightweight models..."
	python3 scripts/download_models.py --stt-model base --llm-model qwen2.5-0.5b-instruct
	@echo "✓ Lightweight models downloaded"

# Docker operations
build:
	@echo "Building Docker image..."
	docker-compose build
	@echo "✓ Docker image built"

up:
	@echo "Starting application (CPU mode)..."
	docker-compose -f docker-compose.cpu.yml up -d
	@echo "✓ Application started at http://localhost:8080"

up-gpu:
	@echo "Starting application (GPU mode)..."
	docker-compose -f docker-compose.gpu.yml up -d
	@echo "✓ Application started at http://localhost:8080"

up-dev:
	@echo "Starting application in development mode..."
	docker-compose up
	@echo "✓ Application started at http://localhost:8080"

down:
	@echo "Stopping application..."
	docker-compose down
	@echo "✓ Application stopped"

restart:
	@echo "Restarting application..."
	docker-compose down
	docker-compose up -d
	@echo "✓ Application restarted"

logs:
	docker-compose logs -f

# Development mode
dev: dev-backend

dev-backend:
	@echo "Starting backend in development mode..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend server..."
	python3 -m http.server 8080 --directory frontend

# Maintenance
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf tmp/* 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	@echo "✓ Temporary files cleaned"

clean-models:
	@echo "Removing downloaded models..."
	@read -p "Are you sure? This will delete all models (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf models/*; \
		echo "✓ Models removed"; \
	else \
		echo "Cancelled"; \
	fi

clean-all: clean clean-models
	@echo "Removing Docker containers and volumes..."
	docker-compose down -v
	@echo "✓ Everything cleaned"

# Testing
test:
	@echo "Running tests..."
	cd backend && pytest
	@echo "✓ Tests passed"

check-health:
	@echo "Checking API health..."
	@curl -s http://localhost:8000/api/health | python3 -m json.tool || \
		echo "✗ API not responding. Is the application running?"

# Quick start
quickstart: download-models up
	@echo ""
	@echo "========================================="
	@echo "Language Learning Assistant is ready!"
	@echo "========================================="
	@echo ""
	@echo "Access the application at:"
	@echo "  http://localhost:8080"
	@echo ""
	@echo "API documentation at:"
	@echo "  http://localhost:8000/docs"
	@echo ""
	@echo "View logs with:"
	@echo "  make logs"
	@echo ""

# Status
status:
	@echo "Application Status:"
	@echo "==================="
	@docker-compose ps
	@echo ""
	@echo "Model Status:"
	@echo "============="
	@ls -lh models/stt/ 2>/dev/null || echo "STT models: Not found"
	@ls -lh models/tts/ 2>/dev/null || echo "TTS models: Not found"
	@ls -lh models/llm/ 2>/dev/null || echo "LLM models: Not found"
