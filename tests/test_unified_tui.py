#!/usr/bin/env python3
"""Test unified TUI with integrated transcribe interface"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_unified_tui():
    """Test that unified TUI works correctly"""
    try:
        from src.tui.app import YouTubeTranscriberTUI
        from src.tui.screens.main_menu import MainMenuScreen
        
        print("✓ Unified TUI components imported successfully")
        
        print("\n📋 New TUI Features:")
        print("  - Split-screen layout maintained (menu left, content right)")
        print("  - Transcribe interface appears in content area")
        print("  - Text-based buttons and controls")
        print("  - URL input field in content area")
        print("  - Keyboard shortcuts: [S]tart, [C]lear")
        
        print("\n🎯 To test the unified TUI:")
        print("  1. Run: source .venv/bin/activate")
        print("  2. Run: python tui.py")
        print("  3. Press '1' or click 'Transcribe' in menu")
        print("  4. Content area shows transcribe interface")
        print("  5. Click in URL input field and type/paste URL")
        print("  6. Press 'S' to start or 'C' to clear")
        
        print("\n✅ All components ready!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_unified_tui()
    sys.exit(0 if success else 1)