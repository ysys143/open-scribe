"""
OpenAI-based transcribers for Open-Scribe
Includes GPT-4o and Whisper API transcription
"""

import os
import time
from typing import Optional, List, Dict
from openai import OpenAI

from .base import BaseTranscriber
from ..utils.audio import compress_audio_if_needed, format_timestamp, timestamp_to_seconds
from ..utils.progress import ProgressBar

class OpenAITranscriber(BaseTranscriber):
    """Base class for OpenAI transcribers"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    @property
    def requires_api_key(self) -> bool:
        return True

class WhisperAPITranscriber(OpenAITranscriber):
    """OpenAI Whisper API transcriber"""
    
    @property
    def name(self) -> str:
        return "whisper-api"
    
    def transcribe(self, audio_path: str, stream: bool = False, 
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            stream: Enable streaming output
            return_timestamps: Include timestamps in output
            
        Returns:
            str: Transcribed text or None if failed
        """
        if not self.is_available():
            print("[Whisper API] Error: OpenAI API key not configured")
            return None
        
        if not self.validate_audio_file(audio_path):
            print(f"[Whisper API] Error: Audio file not found: {audio_path}")
            return None
        
        print(f"[Whisper API] Processing: {audio_path}")
        
        # Check and compress audio if needed
        processed_path, was_compressed = compress_audio_if_needed(audio_path)
        
        # Show progress for non-streaming mode
        progress = None
        if not stream:
            progress = ProgressBar("[Whisper API] Transcribing")
            progress.start()
        
        try:
            with open(processed_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json" if return_timestamps else "text"
                )
            
            if progress:
                progress.stop()
            
            # Handle response based on format
            if return_timestamps and hasattr(transcription, 'segments'):
                return self._format_with_timestamps(transcription.segments, stream)
            elif hasattr(transcription, 'text'):
                if stream:
                    self._stream_text(transcription.text)
                return transcription.text
            else:
                return str(transcription)
                
        except Exception as e:
            if progress:
                progress.stop()
            print(f"[Whisper API] Error: {e}")
            return None
        finally:
            # Clean up compressed file if created
            if was_compressed and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except:
                    pass
    
    def _format_with_timestamps(self, segments: List, stream: bool) -> str:
        """Format transcription with timestamps"""
        formatted_lines = []
        
        if stream:
            print("[Whisper API] Streaming transcription...")
            print("-" * 60)
        
        for segment in segments:
            if hasattr(segment, 'start') and hasattr(segment, 'text'):
                timestamp = format_timestamp(segment.start)
                text = segment.text.strip()
                line = f"[{timestamp}] {text}"
                formatted_lines.append(line)
                
                if stream:
                    print(line)
                    time.sleep(0.05)  # Streaming effect
        
        if stream:
            print("-" * 60)
        
        return '\n'.join(formatted_lines)
    
    def _stream_text(self, text: str):
        """Stream text output word by word"""
        print("[Whisper API] Streaming transcription...")
        print("-" * 60)
        
        words = text.split()
        current_line = []
        
        for i, word in enumerate(words):
            current_line.append(word)
            
            # Print 10 words per line
            if (i + 1) % 10 == 0:
                print(' '.join(current_line))
                current_line = []
                time.sleep(0.05)
        
        # Print remaining words
        if current_line:
            print(' '.join(current_line))
        
        print("-" * 60)

class GPT4TranscriberBase(OpenAITranscriber):
    """Base class for GPT-4 based transcribers"""
    
    def __init__(self, config, model: str):
        super().__init__(config)
        self.model = model
    
    def transcribe(self, audio_path: str, stream: bool = False,
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe using GPT-4 models via Whisper API
        Note: GPT-4 models use the same Whisper API endpoint
        """
        # GPT-4o models actually use Whisper API for transcription
        whisper = WhisperAPITranscriber(self.config)
        return whisper.transcribe(audio_path, stream, return_timestamps, **kwargs)

class GPT4OTranscriber(GPT4TranscriberBase):
    """GPT-4o transcriber"""
    
    def __init__(self, config):
        super().__init__(config, "gpt-4o")
    
    @property
    def name(self) -> str:
        return "gpt-4o-transcribe"

class GPT4OMiniTranscriber(GPT4TranscriberBase):
    """GPT-4o-mini transcriber"""
    
    def __init__(self, config):
        super().__init__(config, "gpt-4o-mini")
    
    @property
    def name(self) -> str:
        return "gpt-4o-mini-transcribe"