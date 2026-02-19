# Quick Start Guide

Get up and running with the Language Learning Assistant in 5 minutes!

## Prerequisites

- Docker and Docker Compose
- 8GB+ RAM
- Internet connection (for initial setup)

## Steps

### 1. Build Docker Image (One-Time Setup)

**For most users (CPU):**
```bash
make build-image
```
or manually:
```bash
docker build -t lingua-local:cpu -f backend/Dockerfile .
```

**For NVIDIA GPU users:**
```bash
make build-image-gpu
```
or manually:
```bash
docker build -t lingua-local:gpu -f backend/Dockerfile.gpu .
```

**Important for GPU users:** The first build takes 5-10 minutes because it compiles `llama-cpp-python` with CUDA support. This is required for GPU acceleration - without it, the LLM will run on CPU and be 15-20x slower.

**Note:** You only need to build the image once. After that, `docker-compose up` will use the cached image and won't download packages every time.

### 2. Start the Application

**For most users (CPU):**
```bash
docker-compose up
```

**For NVIDIA GPU users:**
```bash
docker-compose -f docker-compose.gpu.yml up
```

**Note:** On first startup, the application will automatically download missing models (LLM and TTS). This may take 5-30 minutes depending on your internet speed (~2-3GB total). The application will start serving requests once models are downloaded.

### 3. Open Your Browser

Navigate to: **http://localhost:8080**

### 4. Start Learning!

1. Select your target language (e.g., Spanish)
2. Choose a scenario (e.g., Restaurant)
3. Click and hold the microphone button to speak
4. Or type a message in the text box
5. Listen to the response!

## First Time Setup

On first startup:
- Models will be automatically downloaded if missing (LLM and TTS)
- The first request may take longer as models are loaded into memory
- Subsequent requests will be faster

**Optional:** If you want to pre-download models before starting the container:
```bash
python3 scripts/download_models.py --all
```

## Troubleshooting

### Models downloading slowly

Models download automatically on first startup. If downloads fail or are slow:
- Check your internet connection
- Pre-download models manually: `python3 scripts/download_models.py --all`
- Check Docker logs: `docker-compose logs -f`

### Out of memory

Use smaller models by editing `.env`:
```bash
cp .env.example .env
# Edit .env and set:
STT_MODEL=base
LLM_MODEL=qwen2.5-0.5b-instruct
```

### Container won't start

Check Docker logs:
```bash
docker-compose logs -f
```

## What's Next?

- Try different languages and scenarios
- Adjust difficulty level (beginner → intermediate → advanced)
- Practice common travel phrases
- Have natural conversations!

## Stopping the Application

```bash
docker-compose down
```

## Getting Help

- Read the full [SETUP.md](SETUP.md) guide
- Check the [README.md](README.md) for architecture details
- Report issues on GitHub

---

**Happy Learning! 🌍**
