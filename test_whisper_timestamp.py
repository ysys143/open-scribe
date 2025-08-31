#!/usr/bin/env python
"""Test whisper-cpp timestamp functionality"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from transcribers.whisper_cpp import WhisperCppTranscriber

# Test with a chunk file
chunk_file = "/Users/jaesolshin/Documents/GitHub/yt-trans/temp_audio/chunk_000.mp3"

if not os.path.exists(chunk_file):
    print(f"Chunk file not found: {chunk_file}")
    print("Creating a test chunk first...")
    from downloader import YouTubeDownloader
    
    config = Config()
    downloader = YouTubeDownloader(config)
    
    # Download just 30 seconds
    url = "https://youtu.be/mkiBMXdE0ew"
    audio_file = downloader.download_audio(url, chunk_duration=30)
    if audio_file:
        chunk_file = "/Users/jaesolshin/Documents/GitHub/yt-trans/temp_audio/chunk_000.mp3"

config = Config()
transcriber = WhisperCppTranscriber(config)

print(f"Testing whisper-cpp with file: {chunk_file}")
print(f"Model: {transcriber.model_path}")
print(f"Executable: {transcriber.executable_path}")
print()

# Test without timestamps
print("=" * 60)
print("TEST 1: Without timestamps")
print("=" * 60)
result = transcriber.transcribe(chunk_file, return_timestamps=False)
if result:
    print("Success!")
    print(f"Length: {len(result)} chars")
    print(f"First 300 chars:\n{result[:300]}")
else:
    print("Failed!")

print()

# Test with timestamps
print("=" * 60)
print("TEST 2: With timestamps")
print("=" * 60)
result = transcriber.transcribe(chunk_file, return_timestamps=True)
if result:
    print("Success!")
    print(f"Length: {len(result)} chars")
    print(f"First 500 chars:\n{result[:500]}")
    
    # Check if timestamps are present
    if '[' in result and ']' in result:
        print("\n✅ Timestamps detected in output!")
    else:
        print("\n❌ No timestamps found in output!")
else:
    print("Failed!")