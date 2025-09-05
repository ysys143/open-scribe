#!/usr/bin/env python3
"""
YouTube Transcriber TUI 진입점
"""

import sys
from pathlib import Path

# src 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.tui.app import YouTubeTranscriberTUI

if __name__ == "__main__":
    app = YouTubeTranscriberTUI()
    app.run()