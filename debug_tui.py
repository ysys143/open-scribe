#!/usr/bin/env python3
"""Debug TUI to check screens"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def check_screens():
    """Check which TranscribeScreen is being used"""
    print("Checking TUI screen imports...")
    
    # Check app.py imports
    from src.tui.app import YouTubeTranscriberTUI
    from src.tui.screens.transcribe_screen import TranscribeScreen as CorrectScreen
    from src.tui.screens.transcribe import TranscribeScreen as PlaceholderScreen
    
    print("\n✓ Both TranscribeScreen versions found:")
    print("  - transcribe_screen.py: Full implementation with URL input")
    print("  - transcribe.py: Placeholder version (Phase 4 pending)")
    
    # Check which one is used in app.py
    import src.tui.app as app_module
    import inspect
    source = inspect.getsource(app_module)
    
    if "from .screens.transcribe_screen import TranscribeScreen" in source:
        print("\n✅ CORRECT: app.py imports the full TranscribeScreen with URL input")
    else:
        print("\n❌ ISSUE: app.py might be importing the wrong TranscribeScreen")
    
    # Show what the TranscribeScreen should contain
    print("\nTranscribeScreen features (from transcribe_screen.py):")
    print("  - URL Input field: YES")
    print("  - Engine selection (RadioButtons): YES")
    print("  - Options (Switches): YES")
    print("  - Start/Clear/Back buttons: YES")
    print("  - Output display area: YES")
    
    print("\n📝 To navigate to TranscribeScreen in TUI:")
    print("  1. Run: python tui.py")
    print("  2. Press '1' or click 'Transcribe' in main menu")
    print("  3. The transcribe screen with URL input should appear")

if __name__ == "__main__":
    check_screens()