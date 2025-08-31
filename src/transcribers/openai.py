"""
Simplified OpenAI-based transcribers for Open-Scribe
Includes GPT-4o and Whisper API transcription
"""

import os
import time
from typing import Optional, List
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseTranscriber
from ..utils.audio import (
    compress_audio_if_needed, format_timestamp,
    should_use_chunking, split_audio_into_chunks, cleanup_temp_chunks,
    get_audio_duration
)
from ..utils.progress import create_estimated_progress, ChunkedProgressBar


class OpenAITranscriber(BaseTranscriber):
    """Base class for OpenAI transcribers"""
    
    def __init__(self, config, model_name: str = "whisper-1", display_name: str = "Whisper API"):
        super().__init__(config)
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.model_name = model_name
        self.display_name = display_name
    
    def is_available(self) -> bool:
        return self.client is not None
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def name(self) -> str:
        return self.display_name


class WhisperAPITranscriber(OpenAITranscriber):
    """OpenAI Whisper API transcriber"""
    
    def __init__(self, config):
        super().__init__(config, model_name="whisper-1", display_name="Whisper API")
    
    @property
    def name(self) -> str:
        return "whisper-api"
    
    def transcribe_single_chunk(self, chunk_path: str, chunk_index: int, 
                               return_timestamps: bool = False,
                               chunk_start_time: float = 0) -> tuple[int, Optional[str]]:
        """
        Transcribe a single audio chunk
        
        Args:
            chunk_path: Path to chunk file
            chunk_index: Index of this chunk
            return_timestamps: Whether to include timestamps
            
        Returns:
            tuple: (chunk_index, transcribed_text)
        """
        try:
            with open(chunk_path, "rb") as audio_file:
                # Choose response format based on model capabilities
                if return_timestamps and self.model_name == "whisper-1":
                    response_format = "verbose_json"
                else:
                    response_format = "text"
                
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    response_format=response_format
                )
            
            # Handle response based on format
            if return_timestamps and self.model_name == "whisper-1" and hasattr(transcription, 'segments'):
                # Format with timestamps for whisper-1
                lines = []
                for segment in transcription.segments:
                    timestamp = format_timestamp(segment.start)
                    lines.append(f"[{timestamp}] {segment.text.strip()}")
                return chunk_index, '\n'.join(lines)
            elif isinstance(transcription, str):
                return chunk_index, transcription
            elif hasattr(transcription, 'text'):
                return chunk_index, transcription.text
            else:
                return chunk_index, str(transcription)
                
        except Exception as e:
            print(f"[{self.display_name}] Error transcribing chunk {chunk_index + 1}: {e}")
            return chunk_index, None
    
    def transcribe_chunks_concurrent(self, chunk_paths: List[str], max_workers: int = 5,
                                    return_timestamps: bool = False) -> List[str]:
        """
        Transcribe multiple chunks concurrently
        
        Returns:
            list: Transcribed texts ordered by chunk index
        """
        results = [None] * len(chunk_paths)
        
        print(f"[{self.display_name}] Transcribing {len(chunk_paths)} chunks...")
        
        # Progress bar
        progress = ChunkedProgressBar(
            total_chunks=len(chunk_paths),
            estimated_per_chunk=30.0,
            display_name=self.display_name
        )
        progress.start()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, chunk_path in enumerate(chunk_paths):
                future = executor.submit(self.transcribe_single_chunk, chunk_path, i, return_timestamps)
                futures[future] = i
            
            # Process results as they complete
            for future in as_completed(futures):
                chunk_index, text = future.result()
                results[chunk_index] = text
                progress.complete_chunk(chunk_index + 1)
                
                if text:
                    print(f"[{self.display_name}] Chunk {chunk_index + 1}: {len(text)} chars")
        
        progress.finish()
        
        # Filter out None results and return
        valid_texts = [text for text in results if text]
        print(f"[{self.display_name}] Completed: {len(valid_texts)}/{len(chunk_paths)} chunks")
        
        return valid_texts
    
    def transcribe(self, audio_path: str, stream: bool = False, 
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe using OpenAI API with automatic chunking for large files
        """
        if not self.is_available():
            print(f"[{self.display_name}] Error: OpenAI API key not configured")
            return None
        
        if not self.validate_audio_file(audio_path):
            print(f"[{self.display_name}] Error: Audio file not found: {audio_path}")
            return None
        
        print(f"[{self.display_name}] Processing: {audio_path}")
        
        # Check timestamp support for the model
        if return_timestamps and self.model_name != "whisper-1":
            print(f"[{self.display_name}] ⚠️  Warning: {self.model_name} does not support timestamps")
            print(f"[{self.display_name}] Proceeding without timestamps...")
            return_timestamps = False
        
        # Check if chunking is needed
        if should_use_chunking(audio_path):
            print(f"[{self.display_name}] File is large, using chunking strategy...")
            
            # Split audio into chunks
            chunk_paths = split_audio_into_chunks(audio_path, chunk_duration_seconds=600)
            
            try:
                # Transcribe chunks concurrently
                chunk_texts = self.transcribe_chunks_concurrent(
                    chunk_paths,
                    max_workers=min(5, len(chunk_paths)),
                    return_timestamps=return_timestamps
                )
                
                # Merge based on timestamp preference
                if return_timestamps:
                    # For timestamps, join with newlines
                    final_transcription = '\n'.join(chunk_texts) if chunk_texts else ""
                else:
                    # For plain text, join with spaces
                    final_transcription = ' '.join(chunk_texts) if chunk_texts else ""
                
                if not final_transcription:
                    print(f"[{self.display_name}] Failed to transcribe")
                    return None
                
                # Stream output if requested
                if stream:
                    self._stream_text(final_transcription)
                
                return final_transcription
                
            finally:
                # Clean up chunk files
                keep_chunks = os.getenv('OPEN_SCRIBE_VERBOSE') == 'true'
                cleanup_temp_chunks(chunk_paths, keep_for_debug=keep_chunks)
        
        # For smaller files, transcribe directly
        processed_path, was_compressed = compress_audio_if_needed(audio_path)
        
        # Show progress
        progress = None
        if not stream:
            file_size_mb = os.path.getsize(processed_path) / (1024 * 1024)
            estimated_duration = max(10, min(60, file_size_mb * 3))
            progress = create_estimated_progress(f"[{self.display_name}] Transcribing", estimated_duration)
            progress.start()
        
        try:
            with open(processed_path, "rb") as audio_file:
                # Choose response format based on model capabilities
                if return_timestamps and self.model_name == "whisper-1":
                    response_format = "verbose_json"
                else:
                    response_format = "text"
                
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    response_format=response_format
                )
            
            if progress:
                progress.complete()
            
            # Handle response based on format
            if return_timestamps and self.model_name == "whisper-1" and hasattr(transcription, 'segments'):
                # Format with timestamps for whisper-1
                lines = []
                for segment in transcription.segments:
                    timestamp = format_timestamp(segment.start)
                    lines.append(f"[{timestamp}] {segment.text.strip()}")
                text = '\n'.join(lines)
            elif isinstance(transcription, str):
                text = transcription
            elif hasattr(transcription, 'text'):
                text = transcription.text
            else:
                text = str(transcription)
            
            if stream and text:
                self._stream_text(text)
            
            return text
                
        except Exception as e:
            if progress:
                progress.stop()
            print(f"[{self.display_name}] Error: {e}")
            return None
        finally:
            # Clean up compressed file if created
            if was_compressed and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except:
                    pass
    
    def _stream_text(self, text: str):
        """Stream text output word by word"""
        print(f"[{self.display_name}] Streaming transcription...")
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


class GPT4OTranscriber(WhisperAPITranscriber):
    """GPT-4o transcriber"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_name = "gpt-4o-transcribe"  # Use actual model name
        self.display_name = "GPT-4o"
    
    @property
    def name(self) -> str:
        return "gpt-4o-transcribe"


class GPT4OMiniTranscriber(WhisperAPITranscriber):
    """GPT-4o-mini transcriber"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model_name = "gpt-4o-mini-transcribe"  # Use actual model name
        self.display_name = "GPT-4o-mini"
    
    @property
    def name(self) -> str:
        return "gpt-4o-mini-transcribe"