"""
OpenAI-based transcribers for Open-Scribe
Includes GPT-4o and Whisper API transcription
"""

import os
import time
import asyncio
from typing import Optional, List, Dict, Tuple
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseTranscriber
from ..utils.audio import (
    compress_audio_if_needed, format_timestamp, timestamp_to_seconds,
    should_use_chunking, split_audio_into_chunks, cleanup_temp_chunks,
    get_audio_duration
)
from ..utils.progress import ProgressBar, EstimatedProgressBar, create_estimated_progress

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
    
    def transcribe_single_chunk(self, chunk_path: str, chunk_index: int, 
                              chunk_start_time: float = 0) -> Tuple[int, Optional[Dict]]:
        """
        Transcribe a single audio chunk
        
        Args:
            chunk_path: Path to chunk file
            chunk_index: Index of this chunk
            chunk_start_time: Start time of this chunk in original audio
            
        Returns:
            tuple: (chunk_index, result_dict with text and timestamps)
        """
        try:
            with open(chunk_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            result = {
                'text': transcription.text if hasattr(transcription, 'text') else str(transcription),
                'segments': []
            }
            
            # Adjust timestamps for chunk position
            if hasattr(transcription, 'segments'):
                for segment in transcription.segments:
                    if hasattr(segment, 'start') and hasattr(segment, 'text'):
                        adjusted_segment = {
                            'start': segment.start + chunk_start_time,
                            'end': segment.end + chunk_start_time if hasattr(segment, 'end') else segment.start + chunk_start_time,
                            'text': segment.text
                        }
                        result['segments'].append(adjusted_segment)
            
            return chunk_index, result
            
        except Exception as e:
            print(f"[Whisper API] Error transcribing chunk {chunk_index}: {e}")
            return chunk_index, None
    
    def transcribe_chunks_concurrent(self, chunk_paths: List[str], 
                                   chunk_duration: float = 600,
                                   max_workers: int = 5) -> List[Dict]:
        """
        Transcribe multiple chunks concurrently
        
        Args:
            chunk_paths: List of paths to chunk files
            chunk_duration: Duration of each chunk in seconds
            max_workers: Maximum concurrent workers
            
        Returns:
            list: Transcription results ordered by chunk index
        """
        results = [None] * len(chunk_paths)
        
        print(f"[Whisper API] Transcribing {len(chunk_paths)} chunks with {max_workers} workers...")
        
        # Use a single consolidated progress bar for all chunks
        from ..utils.progress import ChunkedProgressBar
        progress = ChunkedProgressBar(
            total_chunks=len(chunk_paths),
            estimated_per_chunk=30.0  # 30 seconds per chunk
        )
        progress.start()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, chunk_path in enumerate(chunk_paths):
                chunk_start_time = i * chunk_duration
                future = executor.submit(
                    self.transcribe_single_chunk, 
                    chunk_path, i, chunk_start_time
                )
                futures[future] = i
            
            # Process results as they complete
            for future in as_completed(futures):
                chunk_index, result = future.result()
                results[chunk_index] = result
                progress.complete_chunk(chunk_index + 1)
        
        progress.finish()
        print(f"[Whisper API] All {len(chunk_paths)} chunks completed successfully")
        
        return results
    
    def merge_chunk_results(self, chunk_results: List[Dict], 
                          return_timestamps: bool = False) -> str:
        """
        Merge chunk results into final transcription
        
        Args:
            chunk_results: List of chunk transcription results
            return_timestamps: Whether to include timestamps
            
        Returns:
            str: Merged transcription text
        """
        if not chunk_results:
            return ""
        
        # Filter out None results (failed chunks)
        valid_results = [r for r in chunk_results if r is not None]
        
        if not valid_results:
            return ""
        
        if return_timestamps:
            # Merge with timestamps
            all_segments = []
            for result in valid_results:
                if result and 'segments' in result:
                    all_segments.extend(result['segments'])
            
            # Format with timestamps
            lines = []
            for segment in all_segments:
                timestamp = format_timestamp(segment['start'])
                lines.append(f"[{timestamp}] {segment['text'].strip()}")
            
            return '\n'.join(lines)
        else:
            # Simple text merge
            texts = []
            for result in valid_results:
                if result and 'text' in result:
                    texts.append(result['text'].strip())
            
            return ' '.join(texts)
    
    def transcribe(self, audio_path: str, stream: bool = False, 
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe using OpenAI Whisper API with automatic chunking for large files
        
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
        
        # Check if chunking is needed
        if should_use_chunking(audio_path):
            print("[Whisper API] File is large, using chunking strategy...")
            
            # Automatically disable stream mode for chunking
            if stream:
                print("[Whisper API] Note: Streaming disabled for chunked processing")
                stream = False
            
            # Split audio into chunks
            chunk_duration = 600  # 10 minutes per chunk
            chunk_paths = split_audio_into_chunks(audio_path, chunk_duration)
            
            if len(chunk_paths) == 1 and chunk_paths[0] == audio_path:
                # Chunking failed, fall back to compression
                print("[Whisper API] Chunking failed, falling back to compression...")
            else:
                try:
                    # Transcribe chunks concurrently
                    chunk_results = self.transcribe_chunks_concurrent(
                        chunk_paths, 
                        chunk_duration,
                        max_workers=min(5, len(chunk_paths))  # Max 5 concurrent requests
                    )
                    
                    # Merge results
                    final_transcription = self.merge_chunk_results(chunk_results, return_timestamps)
                    
                    # Stream output if requested
                    if stream and final_transcription:
                        self._stream_text(final_transcription)
                    
                    return final_transcription
                    
                finally:
                    # Clean up chunk files
                    cleanup_temp_chunks(chunk_paths)
        
        # Original logic for smaller files or if chunking is not needed
        # Check and compress audio if needed
        processed_path, was_compressed = compress_audio_if_needed(audio_path)
        
        # Show progress for non-streaming mode
        progress = None
        if not stream:
            # Estimate based on file size: roughly 30 seconds per 10MB
            file_size_mb = os.path.getsize(processed_path) / (1024 * 1024)
            estimated_duration = max(10, min(60, file_size_mb * 3))  # 10-60 seconds range
            progress = create_estimated_progress("[Whisper API] Transcribing", estimated_duration)
            progress.start()
        
        try:
            with open(processed_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json" if return_timestamps else "text"
                )
            
            if progress:
                progress.complete()
            
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
        self._whisper_transcriber = None
    
    @property
    def whisper_transcriber(self):
        """Lazy initialization of WhisperAPITranscriber"""
        if self._whisper_transcriber is None:
            self._whisper_transcriber = WhisperAPITranscriber(self.config)
        return self._whisper_transcriber
    
    def transcribe(self, audio_path: str, stream: bool = False,
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Transcribe using GPT-4 models via Whisper API
        Note: GPT-4 models use the same Whisper API endpoint with chunking support
        """
        # GPT-4o models actually use Whisper API for transcription
        return self.whisper_transcriber.transcribe(audio_path, stream, return_timestamps, **kwargs)

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