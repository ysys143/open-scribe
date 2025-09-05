#!/usr/bin/env python3
"""Test TUI components"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all TUI modules can be imported"""
    try:
        from src.tui.app import YouTubeTranscriberTUI
        print("✓ Main TUI app imports successfully")
        
        from src.tui.screens.main_menu import MainMenuScreen
        print("✓ Main menu screen imports successfully")
        
        from src.tui.screens.transcribe_screen import TranscribeScreen
        print("✓ Transcribe screen imports successfully")
        
        print("\nAll TUI modules imported successfully!")
        print("You can run the TUI with: python tui.py")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)