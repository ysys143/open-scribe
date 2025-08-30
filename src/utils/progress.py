"""
Progress display utilities for Open-Scribe
"""

import sys
import time
import threading
import itertools
from typing import Optional

class ProgressBar:
    """Progress bar for non-streaming mode"""
    
    def __init__(self, message: str = "Processing"):
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None
        
    def start(self):
        """Start the progress bar animation"""
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def _animate(self):
        """Animation loop for progress bar"""
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while not self.stop_event.is_set():
            sys.stdout.write(f'\r{self.message} {next(spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 3) + '\r')
        sys.stdout.flush()
        
    def stop(self):
        """Stop the progress bar animation"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)

class DownloadProgress:
    """Progress tracking for downloads"""
    
    def __init__(self):
        self.current = 0
        self.total = 0
        self.percentage = 0
        
    def update(self, downloaded: int, total: int):
        """Update download progress"""
        self.current = downloaded
        self.total = total
        if total > 0:
            self.percentage = (downloaded / total) * 100
            
    def display(self, prefix: str = "Downloading"):
        """Display progress bar"""
        bar_length = 30
        filled = int(bar_length * self.percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        sys.stdout.write(f'\r{prefix}: [{bar}] {self.percentage:.1f}%')
        sys.stdout.flush()
        
        if self.percentage >= 100:
            sys.stdout.write('\n')
            sys.stdout.flush()

def show_spinner(message: str, duration: Optional[float] = None):
    """
    Show a spinner for a specified duration or until stopped
    
    Args:
        message: Message to display
        duration: Duration in seconds (None for indefinite)
    """
    progress = ProgressBar(message)
    progress.start()
    
    if duration:
        time.sleep(duration)
        progress.stop()
        return None
    
    return progress