#!/usr/bin/env python3
"""
Validation script to check if the project is set up correctly.
"""

import sys
from pathlib import Path

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists."""
    if path.exists():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} not found: {path}")
        return False

def check_directory_exists(path: Path, description: str) -> bool:
    """Check if a directory exists."""
    if path.exists() and path.is_dir():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description} not found: {path}")
        return False

def main():
    print("=" * 60)
    print("Language Learning Assistant - Setup Validation")
    print("=" * 60)
    print()

    base_dir = Path(__file__).parent.parent
    checks = []

    print("Checking project structure...")
    print("-" * 60)

    # Backend
    checks.append(check_directory_exists(base_dir / "backend", "Backend directory"))
    checks.append(check_file_exists(base_dir / "backend" / "requirements.txt", "Requirements file"))
    checks.append(check_file_exists(base_dir / "backend" / "Dockerfile", "Dockerfile"))
    checks.append(check_directory_exists(base_dir / "backend" / "app", "Backend app directory"))
    
    # Frontend
    checks.append(check_directory_exists(base_dir / "frontend", "Frontend directory"))
    checks.append(check_file_exists(base_dir / "frontend" / "index.html", "Frontend HTML"))
    checks.append(check_file_exists(base_dir / "frontend" / "css" / "style.css", "Frontend CSS"))
    checks.append(check_file_exists(base_dir / "frontend" / "js" / "app.js", "Frontend JavaScript"))

    # Scripts
    checks.append(check_directory_exists(base_dir / "scripts", "Scripts directory"))
    checks.append(check_file_exists(base_dir / "scripts" / "download_models.py", "Model download script"))

    # Docker
    checks.append(check_file_exists(base_dir / "docker-compose.yml", "Docker Compose"))
    checks.append(check_file_exists(base_dir / "docker-compose.cpu.yml", "Docker Compose CPU"))
    checks.append(check_file_exists(base_dir / "docker-compose.gpu.yml", "Docker Compose GPU"))

    # Documentation
    checks.append(check_file_exists(base_dir / "README.md", "README"))
    checks.append(check_file_exists(base_dir / "SETUP.md", "Setup guide"))
    checks.append(check_file_exists(base_dir / ".env.example", "Environment example"))

    print()
    print("Checking model directories...")
    print("-" * 60)

    models_dir = base_dir / "models"
    if models_dir.exists():
        print(f"✓ Models directory exists: {models_dir}")
        
        stt_dir = models_dir / "stt"
        tts_dir = models_dir / "tts"
        llm_dir = models_dir / "llm"
        
        check_directory_exists(stt_dir, "STT models directory")
        check_directory_exists(tts_dir, "TTS models directory")
        check_directory_exists(llm_dir, "LLM models directory")

        # Check for actual model files
        stt_files = list(stt_dir.glob("*")) if stt_dir.exists() else []
        tts_files = list(tts_dir.glob("*.onnx")) if tts_dir.exists() else []
        llm_files = list(llm_dir.glob("*.gguf")) if llm_dir.exists() else []

        if stt_files:
            print(f"  → STT files: {len(stt_files)}")
        else:
            print(f"  ⚠ No STT models found (will download on first use)")

        if tts_files:
            print(f"  → TTS voices: {len(tts_files)}")
        else:
            print(f"  ⚠ No TTS voices found. Run: python3 scripts/download_models.py")

        if llm_files:
            print(f"  → LLM models: {len(llm_files)}")
        else:
            print(f"  ⚠ No LLM models found. Run: python3 scripts/download_models.py")
    else:
        print(f"✗ Models directory not found: {models_dir}")
        print(f"  Creating models directory...")
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / "stt").mkdir(exist_ok=True)
        (models_dir / "tts").mkdir(exist_ok=True)
        (models_dir / "llm").mkdir(exist_ok=True)
        print(f"  ✓ Created models directories")

    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)

    print(f"Passed: {passed}/{total} checks")
    print()

    if passed == total:
        print("✓ Project structure is valid!")
        print()
        print("Next steps:")
        print("1. Download models: python3 scripts/download_models.py")
        print("2. Start application: docker-compose up")
        print("3. Open browser: http://localhost:8080")
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
