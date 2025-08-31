#!/usr/bin/env python
"""
Test suite for the refactored transcriber system
Verifies that all transcribers have a unified interface and work correctly
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.transcribers.openai import WhisperAPITranscriber, GPT4OTranscriber, GPT4OMiniTranscriber
from src.transcribers.youtube import YouTubeTranscriptAPITranscriber
from src.config import Config


def test_transcriber_interface(transcriber_class, name):
    """Test that a transcriber implements the required interface"""
    print(f"\n=== Testing {name} ===")
    
    # Create config
    config = Config()
    
    # Create transcriber
    transcriber = transcriber_class(config)
    
    # Test required properties
    assert hasattr(transcriber, 'name'), f"{name} missing 'name' property"
    assert hasattr(transcriber, 'requires_api_key'), f"{name} missing 'requires_api_key' property"
    
    # Test required methods
    assert hasattr(transcriber, 'is_available'), f"{name} missing 'is_available' method"
    assert hasattr(transcriber, 'transcribe'), f"{name} missing 'transcribe' method"
    assert hasattr(transcriber, 'validate_audio_file'), f"{name} missing 'validate_audio_file' method"
    
    # Test transcribe signature
    import inspect
    sig = inspect.signature(transcriber.transcribe)
    params = list(sig.parameters.keys())
    
    assert 'audio_path' in params, f"{name}.transcribe missing 'audio_path' parameter"
    assert 'stream' in params, f"{name}.transcribe missing 'stream' parameter"
    assert 'return_timestamps' in params, f"{name}.transcribe missing 'return_timestamps' parameter"
    
    print(f"✓ {name} has correct interface")
    print(f"  - name: {transcriber.name}")
    print(f"  - requires_api_key: {transcriber.requires_api_key}")
    print(f"  - is_available: {transcriber.is_available()}")
    
    return True


def test_error_handling():
    """Test error handling in transcribers"""
    print("\n=== Testing Error Handling ===")
    
    # Test with no API key
    class NoKeyConfig:
        OPENAI_API_KEY = None
    
    config = NoKeyConfig()
    transcriber = WhisperAPITranscriber(config)
    
    # Should return None for missing API key
    result = transcriber.transcribe('/nonexistent/file.mp3')
    assert result is None, "Should return None when API key is missing"
    print("✓ Returns None when API key is missing")
    
    # Test with invalid file
    config = Config()
    if config.OPENAI_API_KEY:
        transcriber = WhisperAPITranscriber(config)
        result = transcriber.transcribe('/nonexistent/file.mp3')
        assert result is None, "Should return None for non-existent file"
        print("✓ Returns None for non-existent file")
    
    return True


def test_model_names():
    """Test that model names are correct"""
    print("\n=== Testing Model Names ===")
    
    config = Config()
    
    # Test Whisper API
    whisper = WhisperAPITranscriber(config)
    assert whisper.model_name == "whisper-1", "Whisper API should use 'whisper-1' model"
    print(f"✓ Whisper API model: {whisper.model_name}")
    
    # Test GPT-4o
    gpt4o = GPT4OTranscriber(config)
    assert gpt4o.model_name == "gpt-4o-transcribe", "GPT-4o should use 'gpt-4o-transcribe' model"
    print(f"✓ GPT-4o model: {gpt4o.model_name}")
    
    # Test GPT-4o-mini
    gpt4o_mini = GPT4OMiniTranscriber(config)
    assert gpt4o_mini.model_name == "gpt-4o-mini-transcribe", "GPT-4o-mini should use 'gpt-4o-mini-transcribe' model"
    print(f"✓ GPT-4o-mini model: {gpt4o_mini.model_name}")
    
    return True


def test_no_dictionary_wrapping():
    """Test that transcribers don't use unnecessary dictionary wrapping"""
    print("\n=== Testing No Dictionary Wrapping ===")
    
    # Read the source code and check for dictionary patterns
    source_file = Path(__file__).parent / "src" / "transcribers" / "openai.py"
    with open(source_file, 'r') as f:
        source = f.read()
    
    # Check for problematic patterns
    bad_patterns = [
        "{'text':",
        '{"text":',
        "result = {",
        "'segments':",
    ]
    
    found_issues = []
    for pattern in bad_patterns:
        if pattern in source:
            found_issues.append(pattern)
    
    if found_issues:
        print(f"✗ Found dictionary wrapping patterns: {found_issues}")
        return False
    
    print("✓ No dictionary wrapping found in OpenAI transcriber")
    return True


def test_timestamp_support():
    """Test that all transcribers support timestamps uniformly"""
    print("\n=== Testing Timestamp Support ===")
    
    # Check that transcribe_single_chunk accepts return_timestamps
    source_file = Path(__file__).parent / "src" / "transcribers" / "openai.py"
    with open(source_file, 'r') as f:
        source = f.read()
    
    # Check for timestamp parameter in transcribe_single_chunk
    if "def transcribe_single_chunk" in source:
        if "return_timestamps" in source[source.find("def transcribe_single_chunk"):source.find("def transcribe_single_chunk") + 500]:
            print("✓ transcribe_single_chunk accepts return_timestamps parameter")
        else:
            print("✗ transcribe_single_chunk missing return_timestamps parameter")
            return False
    
    # Check for response_format logic
    if 'response_format = "verbose_json" if return_timestamps else "text"' in source:
        print("✓ Response format switches based on return_timestamps")
    else:
        print("✗ Response format doesn't switch based on return_timestamps")
        return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("TRANSCRIBER REFACTORING TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    # Test interfaces
    transcribers = [
        (WhisperAPITranscriber, "Whisper API"),
        (GPT4OTranscriber, "GPT-4o"),
        (GPT4OMiniTranscriber, "GPT-4o-mini"),
        (YouTubeTranscriptAPITranscriber, "YouTube Transcript API"),
    ]
    
    for transcriber_class, name in transcribers:
        try:
            if not test_transcriber_interface(transcriber_class, name):
                all_passed = False
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            all_passed = False
    
    # Test specific functionality
    tests = [
        test_error_handling,
        test_model_names,
        test_no_dictionary_wrapping,
        test_timestamp_support,
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test failed: {e}")
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Refactoring is complete!")
    else:
        print("❌ SOME TESTS FAILED - Please review the issues above")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())