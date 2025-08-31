#!/usr/bin/env python
"""
Test script for timestamp functionality with different OpenAI models
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_timestamp_with_whisper():
    """Test if whisper-1 model supports verbose_json for timestamps"""
    from openai import OpenAI
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Find a small test audio file
    audio_dir = Path(__file__).parent / "audio"
    test_files = list(audio_dir.glob("*.mp3"))[:1]  # Get first mp3 file
    
    if not test_files:
        print("No test audio files found")
        return
    
    test_file = test_files[0]
    print(f"Testing with file: {test_file.name}")
    print(f"File size: {test_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Test 1: whisper-1 with text format
    print("\n=== Test 1: whisper-1 with text format ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        print(f"Success! Type: {type(result)}")
        if isinstance(result, str):
            print(f"Text length: {len(result)} chars")
            print(f"First 100 chars: {result[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: whisper-1 with verbose_json format
    print("\n=== Test 2: whisper-1 with verbose_json format ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        print(f"Success! Type: {type(result)}")
        if hasattr(result, 'segments'):
            print(f"Has segments: {len(result.segments)} segments")
            if result.segments:
                first_seg = result.segments[0]
                print(f"First segment: start={first_seg.start}, text={first_seg.text[:50]}...")
        if hasattr(result, 'text'):
            print(f"Has text: {len(result.text)} chars")
    except Exception as e:
        print(f"Error: {e}")


def test_timestamp_with_gpt4o():
    """Test what formats GPT-4o models support"""
    from openai import OpenAI
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Find a small test audio file
    audio_dir = Path(__file__).parent / "audio"
    test_files = list(audio_dir.glob("*.mp3"))[:1]
    
    if not test_files:
        print("No test audio files found")
        return
    
    test_file = test_files[0]
    print(f"Testing with file: {test_file.name}")
    
    # Test 3: gpt-4o-mini-transcribe with text
    print("\n=== Test 3: gpt-4o-mini-transcribe with text ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="text"
            )
        print(f"Success! Type: {type(result)}")
        if isinstance(result, str):
            print(f"Text length: {len(result)} chars")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: gpt-4o-mini-transcribe with json
    print("\n=== Test 4: gpt-4o-mini-transcribe with json ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="json"
            )
        print(f"Success! Type: {type(result)}")
        if hasattr(result, '__dict__'):
            print(f"Attributes: {list(result.__dict__.keys())}")
        if hasattr(result, 'text'):
            print(f"Has text: {len(result.text)} chars")
        if hasattr(result, 'segments'):
            print(f"Has segments: Yes")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: gpt-4o-mini-transcribe with verbose_json (expected to fail)
    print("\n=== Test 5: gpt-4o-mini-transcribe with verbose_json (expected to fail) ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="verbose_json"
            )
        print(f"Unexpected success! Type: {type(result)}")
    except Exception as e:
        print(f"Expected error: {e}")


def test_json_format_details():
    """Test what the json format actually returns"""
    from openai import OpenAI
    import json
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Create a very short test audio
    audio_dir = Path(__file__).parent / "audio"
    test_files = list(audio_dir.glob("*.mp3"))[:1]
    
    if not test_files:
        print("No test audio files found")
        return
    
    test_file = test_files[0]
    
    print("\n=== Detailed JSON format test ===")
    try:
        with open(test_file, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="json"
            )
        
        print(f"Result type: {type(result)}")
        print(f"Result class: {result.__class__.__name__}")
        
        # Try to get the raw data
        if hasattr(result, 'model_dump'):
            data = result.model_dump()
            print(f"\nmodel_dump() keys: {list(data.keys())}")
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: (string, {len(value)} chars)")
                elif isinstance(value, list):
                    print(f"  {key}: (list, {len(value)} items)")
                else:
                    print(f"  {key}: {value}")
        
        # Check for specific attributes
        for attr in ['text', 'segments', 'language', 'duration', 'words']:
            if hasattr(result, attr):
                val = getattr(result, attr)
                if val is not None:
                    if isinstance(val, str):
                        print(f"\n{attr}: (exists, {len(val)} chars)")
                    elif isinstance(val, list):
                        print(f"\n{attr}: (exists, {len(val)} items)")
                        if val and attr == 'segments':
                            print(f"  First segment: {val[0]}")
                    else:
                        print(f"\n{attr}: {val}")
                        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("OPENAI TRANSCRIPTION FORMAT TEST")
    print("=" * 60)
    
    # Test whisper-1 model
    test_timestamp_with_whisper()
    
    # Test GPT-4o models
    test_timestamp_with_gpt4o()
    
    # Test json format details
    test_json_format_details()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)