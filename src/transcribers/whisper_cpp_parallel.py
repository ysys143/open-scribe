"""
Enhanced Whisper.cpp processor with progress tracking for parallel processing
"""

import subprocess
import re
import time
import threading
from typing import Callable, Optional


class WhisperCppProgressProcessor:
    """Process whisper.cpp with progress tracking"""
    
    def __init__(self, executable_path: str, model_path: str, verbose: bool = False):
        self.executable_path = executable_path
        self.model_path = model_path
        self.verbose = verbose
    
    def transcribe_with_progress(
        self,
        audio_file: str,
        chunk_index: int,
        return_timestamps: bool = False,
        progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> str:
        """
        Transcribe audio with progress tracking
        
        Args:
            audio_file: Path to audio file
            chunk_index: Index of the chunk being processed
            return_timestamps: Whether to return timestamps
            progress_callback: Callback for progress updates (chunk_index, progress_pct)
            
        Returns:
            Transcribed text
        """
        # Build command
        output_file = f"/tmp/whisper_chunk_{chunk_index}"
        cmd = [
            self.executable_path,
            '-m', self.model_path,
            '-f', audio_file,
            '-of', output_file,
            # '--print-progress' removed to avoid stderr output
            '--threads', '4',
            '-l', 'auto'
        ]
        
        # Add format option
        if return_timestamps:
            cmd.append('--output-srt')
            output_extension = '.srt'
        else:
            cmd.append('--output-txt')
            output_extension = '.txt'
        
        # Start process - suppress all stderr output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Suppress all stderr output
            universal_newlines=False
        )
        
        # Simple progress simulation since we can't get real progress from whisper.cpp
        def simulate_progress():
            """Simulate progress based on time"""
            start = time.time()
            # Estimate 80-100 seconds per 5-minute chunk
            estimated_duration = 90
            
            # Initial progress
            if progress_callback:
                progress_callback(chunk_index, 1)
            
            while process.poll() is None:  # While process is running
                elapsed = time.time() - start
                progress_pct = min(95, (elapsed / estimated_duration) * 100)
                
                if progress_callback:
                    progress_callback(chunk_index, max(1, progress_pct))
                
                time.sleep(1)  # Update every second
            
            # Almost done
            if progress_callback:
                progress_callback(chunk_index, 99)
        
        # Start progress simulation thread
        if progress_callback:
            monitor_thread = threading.Thread(target=simulate_progress, daemon=True)
            monitor_thread.start()
        
        # Wait for process
        stdout, stderr = process.communicate()
        returncode = process.returncode
        
        # Mark as complete
        if progress_callback:
            progress_callback(chunk_index, 100)
        
        if returncode != 0:
            raise Exception(f"Whisper.cpp failed with code {returncode}")
        
        # Read output file
        actual_output_file = output_file + output_extension
        try:
            with open(actual_output_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Failed to read output: {e}")
        finally:
            # Clean up
            try:
                import os
                if os.path.exists(actual_output_file):
                    os.unlink(actual_output_file)
            except:
                pass