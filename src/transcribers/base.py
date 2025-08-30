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
    def transcribe(self, audio_path: str, **kwargs) -> Optional[str]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
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