"""
Progress display utilities for Open-Scribe
"""

import sys
import time
import threading
import itertools
from typing import Optional, Callable

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

class EstimatedProgressBar:
    """Progress bar with estimated time tracking"""
    
    def __init__(self, message: str = "Processing", estimated_duration: float = 30.0):
        """
        Initialize progress bar with estimated duration
        
        Args:
            message: Message to display
            estimated_duration: Estimated processing time in seconds
        """
        self.message = message
        self.estimated_duration = estimated_duration
        self.start_time = None
        self.stop_event = threading.Event()
        self.thread = None
        self.completed = False
        self.current_chunk = None
        self.total_chunks = None
        
    def set_chunk_info(self, current: int, total: int):
        """Set chunk processing information"""
        self.current_chunk = current
        self.total_chunks = total
        
    def start(self):
        """Start the progress bar animation"""
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def _animate(self):
        """Animation loop for progress bar"""
        bar_length = 30
        
        while not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            
            # Calculate progress percentage
            if self.completed:
                progress = 100.0
            elif elapsed < self.estimated_duration:
                # Linear progress up to 90%
                progress = min(90.0, (elapsed / self.estimated_duration) * 90.0)
            else:
                # Stay between 90-99% when over time
                overtime = elapsed - self.estimated_duration
                # Oscillate between 90-99% every 2 seconds
                progress = 90.0 + 9.0 * (0.5 + 0.5 * abs((overtime % 4) - 2) / 2)
            
            # Calculate bar fill
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Format time display
            time_display = f"{int(elapsed)}s/{int(self.estimated_duration)}s"
            if elapsed > self.estimated_duration:
                time_display = f"{int(elapsed)}s (overtime)"
            
            # Build message
            if self.current_chunk is not None and self.total_chunks is not None:
                chunk_info = f" Chunk {self.current_chunk}/{self.total_chunks}:"
                full_message = f'\r{self.message}{chunk_info} [{bar}] {progress:.1f}% ({time_display})'
            else:
                full_message = f'\r{self.message}: [{bar}] {progress:.1f}% ({time_display})'
            
            # Display
            sys.stdout.write(full_message + ' ' * 10)  # Extra spaces to clear line
            sys.stdout.flush()
            time.sleep(0.1)
        
        # Final update when completed
        if self.completed:
            elapsed = time.time() - self.start_time
            filled = bar_length
            bar = '█' * filled
            
            if self.current_chunk is not None and self.total_chunks is not None:
                chunk_info = f" Chunk {self.current_chunk}/{self.total_chunks}:"
                full_message = f'\r{self.message}{chunk_info} [{bar}] 100.0% ({int(elapsed)}s)'
            else:
                full_message = f'\r{self.message}: [{bar}] 100.0% ({int(elapsed)}s)'
            
            sys.stdout.write(full_message + '\n')
        else:
            # Clear the line
            sys.stdout.write('\r' + ' ' * 80 + '\r')
        
        sys.stdout.flush()
        
    def complete(self):
        """Mark as completed and show 100%"""
        self.completed = True
        time.sleep(0.1)  # Brief pause to show 100%
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)
            
    def stop(self):
        """Stop the progress bar animation"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)


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


def create_estimated_progress(message: str, estimated_duration: float = 30.0,
                            chunk_info: Optional[tuple] = None) -> EstimatedProgressBar:
    """
    Create an estimated progress bar
    
    Args:
        message: Message to display
        estimated_duration: Estimated processing time in seconds
        chunk_info: Optional tuple of (current_chunk, total_chunks)
        
    Returns:
        EstimatedProgressBar instance
    """
    progress = EstimatedProgressBar(message, estimated_duration)
    if chunk_info:
        progress.set_chunk_info(chunk_info[0], chunk_info[1])
    return progress


class ChunkedProgressBar:
    """Progress bar for chunked processing with thread-safe updates"""
    
    def __init__(self, total_chunks: int, estimated_per_chunk: float = 30.0):
        """
        Initialize chunked progress bar
        
        Args:
            total_chunks: Total number of chunks to process
            estimated_per_chunk: Estimated time per chunk in seconds
        """
        self.total_chunks = total_chunks
        self.completed_chunks = 0
        self.estimated_per_chunk = estimated_per_chunk
        self.estimated_total = total_chunks * estimated_per_chunk
        self.start_time = None
        self.stop_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()  # Thread lock for safe updates
        self.active_workers = 0
        self.max_workers = 5
        
    def start(self):
        """Start the progress bar animation"""
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def _animate(self):
        """Animation loop for progress bar"""
        bar_length = 40  # Longer bar for better visibility
        
        while not self.stop_event.is_set():
            with self.lock:
                elapsed = time.time() - self.start_time
                
                # Calculate overall progress
                progress_pct = (self.completed_chunks / self.total_chunks) * 100
                
                # Calculate ETA
                if self.completed_chunks > 0:
                    avg_time_per_chunk = elapsed / self.completed_chunks
                    remaining_chunks = self.total_chunks - self.completed_chunks
                    eta = remaining_chunks * avg_time_per_chunk
                    eta_str = f"ETA: {int(eta)}s"
                else:
                    eta_str = f"ETA: {int(self.estimated_total)}s"
                
                # Create progress bar
                filled = int(bar_length * progress_pct / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                # Build status message
                status = f"\r[Whisper API] Processing chunks: [{bar}] {self.completed_chunks}/{self.total_chunks} ({progress_pct:.1f}%) | {eta_str}"
                
                # Clear line and write status
                sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear entire line
                sys.stdout.write(status)
                sys.stdout.flush()
            
            time.sleep(0.1)
        
        # Final update
        with self.lock:
            if self.completed_chunks == self.total_chunks:
                elapsed = time.time() - self.start_time
                filled = bar_length
                bar = '█' * filled
                status = f"\r[Whisper API] Processing chunks: [{bar}] {self.total_chunks}/{self.total_chunks} (100.0%) | Completed in {int(elapsed)}s"
                sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear entire line
                sys.stdout.write(status + '\n')
                sys.stdout.flush()
    
    def complete_chunk(self, chunk_number: int):
        """Mark a chunk as completed (thread-safe)"""
        with self.lock:
            self.completed_chunks += 1
    
    def finish(self):
        """Stop the progress bar"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)