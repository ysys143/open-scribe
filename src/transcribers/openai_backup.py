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

class WhisperAPITranscriber(OpenAITranscriber):
    """OpenAI Whisper API transcriber"""
    
    def __init__(self, config):
        super().__init__(config, model_name="whisper-1", display_name="Whisper API")
    
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
                # GPT-4o models don't support verbose_json, use text instead
                if self.model_name.startswith('gpt-4o'):
                    response_format = "text"
                else:
                    response_format = "verbose_json"
                    
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    response_format=response_format
                )
                
                # Debug: Log the response type and content
                if self.config.DEFAULT_VERBOSE:
                    print(f"[{self.display_name}] Chunk {chunk_index + 1} response type: {type(transcription)}")
                    if hasattr(transcription, '__dict__'):
                        print(f"[{self.display_name}] Chunk {chunk_index + 1} attributes: {transcription.__dict__.keys() if hasattr(transcription.__dict__, 'keys') else transcription.__dict__}")
            
            # Handle different response types based on model
            if isinstance(transcription, str):
                # GPT-4o models with text format return a string directly
                result = {
                    'text': transcription,
                    'segments': []
                }
                print(f"[{self.display_name}] Chunk {chunk_index + 1}: Received string response, length: {len(transcription)}")
            elif hasattr(transcription, 'text'):
                # Whisper models return an object with text attribute
                result = {
                    'text': transcription.text,
                    'segments': []
                }
                print(f"[{self.display_name}] Chunk {chunk_index + 1}: Received object with text, length: {len(transcription.text)}")
            else:
                # Handle unexpected response format - this might be a direct response object
                # Try to access the text directly from the response
                text = ""
                if hasattr(transcription, 'model_dump'):
                    # Pydantic model response
                    data = transcription.model_dump()
                    text = data.get('text', '')
                    print(f"[{self.display_name}] Chunk {chunk_index + 1}: Pydantic model response, text length: {len(text)}")
                elif hasattr(transcription, 'to_dict'):
                    # Dictionary-like response
                    data = transcription.to_dict()
                    text = data.get('text', '')
                    print(f"[{self.display_name}] Chunk {chunk_index + 1}: Dict response, text length: {len(text)}")
                else:
                    # Last resort: convert to string
                    text = str(transcription)
                    print(f"[{self.display_name}] Chunk {chunk_index + 1}: Fallback to str(), length: {len(text)}")
                
                result = {
                    'text': text,
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
            print(f"[{self.display_name}] ❌ Error transcribing chunk {chunk_index + 1}: {e}")
            import traceback
            if os.getenv('OPEN_SCRIBE_VERBOSE') == 'true':
                traceback.print_exc()
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
        
        print(f"[{self.display_name}] Transcribing {len(chunk_paths)} chunks with {max_workers} workers...")
        
        # Use a single consolidated progress bar for all chunks
        from ..utils.progress import ChunkedProgressBar
        progress = ChunkedProgressBar(
            total_chunks=len(chunk_paths),
            estimated_per_chunk=30.0,  # 30 seconds per chunk
            display_name=self.display_name
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
        # Check how many chunks actually have content
        chunks_with_content = sum(1 for r in results if r and r.get('text'))
        print(f"[{self.display_name}] Completed: {chunks_with_content}/{len(chunk_paths)} chunks have content")
        
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
        failed_chunks = len(chunk_results) - len(valid_results)
        
        if failed_chunks > 0:
            print(f"[{self.display_name}] ⚠️  {failed_chunks} chunk(s) failed to transcribe")
        
        if not valid_results:
            print(f"[{self.display_name}] ❌ All chunks failed - no transcription available")
            return ""
        
        # Debug: Show what we got from each chunk
        print(f"[{self.display_name}] Processing {len(valid_results)} valid chunks:")
        for i, result in enumerate(valid_results):
            if result and 'text' in result:
                text_preview = result['text'][:100] if result['text'] else "(empty)"
                print(f"  Chunk {i+1}: {len(result['text'])} chars - Preview: {text_preview}...")
            else:
                print(f"  Chunk {i+1}: No 'text' field found")
        
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
            
            merged = ' '.join(texts)
            if not merged and valid_results:
                print(f"[{self.display_name}] Debug: Valid results exist but no text found")
                print(f"[{self.display_name}] Debug: Result sample: {str(valid_results[0])[:200] if valid_results else 'None'}")
                print(f"[{self.display_name}] Debug: Result keys: {valid_results[0].keys() if valid_results and isinstance(valid_results[0], dict) else 'Not a dict'}")
                # Try to extract text from raw results if standard extraction failed
                for i, result in enumerate(valid_results):
                    if result:
                        print(f"[{self.display_name}] Debug: Chunk {i+1} type: {type(result)}")
                        if isinstance(result, str):
                            texts.append(result.strip())
                        elif hasattr(result, '__str__'):
                            raw_text = str(result).strip()
                            if raw_text and raw_text != 'None':
                                texts.append(raw_text)
                merged = ' '.join(texts)
            return merged
    
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
            print(f"[{self.display_name}] Error: OpenAI API key not configured")
            return None
        
        if not self.validate_audio_file(audio_path):
            print(f"[{self.display_name}] Error: Audio file not found: {audio_path}")
            return None
        
        print(f"[{self.display_name}] Processing: {audio_path}")
        
        # Check if chunking is needed
        if should_use_chunking(audio_path):
            print(f"[{self.display_name}] File is large, using chunking strategy...")
            
            # Automatically disable stream mode for chunking
            if stream:
                print(f"[{self.display_name}] Note: Streaming disabled for chunked processing")
                stream = False
            
            # Split audio into chunks
            chunk_duration = 600  # 10 minutes per chunk
            chunk_paths = split_audio_into_chunks(audio_path, chunk_duration)
            
            if len(chunk_paths) == 1 and chunk_paths[0] == audio_path:
                # Chunking failed, fall back to compression
                print(f"[{self.display_name}] Chunking failed, falling back to compression...")
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
                    
                    if not final_transcription or not final_transcription.strip():
                        print(f"[{self.display_name}] ❌ Failed to merge chunk results")
                        return None
                    
                    # Stream output if requested
                    if stream and final_transcription:
                        self._stream_text(final_transcription)
                    
                    return final_transcription
                    
                finally:
                    # Clean up chunk files (keep for debugging if verbose mode)
                    keep_chunks = os.getenv('OPEN_SCRIBE_VERBOSE') == 'true'
                    cleanup_temp_chunks(chunk_paths, keep_for_debug=keep_chunks)
        
        # Original logic for smaller files or if chunking is not needed
        # Check and compress audio if needed
        processed_path, was_compressed = compress_audio_if_needed(audio_path)
        
        # Show progress for non-streaming mode
        progress = None
        if not stream:
            # Estimate based on file size: roughly 30 seconds per 10MB
            file_size_mb = os.path.getsize(processed_path) / (1024 * 1024)
            estimated_duration = max(10, min(60, file_size_mb * 3))  # 10-60 seconds range
            progress = create_estimated_progress(f"[{self.display_name}] Transcribing", estimated_duration)
            progress.start()
        
        try:
            with open(processed_path, "rb") as audio_file:
                # GPT-4o models don't support verbose_json
                if self.model_name.startswith('gpt-4o'):
                    response_format = "text"
                else:
                    response_format = "verbose_json" if return_timestamps else "text"
                    
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    response_format=response_format
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
            print(f"[{self.display_name}] Error: {e}")
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
            print(f"[{self.display_name}] Streaming transcription...")
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
    """GPT-4o transcriber using the new GPT-4o-transcribe model"""
    
    def __init__(self, config):
        # Initialize with GPT-4o-transcribe model
        super().__init__(config)
        self.model_name = "gpt-4o-transcribe"
        self.display_name = "GPT-4o"
    
    @property
    def name(self) -> str:
        return "gpt-4o-transcribe"

class GPT4OMiniTranscriber(WhisperAPITranscriber):
    """GPT-4o-mini transcriber using the new GPT-4o-mini-transcribe model"""
    
    def __init__(self, config):
        # Initialize with GPT-4o-mini-transcribe model
        super().__init__(config)
        self.model_name = "gpt-4o-mini-transcribe"
        self.display_name = "GPT-4o-mini"
    
    @property
    def name(self) -> str:
        return "gpt-4o-mini-transcribe"