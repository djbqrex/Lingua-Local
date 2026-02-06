#!/usr/bin/env python3
"""
Simple structure check that doesn't require dependencies.
"""

import sys
from pathlib import Path

def check_python_files():
    """Check that all Python files have valid syntax."""
    print("Checking Python file syntax...")
    
    base_dir = Path(__file__).parent.parent
    python_files = []
    
    # Collect Python files
    for pattern in ["backend/app/*.py", "backend/app/*/*.py", "scripts/*.py"]:
        python_files.extend(base_dir.glob(pattern))
    
    errors = []
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"✓ {py_file.relative_to(base_dir)}")
        except SyntaxError as e:
            errors.append((py_file, e))
            print(f"✗ {py_file.relative_to(base_dir)}: {e}")
    
    return len(errors) == 0

def check_required_files():
    """Check that all required files exist."""
    print("\nChecking required files...")
    
    base_dir = Path(__file__).parent.parent
    required_files = [
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/models/__init__.py",
        "backend/app/models/stt.py",
        "backend/app/models/tts.py",
        "backend/app/models/llm.py",
        "backend/app/routes/__init__.py",
        "backend/app/routes/health.py",
        "backend/app/routes/conversation.py",
        "backend/app/utils/__init__.py",
        "backend/app/utils/audio.py",
        "backend/app/utils/language.py",
        "frontend/index.html",
        "frontend/css/style.css",
        "frontend/js/app.js",
        "frontend/js/api.js",
        "frontend/js/audio.js",
        "docker-compose.yml",
        "docker-compose.cpu.yml",
        "docker-compose.gpu.yml",
        ".env.example",
        "README.md",
        "SETUP.md",
        "QUICKSTART.md",
    ]
    
    missing = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            missing.append(file_path)
            print(f"✗ {file_path}")
    
    return len(missing) == 0

def check_javascript_files():
    """Basic check for JavaScript files."""
    print("\nChecking JavaScript files...")
    
    base_dir = Path(__file__).parent.parent
    js_files = list(base_dir.glob("frontend/js/*.js"))
    
    for js_file in js_files:
        # Basic check: ensure file is not empty and has some content
        content = js_file.read_text()
        if len(content) > 100:  # Reasonable minimum
            print(f"✓ {js_file.relative_to(base_dir)} ({len(content)} bytes)")
        else:
            print(f"⚠ {js_file.relative_to(base_dir)} seems too small")
    
    return len(js_files) > 0

def main():
    print("=" * 60)
    print("Language Learning Assistant - Structure Check")
    print("=" * 60)
    print()
    
    checks = []
    checks.append(("Required Files", check_required_files()))
    checks.append(("Python Syntax", check_python_files()))
    checks.append(("JavaScript Files", check_javascript_files()))
    
    print()
    print("=" * 60)
    print("Check Summary")
    print("=" * 60)
    
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    
    if all(result for _, result in checks):
        print("✓ All structure checks passed!")
        print()
        print("Next steps:")
        print("1. Validate setup: python3 scripts/validate_setup.py")
        print("2. Download models: python3 scripts/download_models.py")
        print("3. Start application: docker-compose up")
        return 0
    else:
        print("✗ Some checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
