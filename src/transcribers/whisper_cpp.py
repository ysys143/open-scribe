"""
Whisper.cpp local transcriber
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import BaseTranscriber


class WhisperCppTranscriber(BaseTranscriber):
    """Transcriber using local whisper.cpp"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_path = os.getenv('WHISPER_CPP_MODEL')
        self.executable_path = os.getenv('WHISPER_CPP_EXECUTABLE', 'whisper')
    
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
                  return_timestamps: bool = False) -> Optional[str]:
        """
        Transcribe using whisper.cpp
        
        Args:
            audio_file: Path to audio file
            stream: Streaming mode (not supported for whisper.cpp)
            return_timestamps: Whether to include timestamps
            
        Returns:
            str: Transcription text or None if failed
        """
        if not self.is_available():
            print("Error: whisper.cpp is not configured properly")
            print(f"Model path: {self.model_path}")
            print(f"Executable: {self.executable_path}")
            return None
        
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