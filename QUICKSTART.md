# Quick Start Guide

Get up and running with the Language Learning Assistant in 5 minutes!

## Prerequisites

- Docker and Docker Compose
- 8GB+ RAM
- Internet connection (for initial setup)

## Steps

### 1. Download Models

```bash
python3 scripts/download_models.py
```

**Note:** This downloads ~2-3GB of models. It may take 5-30 minutes depending on your internet speed.

### 2. Build Docker Image (One-Time Setup)

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

**Note:** You only need to build the image once. After that, `docker-compose up` will use the cached image and won't download packages every time.

### 3. Start the Application

**For most users (CPU):**
```bash
docker-compose up
```

**For NVIDIA GPU users:**
```bash
docker-compose -f docker-compose.gpu.yml up
```

### 4. Open Your Browser

Navigate to: **http://localhost:8080**

### 5. Start Learning!

1. Select your target language (e.g., Spanish)
2. Choose a scenario (e.g., Restaurant)
3. Click and hold the microphone button to speak
4. Or type a message in the text box
5. Listen to the response!

## First Time Setup

The first request may take longer as models are loaded into memory. Subsequent requests will be faster.

## Troubleshooting

### "Models not found" error

Run the download script:
```bash
python3 scripts/download_models.py --all
```

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
