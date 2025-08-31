#!/usr/bin/env python
"""
Test script to verify and fix timestamp and whisper-cpp issues
"""

import os
import subprocess
from pathlib import Path

# Test 1: Check current timestamp default
print("=== Test 1: Timestamp Default Settings ===")
print(f"OPEN_SCRIBE_TIMESTAMP env var: {os.getenv('OPEN_SCRIBE_TIMESTAMP', 'Not set')}")

from src.config import Config
config = Config()
print(f"Config.DEFAULT_TIMESTAMP: {config.DEFAULT_TIMESTAMP}")

# Test 2: Check if whisper-cpp is available and test encoding
print("\n=== Test 2: Whisper-cpp Configuration ===")
whisper_model = os.getenv('WHISPER_CPP_MODEL')
whisper_exe = os.getenv('WHISPER_CPP_EXECUTABLE', 'whisper')

print(f"WHISPER_CPP_MODEL: {whisper_model}")
print(f"WHISPER_CPP_EXECUTABLE: {whisper_exe}")

if whisper_model and Path(whisper_model).exists():
    print("✓ Model file exists")
else:
    print("✗ Model file not found or not configured")

# Test whisper executable
try:
    result = subprocess.run(
        [whisper_exe, '--help'],
        capture_output=True,
        text=False,  # Use bytes to avoid encoding issues
        timeout=5
    )
    if result.returncode == 0:
        print("✓ Whisper executable found")
    else:
        print("✗ Whisper executable failed")
except FileNotFoundError:
    print("✗ Whisper executable not found")
except Exception as e:
    print(f"✗ Error testing whisper: {e}")

print("\n=== Suggested Fixes ===")
print("1. To enable timestamps by default, set environment variable:")
print("   export OPEN_SCRIBE_TIMESTAMP=true")
print("   Or modify Config.DEFAULT_TIMESTAMP in config.py to True")
print("\n2. Whisper-cpp UTF-8 fix will be applied to handle binary output correctly")