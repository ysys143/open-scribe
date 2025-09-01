#!/usr/bin/env python
"""Test whisper.cpp progress bar"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.transcribers.whisper_cpp import WhisperCppTranscriber

def test_progress():
    config = Config()
    transcriber = WhisperCppTranscriber(config)
    
    # Use a test file
    test_file = "/Users/jaesolshin/Documents/GitHub/yt-trans/audio/테스트 코드와 TDD 🧪(feat. 프론트엔드, 백엔드를 위한 테스트 코드) [Npi21gLIEZM].mp3"
    
    if not Path(test_file).exists():
        print("Test file not found")
        return
    
    print("Testing whisper.cpp progress bar...")
    print("=" * 60)
    
    result = transcriber.transcribe(test_file, stream=False, return_timestamps=False)
    
    if result:
        print("\n" + "=" * 60)
        print(f"Success! Transcribed {len(result)} characters")
        print(f"First 100 chars: {result[:100]}...")
    else:
        print("\nTranscription failed")

if __name__ == "__main__":
    test_progress()