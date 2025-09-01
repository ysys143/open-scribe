#!/usr/bin/env python
"""Test 2-level progress display"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.transcribers.openai import GPT4OMiniTranscriber

def test_parallel_progress():
    """Test parallel processing with 2-level progress"""
    # Setup config
    config = Config()
    
    # Create transcriber
    transcriber = GPT4OMiniTranscriber(config)
    
    # Test URL (short video for testing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("Testing 2-level progress display with parallel processing...")
    print("=" * 60)
    
    # Create a test audio file path (would normally be downloaded)
    test_audio = "/Users/jaesolshin/Documents/GitHub/yt-trans/audio/test.mp3"
    
    if not Path(test_audio).exists():
        print(f"Test audio file not found: {test_audio}")
        print("Please provide a test audio file or YouTube URL")
        return
    
    # Test with chunking forced
    result = transcriber.transcribe(
        test_audio,
        stream=False,
        return_timestamps=True  # This forces chunking for GPT-4o models
    )
    
    if result:
        print("\n" + "=" * 60)
        print("Transcription successful!")
        print(f"Result length: {len(result)} characters")
        print("First 200 chars:")
        print(result[:200])
    else:
        print("\nTranscription failed")

if __name__ == "__main__":
    test_parallel_progress()