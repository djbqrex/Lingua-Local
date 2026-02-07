# Docker Build Notes

## PyAV (av) Dependency Issue - RESOLVED

### The Problem

The build was failing with errors like:
```
error: 'AV_OPT_TYPE_CHANNEL_LAYOUT' undeclared
ERROR: Failed to build 'av' when getting requirements to build wheel
```

### Root Cause

1. **`faster-whisper==1.0.0` requires `av==11.*`** (PyAV) as a dependency
2. **PyAV 11.x is incompatible with modern FFmpeg** versions (FFmpeg 5.x/6.x)
3. The FFmpeg in `python:3.11-slim` uses a newer API that PyAV 11.x doesn't support

### The Solution

We upgraded `faster-whisper` to a version that uses a compatible `av` version:

1. **Upgraded `faster-whisper` from 1.0.0 to >=1.0.3** - newer versions use av>=13.0.0
2. **Added FFmpeg development libraries** back to Dockerfile (required for PyAV to build)
3. **Kept `pydub` separate** with `--no-deps` (it doesn't need PyAV, just ffmpeg CLI)

### Files Modified

- `backend/Dockerfile` - Uses `requirements.docker.txt` and av constraint
- `backend/Dockerfile.gpu` - Same fix for GPU builds
- `backend/requirements.docker.txt` - Docker-specific requirements without pydub
- `backend/requirements.txt` - Original file, pydub commented out for local dev clarity

### Build Command

```bash
make build-image
```

or manually:

```bash
docker build -t lingua-local:cpu -f backend/Dockerfile .
```

### Why This Works

- PyAV 13.0.0+ supports the modern FFmpeg API
- `faster-whisper` 1.0.3+ natively uses av>=13.0.0 (no version conflicts)
- The FFmpeg dev libraries allow PyAV to build successfully

### After Building

Once the image is built, `docker-compose up` will use the cached image and won't rebuild or download packages every time you start the container.

### If Build Still Fails

If av 13.0.0 still has build issues, try:

1. **Use a pre-built wheel:**
   ```bash
   pip install --only-binary=:all: "av>=13.0.0"
   ```

2. **Upgrade faster-whisper** to a newer version that might have relaxed av requirements

3. **Use a different base image** like `python:3.11-bullseye` which may have different FFmpeg versions

