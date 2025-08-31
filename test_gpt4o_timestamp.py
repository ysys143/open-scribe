#!/usr/bin/env python3
"""
Test if gpt-4o-mini-transcribe can support timestamps through various approaches
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_timestamp_support():
    """Test different approaches to get timestamps from gpt-4o-mini-transcribe"""
    
    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Test audio file - use a small sample
    test_audio = "/Users/jaesolshin/Documents/GitHub/yt-trans/audio/sample.mp3"
    
    # Check if test file exists, if not create a small one
    if not os.path.exists(test_audio):
        print(f"Test audio file not found: {test_audio}")
        print("Please provide a small test audio file")
        return
    
    print("Testing timestamp support for gpt-4o-mini-transcribe model...")
    print("=" * 60)
    
    # Test 1: Try verbose_json format (expected to fail based on documentation)
    print("\nTest 1: verbose_json format")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="verbose_json"
            )
        print(f"✓ Success! Response type: {type(response)}")
        if hasattr(response, 'segments'):
            print(f"  Has segments: Yes ({len(response.segments)} segments)")
            for i, seg in enumerate(response.segments[:3]):
                print(f"  Segment {i}: start={seg.start}, text={seg.text[:50]}...")
        else:
            print(f"  Has segments: No")
            print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 2: Try json format
    print("\nTest 2: json format")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="json"
            )
        print(f"✓ Success! Response type: {type(response)}")
        print(f"  Response keys: {list(response.__dict__.keys()) if hasattr(response, '__dict__') else 'N/A'}")
        print(f"  Text length: {len(response.text) if hasattr(response, 'text') else 'N/A'}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 3: Try srt format (subtitle format with timestamps)
    print("\nTest 3: srt format")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="srt"
            )
        print(f"✓ Success! Response type: {type(response)}")
        if isinstance(response, str):
            lines = response.split('\n')[:10]
            print("  First few lines:")
            for line in lines:
                print(f"    {line}")
        else:
            print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 4: Try vtt format (WebVTT subtitle format)
    print("\nTest 4: vtt format")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="vtt"
            )
        print(f"✓ Success! Response type: {type(response)}")
        if isinstance(response, str):
            lines = response.split('\n')[:10]
            print("  First few lines:")
            for line in lines:
                print(f"    {line}")
        else:
            print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 5: Try with timestamp_granularities parameter (new in 2025?)
    print("\nTest 5: timestamp_granularities parameter")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="json",
                timestamp_granularities=["segment", "word"]  # Try new parameter
            )
        print(f"✓ Success! Response type: {type(response)}")
        print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 6: Compare with whisper-1 model
    print("\nTest 6: whisper-1 with verbose_json (baseline)")
    print("-" * 40)
    try:
        with open(test_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        print(f"✓ Success! Response type: {type(response)}")
        if hasattr(response, 'segments'):
            print(f"  Has segments: Yes ({len(response.segments)} segments)")
            for i, seg in enumerate(response.segments[:3]):
                print(f"  Segment {i}: start={seg.start:.2f}s, text={seg.text[:50]}...")
        else:
            print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    
    # Summary and recommendations
    print("\n## Summary and Recommendations:")
    print("-" * 40)
    print("""
Based on the test results above, here are potential approaches for timestamps with gpt-4o-mini-transcribe:

1. **SRT/VTT Format**: If these formats work, they provide timestamps but require parsing
   - SRT: Standard subtitle format with timestamps
   - VTT: WebVTT format, similar to SRT but with more features

2. **Chunked Processing**: Split audio into fixed-duration chunks
   - Process each chunk separately
   - Track time offsets manually
   - Merge results with calculated timestamps

3. **Hybrid Approach**: Use whisper-1 for timestamps, gpt-4o-mini for quality
   - Get timestamps from whisper-1 verbose_json
   - Get high-quality text from gpt-4o-mini
   - Align the two using text matching algorithms

4. **Real-time API**: Use the new WebSocket-based real-time API
   - Stream audio in chunks
   - Receive transcriptions with timing information
   - More complex but provides real-time timestamps
    """)

if __name__ == "__main__":
    test_timestamp_support()