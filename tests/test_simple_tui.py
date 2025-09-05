#!/usr/bin/env python3
"""Test simplified TUI input functionality"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_simple_tui():
    """Test that simple TUI can be imported"""
    try:
        from src.tui.app import YouTubeTranscriberTUI
        from src.tui.screens.simple_transcribe import SimpleTranscribeScreen
        
        print("✓ Simple TUI components imported successfully")
        print("\nTo test the TUI with working Input field:")
        print("1. Run: source .venv/bin/activate")
        print("2. Run: python tui.py")
        print("3. Press '1' to go to Transcribe screen")
        print("4. The Input field should now be active")
        print("5. Try typing or pasting (Ctrl+V) a YouTube URL")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_tui()
    sys.exit(0 if success else 1)