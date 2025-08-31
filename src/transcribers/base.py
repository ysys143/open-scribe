"""
Base transcriber class for Open-Scribe
Defines the interface all transcribers must implement
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseTranscriber(ABC):
    """Abstract base class for all transcription engines"""
    
    def __init__(self, config: Any):
        """
        Initialize transcriber with configuration
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    @abstractmethod
    def transcribe(self, audio_path: str, stream: bool = False,
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file or URL (for YouTube transcriber)
            stream: Enable streaming output
            return_timestamps: Include timestamps in output
            **kwargs: Additional engine-specific parameters
            
        Returns:
            str: Transcribed text or None if failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this transcriber is available/configured
        
        Returns:
            bool: True if transcriber can be used
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of this transcriber
        
        Returns:
            str: Transcriber name
        """
        pass
    
    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """
        Check if this transcriber requires an API key
        
        Returns:
            bool: True if API key is required
        """
        pass
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """
        Validate that audio file exists and is accessible
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            bool: True if file is valid
        """
        import os
        return os.path.exists(audio_path) and os.path.isfile(audio_path)
    
    def transcribe_with_chunking(self, audio_path: str, stream: bool = False,
                                return_timestamps: bool = False,
                                chunk_duration: int = 600,
                                max_workers: int = 5) -> Optional[str]:
        """
        Transcribe large audio files using chunking
        
        Args:
            audio_path: Path to audio file
            stream: Enable streaming output
            return_timestamps: Include timestamps
            chunk_duration: Duration of each chunk in seconds
            max_workers: Maximum concurrent workers
            
        Returns:
            str: Transcribed text or None if failed
        """
        from ..utils.audio import should_use_chunking, split_audio_into_chunks, cleanup_temp_chunks
        import os
        
        if not should_use_chunking(audio_path):
            return self.transcribe(audio_path, stream=stream, return_timestamps=return_timestamps)
        
        print(f"[{self.name}] Using chunking strategy for large file")
        chunk_paths = split_audio_into_chunks(audio_path, chunk_duration)
        
        try:
            # Transcribe each chunk
            chunk_texts = []
            for i, chunk_path in enumerate(chunk_paths):
                print(f"[{self.name}] Processing chunk {i+1}/{len(chunk_paths)}")
                text = self.transcribe(chunk_path, stream=False, return_timestamps=False)
                if text:
                    chunk_texts.append(text)
                else:
                    print(f"[{self.name}] Warning: Chunk {i+1} failed to transcribe")
            
            # Simple merge
            final_text = ' '.join(chunk_texts)
            
            if stream and final_text:
                self._stream_text(final_text)
            
            return final_text if final_text else None
            
        finally:
            # Clean up chunks
            keep_chunks = os.getenv('OPEN_SCRIBE_VERBOSE') == 'true'
            cleanup_temp_chunks(chunk_paths, keep_for_debug=keep_chunks)
    
    def _stream_text(self, text: str):
        """
        Stream text output word by word
        
        Args:
            text: Text to stream
        """
        import time
        print(f"[{self.name}] Streaming transcription...")
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