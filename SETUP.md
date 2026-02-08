# Setup Guide - Local Language Learning Assistant

This guide will help you set up and run the Language Learning Assistant on your system.

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker and Docker Compose installed
- 8GB+ RAM available
- (Optional) NVIDIA GPU with CUDA support for better performance

### Steps

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd local-language-learning-assistant
   ```

2. **Download Models**
   ```bash
   python3 scripts/download_models.py
   ```
   
   This will download:
   - Whisper model for speech-to-text (~244MB for small model)
   - Piper voice for text-to-speech (~40MB)
   - Qwen language model (~1-2GB)

3. **Start the Application**
   
   **For CPU-only systems:**
   ```bash
   docker-compose -f docker-compose.cpu.yml up
   ```
   
   **For systems with NVIDIA GPU:**
   ```bash
   docker-compose -f docker-compose.gpu.yml up
   ```
   
   **For auto-detection:**
   ```bash
   docker-compose up
   ```

4. **Open Browser**
   
   Navigate to: `http://localhost:8080`

5. **Start Learning!**
   - Select your target language
   - Choose a scenario (restaurant, directions, etc.)
   - Click and hold the microphone to speak, or type your message

## Manual Setup (Without Docker)

### Prerequisites
- Python 3.11+
- pip
- ffmpeg
- 8GB+ RAM

### Steps

1. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Download Models**
   ```bash
   python3 scripts/download_models.py
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

4. **Start Backend**
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. **Serve Frontend**
   
   In a new terminal:
   ```bash
   python3 -m http.server 8080 --directory frontend
   ```

6. **Open Browser**
   
   Navigate to: `http://localhost:8080`

## Hardware-Specific Configuration

### OrangePi 6 (32GB RAM, NPU)

Use the CPU-optimized configuration:

```bash
docker-compose -f docker-compose.cpu.yml up
```

**Recommended settings in `.env`:**
```bash
DEVICE=cpu
COMPUTE_TYPE=int8
STT_MODEL=base
LLM_MODEL=qwen2.5-1.5b-instruct
```

**Expected Performance:**
- STT Latency: 1-3 seconds
- LLM Response: 2-5 seconds
- TTS Latency: <500ms
- Total: 3-8 seconds per turn

### NVIDIA RTX 3090 (24GB VRAM)

Use the GPU-accelerated configuration:

```bash
docker-compose -f docker-compose.gpu.yml up
```

**Recommended settings in `.env`:**
```bash
DEVICE=cuda
COMPUTE_TYPE=float16
STT_MODEL=medium
LLM_MODEL=qwen2.5-3b-instruct
```

**Expected Performance:**
- STT Latency: 0.5-2 seconds
- LLM Response: 0.5-2 seconds
- TTS Latency: <200ms
- Total: 1-4 seconds per turn

### Standard CPU (8GB+ RAM)

Use the CPU configuration with lighter models:

```bash
docker-compose -f docker-compose.cpu.yml up
```

**Recommended settings:**
```bash
DEVICE=cpu
COMPUTE_TYPE=int8
STT_MODEL=base
LLM_MODEL=qwen2.5-0.5b-instruct
```

## Downloading Additional Models

### Different Whisper Models

Whisper models are downloaded automatically on first use. Sizes:
- `tiny`: 39MB (fastest, less accurate)
- `base`: 74MB (good balance)
- `small`: 244MB (recommended)
- `medium`: 769MB (very good)
- `large-v3`: 1.5GB (best accuracy)

Change in `.env`:
```bash
STT_MODEL=base
```

### Additional TTS Voices

Download voices for other languages:

```bash
python3 scripts/download_models.py --tts-voice es_ES-davefx-medium
```

Available voices:
- Spanish: `es_ES-davefx-medium`, `es_MX-ald-medium`
- French: `fr_FR-siwis-medium`
- German: `de_DE-thorsten-medium`
- Italian: `it_IT-riccardo-medium`
- Portuguese: `pt_BR-faber-medium`
- Japanese: `ja_JP-kokoro-medium`
- And many more...

Browse all voices: https://github.com/rhasspy/piper/blob/master/VOICES.md

### Different LLM Models

Download alternative language models:

```bash
# Smaller, faster model
python3 scripts/download_models.py --llm-model qwen2.5-0.5b-instruct

# Larger, better quality model
python3 scripts/download_models.py --llm-model qwen2.5-3b-instruct
```

You can also manually download GGUF models from Hugging Face:
1. Visit: https://huggingface.co/models?library=gguf
2. Search for models (Qwen, Llama, Phi, etc.)
3. Download `.gguf` files to `models/llm/` directory

## Troubleshooting

### Models Not Loading

**Problem:** API shows models as "not_loaded"

**Solutions:**
1. Verify models are downloaded:
   ```bash
   ls -lh models/stt/
   ls -lh models/tts/
   ls -lh models/llm/
   ```

2. Check Docker volume mounting:
   ```bash
   docker-compose down
   docker-compose up
   ```

3. Check logs:
   ```bash
   docker-compose logs -f
   ```

### Out of Memory

**Problem:** Container crashes or system freezes

**Solutions:**
1. Use smaller models in `.env`:
   ```bash
   STT_MODEL=tiny
   LLM_MODEL=qwen2.5-0.5b-instruct
   ```

2. Reduce resource limits in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```

3. Close other applications to free RAM

### Microphone Not Working

**Problem:** Browser doesn't access microphone

**Solutions:**
1. Grant microphone permissions in browser
2. Use HTTPS or localhost (required by browsers)
3. Check browser console for errors (F12)

### Slow Performance

**Problem:** Responses take too long (>5 seconds)

**Diagnosis:**
Check timing logs to identify the bottleneck:
```bash
docker-compose logs backend | grep "\[TIMING\]"
```

Look for the breakdown:
```
[TIMING] Breakdown - Read: X.XXXs, Write: X.XXXs, STT: X.XXXs, Context: X.XXXs, LLM: X.XXXs
```

**Solutions:**

1. **If LLM is slow (>5s):**
   - **Check GPU usage**: Ensure LLM is using GPU (see "GPU Not Detected" above)
   - **Use smaller model**: `LLM_MODEL=qwen2.5-1.5b-instruct` instead of 3b
   - **Use quantized model**: Download Q4_K_M or Q2_K GGUF models
   - **Reduce context**: Context window is already optimized to 512 tokens

2. **If STT is slow (>2s):**
   - Use smaller Whisper model: `STT_MODEL=base` or `small`
   - Reduce audio length: Speak shorter phrases

3. **General optimizations:**
   - Enable GPU if available: `DEVICE=cuda`
   - Use appropriate model sizes for your hardware (see Performance Tuning section)
   - Check system resources: `docker stats` and `nvidia-smi`

### GPU Not Detected or LLM Running on CPU

**Problem:** CUDA errors, GPU not used, or LLM is very slow (4-5 chunks/sec instead of 50-100/sec)

**Symptoms:**
- LLM first token takes 5+ seconds (should be 0.1-0.5s)
- LLM generation rate is 3-5 chunks/sec (should be 50-100/sec)
- Logs show: "Could not find nvcc" or "cuBLAS not found"

**Solutions:**

1. **Install NVIDIA Docker runtime:**
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

2. **Verify GPU access:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```

3. **Rebuild Docker image with CUDA support:**
   
   The GPU Dockerfile must use `nvidia/cuda:12.1.0-devel-ubuntu22.04` (not `runtime`) to compile `llama-cpp-python` with CUDA support. If you're experiencing slow LLM performance:
   
   ```bash
   # Rebuild with CUDA support (takes 5-10 minutes)
   docker-compose -f docker-compose.gpu.yml build --no-cache
   
   # Start the container
   docker-compose -f docker-compose.gpu.yml up
   ```
   
   The Dockerfile should include:
   ```dockerfile
   FROM nvidia/cuda:12.1.0-devel-ubuntu22.04  # devel, not runtime!
   RUN apt-get install cmake ...  # Required for CUDA builds
   CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip3 install llama-cpp-python
   ```

4. **Verify GPU usage:**
   ```bash
   # Check GPU utilization during inference
   watch -n 1 nvidia-smi
   # Should see 80-100% GPU utilization during LLM generation
   ```

## Updating

### Update Code

```bash
git pull
docker-compose down
docker-compose build
docker-compose up
```

### Update Models

```bash
python3 scripts/download_models.py --all
```

## Development Mode

For development with hot-reload:

1. **Install dependencies locally:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run backend with reload:**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Serve frontend:**
   ```bash
   python3 -m http.server 8080 --directory frontend
   ```

4. **Edit code:**
   - Backend: `backend/app/`
   - Frontend: `frontend/`
   
   Changes will be reflected automatically.

## Configuration Reference

See `.env.example` for all available configuration options.

Key settings:
- `DEVICE`: Hardware to use (cpu, cuda, auto)
- `STT_MODEL`: Whisper model size
- `LLM_MODEL`: Language model name
- `TTS_VOICE`: Text-to-speech voice
- `SUPPORTED_LANGUAGES`: Languages to enable
- `MAX_AUDIO_LENGTH`: Maximum recording length (seconds)

## Performance Tuning

### Expected Performance

**RTX 3090 (GPU):**
- STT: 0.5-1s (Whisper medium)
- LLM First Token: 0.1-0.5s (Qwen 3B)
- LLM Generation: 50-100 tokens/sec
- TTS: 0.2s
- **Total: 1-3s per conversation turn**

**CPU Only:**
- STT: 1-3s (Whisper base/small)
- LLM First Token: 0.5-2s (Qwen 1.5B)
- LLM Generation: 10-30 tokens/sec
- TTS: 0.5s
- **Total: 3-8s per conversation turn**

### For Speed
- Use smaller models (tiny/base for STT, 0.5b/1.5b for LLM)
- Set `COMPUTE_TYPE=int8` (CPU) or `float16` (GPU)
- Ensure GPU is properly configured (see GPU troubleshooting)
- Use quantized GGUF models (Q4_K_M, Q2_K)

### For Quality
- Use larger models (medium/large for STT, 3b/7b for LLM)
- Set `COMPUTE_TYPE=float16` (GPU)
- Use GPU acceleration
- Context window is optimized to 512 tokens (good balance)

### For Memory Efficiency
- Use quantized models (Q4_K_M, Q5_K_M)
- Set `CACHE_MODELS=false` (not recommended - models stay hot for better performance)
- Use smaller STT models
- Limit concurrent users

### Streaming Performance

The app uses **streaming responses** by default:
- **Token-by-token display** - responses appear in real-time
- **Models stay hot in memory** - no re-initialization overhead
- **3-5x faster perceived latency** - first token appears quickly

No configuration needed - streaming is enabled automatically.

## Next Steps

- Try different scenarios and difficulty levels
- Practice with different languages
- Adjust settings for your hardware
- Contribute improvements!

## Getting Help

- Check logs: `docker-compose logs -f`
- Review API docs: `http://localhost:8080/docs`
- Report issues on GitHub
- Read the main README.md for architecture details
