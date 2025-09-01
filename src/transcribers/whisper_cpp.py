"""
Whisper.cpp local transcriber
"""

import os
import re
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, List

from .base import BaseTranscriber
from ..utils.audio import split_audio_into_chunks, cleanup_temp_chunks, get_audio_duration
from ..utils.worker_pool import WorkerPool, ChunkResult


class WhisperCppTranscriber(BaseTranscriber):
    """Transcriber using local whisper.cpp"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_path = config.WHISPER_CPP_MODEL
        self.executable_path = config.WHISPER_CPP_EXECUTABLE
    
    @property
    def name(self) -> str:
        """Get the name of this transcriber"""
        return "Whisper.cpp"
    
    @property
    def requires_api_key(self) -> bool:
        """Whisper.cpp is local and doesn't require an API key"""
        return False
        
    def is_available(self) -> bool:
        """Check if whisper.cpp is available"""
        if not self.model_path or not Path(self.model_path).exists():
            return False
            
        # Check if executable exists
        try:
            result = subprocess.run(
                [self.executable_path, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def transcribe(self, audio_file: str, stream: bool = False,
                  return_timestamps: bool = False, use_parallel: bool = True) -> Optional[str]:
        """
        Transcribe using whisper.cpp
        
        Args:
            audio_file: Path to audio file
            stream: Streaming mode (not supported for whisper.cpp)
            return_timestamps: Whether to include timestamps
            use_parallel: Use parallel processing for large files
            
        Returns:
            str: Transcription text or None if failed
        """
        if not self.is_available():
            print("Error: whisper.cpp is not configured properly")
            print(f"Model path: {self.model_path}")
            print(f"Executable: {self.executable_path}")
            return None
        
        # Check if we should use parallel processing
        duration = get_audio_duration(audio_file)
        
        # Use parallel for files longer than 10 minutes
        if use_parallel and duration > 600:
            print(f"[Whisper.cpp] Using parallel processing for {duration}s audio")
            return self._transcribe_parallel(audio_file, return_timestamps)
        
        # Create temp output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            output_file = tmp.name
        
        # Create a temp symlink with a simple name if the file has special characters
        temp_audio_link = None
        audio_to_use = audio_file
        output_extension = '.txt'  # Default extension
        
        # Check if filename contains problematic characters
        if any(c in audio_file for c in ["'", "'", "'", """, """, "？", "｜", " "]):
            try:
                # Create temp symlink with simple name
                import hashlib
                file_hash = hashlib.md5(audio_file.encode()).hexdigest()[:8]
                ext = Path(audio_file).suffix
                temp_audio_link = f"/tmp/whisper_temp_{file_hash}{ext}"
                
                # Remove existing symlink if present
                if Path(temp_audio_link).exists():
                    Path(temp_audio_link).unlink()
                
                # Create symlink
                Path(temp_audio_link).symlink_to(Path(audio_file).absolute())
                audio_to_use = temp_audio_link
                print(f"Using temporary file for whisper.cpp processing...")
            except Exception as e:
                print(f"Warning: Could not create temp symlink: {e}")
                # Continue with original path
        
        try:
            # Build whisper.cpp command
            cmd = [
                self.executable_path,
                '-m', self.model_path,
                '-f', audio_to_use,
                '-of', output_file[:-4],  # Remove .txt extension as whisper.cpp adds it
                '--print-progress',  # Show progress
                '--threads', '4'
            ]
            
            # Choose output format based on timestamp preference
            if return_timestamps:
                # Use SRT format for timestamps
                cmd.append('--output-srt')
                output_extension = '.srt'
            else:
                # Use plain text format without timestamps
                cmd.append('--output-txt')
                output_extension = '.txt'
            
            # Add language hint if available
            cmd.extend(['-l', 'auto'])
            
            print("Running whisper.cpp (this may take a while)...")
            
            # Run whisper.cpp with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=False
            )
            
            # Stream output in real-time with progress bar
            output_lines = []
            try:
                for line in process.stdout:
                    decoded_line = line.decode('utf-8', errors='replace')
                    # Parse and display progress bar
                    if 'progress' in decoded_line.lower() or '%' in decoded_line:
                        # Extract percentage from lines like "progress = 90%"
                        percent_match = re.search(r'(\d+)%', decoded_line)
                        if percent_match:
                            percent = int(percent_match.group(1))
                            # Create progress bar
                            bar_length = 50
                            filled = int(bar_length * percent / 100)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"\rTranscribing: [{bar}] {percent:3d}%", end='', flush=True)
                        else:
                            # If we can't parse percentage, show the raw line
                            print(f"\r{decoded_line.strip()}", end='', flush=True)
                    output_lines.append(decoded_line)
                
                # Wait for process to complete
                process.wait(timeout=1800)  # 30 minute timeout
                print()  # Add newline after progress bar
                result_returncode = process.returncode
                result_output = ''.join(output_lines)
                
            except subprocess.TimeoutExpired:
                process.kill()
                print("\nError: whisper.cpp timed out (exceeded 30 minutes)")
                return None
            
            # Check result
            result = type('Result', (), {'returncode': result_returncode, 'stdout': result_output.encode('utf-8')})()
            
            # Run whisper.cpp
            # result = subprocess.run(
            #     cmd,
            #     capture_output=True,
            #     text=False,  # Use binary to avoid encoding issues
            #     timeout=1800  # 30 minute timeout
            # )
            
            if result.returncode != 0:
                print(f"\nError: whisper.cpp failed with code {result.returncode}")
                if result_output:
                    print(f"Error output: {result_output[:500]}")  # Show first 500 chars
                return None
            
            # Read the output file with correct extension
            actual_output_file = output_file[:-4] + output_extension
            if Path(actual_output_file).exists():
                # Try reading with UTF-8, fallback to other encodings
                try:
                    with open(actual_output_file, 'r', encoding='utf-8') as f:
                        transcription = f.read().strip()
                except UnicodeDecodeError:
                    # Try with errors='replace' to handle invalid UTF-8
                    with open(actual_output_file, 'r', encoding='utf-8', errors='replace') as f:
                        transcription = f.read().strip()
                
                # Format output based on timestamp preference
                if return_timestamps:
                    # Parse SRT format and convert to simpler format
                    # SRT format:
                    # 1
                    # 00:00:00,000 --> 00:00:05,000
                    # Text content
                    parts = transcription.split('\n\n')
                    formatted_lines = []
                    for part in parts:
                        lines = part.strip().split('\n')
                        if len(lines) >= 3:
                            # lines[0] is the sequence number
                            # lines[1] is the timestamp
                            # lines[2:] is the text
                            timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}),\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', lines[1])
                            if timestamp_match:
                                timestamp = timestamp_match.group(1)
                                # Remove leading zeros from hours if 00
                                if timestamp.startswith('00:'):
                                    timestamp = timestamp[3:]
                                text = ' '.join(lines[2:])
                                formatted_lines.append(f"[{timestamp}] {text}")
                    return '\n'.join(formatted_lines)
                else:
                    # Plain text format, return as is
                    return transcription
            else:
                print(f"Error: Output file not found: {actual_output_file}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Error: whisper.cpp timed out (exceeded 30 minutes)")
            return None
        except Exception as e:
            print(f"Error running whisper.cpp: {e}")
            return None
        finally:
            # Clean up temp files (check for both .txt and .srt extensions)
            try:
                for ext in ['.txt', '.srt']:
                    temp_file = output_file[:-4] + ext
                    if Path(temp_file).exists():
                        Path(temp_file).unlink()
            except:
                pass
            
            # Clean up temp symlink if created
            if temp_audio_link and Path(temp_audio_link).exists():
                try:
                    Path(temp_audio_link).unlink()
                except:
                    pass
    
    def _transcribe_parallel(self, audio_file: str, return_timestamps: bool = False) -> Optional[str]:
        """
        Transcribe using parallel processing
        
        Args:
            audio_file: Path to audio file
            return_timestamps: Whether to include timestamps
            
        Returns:
            Transcribed text or None
        """
        # Get audio duration
        duration = get_audio_duration(audio_file)
        
        # Split audio into chunks (5 minute chunks for whisper-cpp)
        chunk_duration = 300  # 5 minutes
        print(f"[Whisper.cpp] Splitting audio into {chunk_duration}s chunks...")
        chunk_paths = split_audio_into_chunks(audio_file, chunk_duration_seconds=chunk_duration)
        
        if not chunk_paths:
            print("[Whisper.cpp] Failed to split audio")
            return None
        
        print(f"[Whisper.cpp] Created {len(chunk_paths)} chunks")
        
        # Initialize worker pool
        worker_pool = WorkerPool(self.config)
        
        # Define processor function for chunks
        def process_chunk(chunk_path: str, index: int) -> str:
            """Process a single chunk"""
            # Use single-threaded transcribe for each chunk
            result = self.transcribe(
                chunk_path,
                stream=False,
                return_timestamps=return_timestamps,
                use_parallel=False  # Prevent recursive parallel
            )
            return result if result else ""
        
        try:
            # Process chunks in parallel
            results = worker_pool.process_chunks(
                chunks=chunk_paths,
                processor_func=process_chunk,
                duration_seconds=int(duration),
                engine='whisper-cpp',
                verbose=self.config.VERBOSE
            )
            
            # Merge results
            if return_timestamps:
                # For timestamps, we need special handling to adjust times
                merged = self._merge_timestamped_results(results, chunk_duration)
            else:
                # Simple merge for plain text
                merged = worker_pool.merge_results(results, separator=" ")
            
            return merged if merged else None
            
        finally:
            # Clean up chunk files
            cleanup_temp_chunks(chunk_paths, keep_for_debug=self.config.VERBOSE)
    
    def _merge_timestamped_results(self, results: List[ChunkResult], chunk_duration: int) -> str:
        """
        Merge timestamped results adjusting timestamps for each chunk
        
        Args:
            results: List of chunk results
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            Merged text with adjusted timestamps
        """
        merged_lines = []
        
        for result in sorted(results, key=lambda r: r.index):
            if not result.success or not result.text:
                continue
            
            # Calculate time offset for this chunk
            time_offset = result.index * chunk_duration
            
            # Adjust timestamps in the text
            lines = result.text.split('\n')
            for line in lines:
                # Match timestamp pattern [HH:MM:SS] or [MM:SS]
                match = re.match(r'^\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$', line)
                if match:
                    # Parse timestamp
                    if match.group(3):  # HH:MM:SS format
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        seconds = int(match.group(3))
                    else:  # MM:SS format
                        hours = 0
                        minutes = int(match.group(1))
                        seconds = int(match.group(2))
                    
                    # Add offset
                    total_seconds = hours * 3600 + minutes * 60 + seconds + time_offset
                    
                    # Format new timestamp
                    new_hours = total_seconds // 3600
                    new_minutes = (total_seconds % 3600) // 60
                    new_seconds = total_seconds % 60
                    
                    if new_hours > 0:
                        timestamp = f"[{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}]"
                    else:
                        timestamp = f"[{new_minutes:02d}:{new_seconds:02d}]"
                    
                    # Add adjusted line
                    text = match.group(4) if match.group(4) else ""
                    merged_lines.append(f"{timestamp} {text}")
                elif line.strip():  # Non-timestamp lines
                    merged_lines.append(line)
        
        return '\n'.join(merged_lines)