#!/usr/bin/env python3
"""
Test GPT-4o timestamp implementation with actual transcriber
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.transcribers.openai import GPT4OMiniTranscriber, WhisperAPITranscriber

def test_timestamp_implementation():
    """Test the timestamp implementation for GPT-4o models"""
    
    # Create config
    config = Config()
    
    # Test audio file - use a small one
    test_audio = "audio/A quick trick for computing eigenvalues ｜ Chapter 15, Essence of linear algebra [e50Bj7jn9IQ].mp3"
    
    if not os.path.exists(test_audio):
        print(f"Test file not found: {test_audio}")
        print("Available files:")
        for f in os.listdir("audio")[:5]:
            print(f"  - {f}")
        return
    
    print("=" * 60)
    print("Testing GPT-4o-mini Timestamp Implementation")
    print("=" * 60)
    
    # Test 1: GPT-4o-mini with timestamps
    print("\n1. GPT-4o-mini with timestamps (chunked approach):")
    print("-" * 40)
    
    transcriber = GPT4OMiniTranscriber(config)
    if transcriber.is_available():
        result = transcriber.transcribe(
            test_audio,
            stream=False,
            return_timestamps=True
        )
        
        if result:
            lines = result.split('\n')[:5]  # Show first 5 lines
            print("First 5 lines of transcription:")
            for line in lines:
                print(f"  {line[:100]}...")  # Truncate long lines
            print(f"\nTotal lines: {len(result.split(chr(10)))}")
            print(f"Total length: {len(result)} characters")
        else:
            print("Transcription failed")
    else:
        print("GPT-4o-mini not available (API key missing)")
    
    # Test 2: Compare with Whisper API
    print("\n2. Whisper API with timestamps (native support):")
    print("-" * 40)
    
    whisper_transcriber = WhisperAPITranscriber(config)
    if whisper_transcriber.is_available():
        result = whisper_transcriber.transcribe(
            test_audio,
            stream=False,
            return_timestamps=True
        )
        
        if result:
            lines = result.split('\n')[:5]  # Show first 5 lines
            print("First 5 lines of transcription:")
            for line in lines:
                print(f"  {line[:100]}...")
            print(f"\nTotal lines: {len(result.split(chr(10)))}")
            print(f"Total length: {len(result)} characters")
        else:
            print("Transcription failed")
    else:
        print("Whisper API not available")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("\nSummary:")
    print("- GPT-4o models now support timestamps via chunking")
    print("- Each chunk gets a timestamp based on its position")
    print("- Default chunk size: 30 seconds for timestamps")
    print("- Whisper still uses native segment-based timestamps")

if __name__ == "__main__":
    test_timestamp_implementation()