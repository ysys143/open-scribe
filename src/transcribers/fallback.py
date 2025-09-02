"""
Fallback transcriber with automatic retry and quality degradation
"""

import time
import traceback
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from .base import BaseTranscriber
from .whisper_cpp import WhisperCppTranscriber
from .whisper_api import WhisperApiTranscriber
from .youtube_api import YouTubeTranscriptApiTranscriber
from ..utils.worker_pool import ChunkResult, ParallelProgressMonitor, WorkerPool
from ..utils.audio import split_audio_into_chunks, cleanup_temp_chunks, get_audio_duration


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""
    max_retries: int = 3
    base_retry_delay: float = 2.0  # Base delay for exponential backoff
    memory_error_keywords: List[str] = None
    network_error_keywords: List[str] = None
    
    def __post_init__(self):
        if self.memory_error_keywords is None:
            self.memory_error_keywords = [
                'memory', 'ENOMEM', 'cannot allocate', 'out of memory',
                'insufficient memory', 'malloc', 'bad_alloc'
            ]
        if self.network_error_keywords is None:
            self.network_error_keywords = [
                'timeout', 'connection', 'network', 'refused', 
                'unreachable', 'SSL', 'certificate'
            ]


class FallbackTranscriber(BaseTranscriber):
    """Transcriber with automatic fallback to lower quality engines"""
    
    # Engine chain from highest to lowest quality
    ENGINE_CHAIN = [
        ('whisper-cpp', 'high', WhisperCppTranscriber),
        ('whisper-api', 'medium', WhisperApiTranscriber),
        ('youtube-transcript-api', 'low', YouTubeTranscriptApiTranscriber)
    ]
    
    def __init__(self, config, primary_engine: str = 'whisper-cpp'):
        super().__init__(config)
        self.primary_engine = primary_engine
        self.fallback_config = FallbackConfig()
        
        # Initialize all transcribers
        self.transcribers = {}
        for engine_name, _, transcriber_class in self.ENGINE_CHAIN:
            try:
                self.transcribers[engine_name] = transcriber_class(config)
            except Exception as e:
                print(f"[FallbackTranscriber] Warning: Could not initialize {engine_name}: {e}")
    
    @property
    def name(self) -> str:
        """Get the name of this transcriber"""
        return f"Fallback ({self.primary_engine})"
    
    @property
    def requires_api_key(self) -> bool:
        """Check if primary engine requires API key"""
        if self.primary_engine in self.transcribers:
            return self.transcribers[self.primary_engine].requires_api_key
        return False
    
    def is_available(self) -> bool:
        """Check if at least one engine is available"""
        for engine_name in self.transcribers:
            if self.transcribers[engine_name].is_available():
                return True
        return False
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate fallback strategy"""
        error_str = str(error).lower()
        error_trace = traceback.format_exc().lower()
        
        # Check for memory errors
        for keyword in self.fallback_config.memory_error_keywords:
            if keyword in error_str or keyword in error_trace:
                return 'memory'
        
        # Check for network errors
        for keyword in self.fallback_config.network_error_keywords:
            if keyword in error_str or keyword in error_trace:
                return 'network'
        
        return 'general'
    
    def _should_retry(self, error_type: str, retry_count: int) -> bool:
        """Determine if we should retry based on error type"""
        if error_type == 'memory':
            return False  # No point retrying memory errors
        elif error_type == 'network':
            return retry_count < self.fallback_config.max_retries
        else:
            return retry_count < 1  # One retry for general errors
    
    def _get_retry_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay"""
        return self.fallback_config.base_retry_delay ** retry_count
    
    def transcribe_chunk_with_fallback(
        self, 
        chunk_path: str, 
        chunk_index: int,
        return_timestamps: bool = False,
        progress_callback: Optional[callable] = None
    ) -> ChunkResult:
        """
        Transcribe a chunk with automatic fallback
        
        Args:
            chunk_path: Path to audio chunk
            chunk_index: Index of the chunk
            return_timestamps: Whether to include timestamps
            progress_callback: Callback for progress updates
            
        Returns:
            ChunkResult with transcription and metadata
        """
        start_time = time.time()
        
        # Try each engine in order
        for engine_idx, (engine_name, quality, _) in enumerate(self.ENGINE_CHAIN):
            # Skip if we don't have this transcriber
            if engine_name not in self.transcribers:
                continue
            
            # Skip if this engine is not available
            if not self.transcribers[engine_name].is_available():
                if engine_idx == 0:
                    print(f"\n[Fallback] Primary engine {engine_name} not available, trying next...")
                continue
            
            # Skip youtube-api for chunk transcription (it needs full video URL)
            if engine_name == 'youtube-transcript-api':
                continue
            
            retry_count = 0
            last_error = None
            
            while True:
                try:
                    # Update progress
                    if progress_callback:
                        progress_callback(chunk_index, 0, engine_name, quality)
                    
                    # Attempt transcription
                    if self.config.VERBOSE:
                        print(f"\n[Fallback] Chunk {chunk_index}: Trying {engine_name} (attempt {retry_count + 1})")
                    
                    result = self.transcribers[engine_name].transcribe(
                        chunk_path,
                        stream=False,
                        return_timestamps=return_timestamps,
                        use_parallel=False  # Already in parallel context
                    )
                    
                    if result:
                        # Success!
                        processing_time = time.time() - start_time
                        
                        if engine_idx > 0 or retry_count > 0:
                            fallback_reason = f"Fallback from failed engine" if engine_idx > 0 else f"Retry {retry_count}"
                            print(f"\n✓ Chunk {chunk_index}: Success with {engine_name} ({fallback_reason})")
                        
                        return ChunkResult(
                            index=chunk_index,
                            text=result,
                            success=True,
                            processing_time=processing_time,
                            engine_used=engine_name,
                            quality_level=quality,
                            retry_count=retry_count,
                            fallback_reason=fallback_reason if engine_idx > 0 else None
                        )
                    else:
                        raise Exception("Empty transcription result")
                        
                except Exception as e:
                    last_error = e
                    error_type = self._classify_error(e)
                    
                    if self._should_retry(error_type, retry_count):
                        retry_count += 1
                        delay = self._get_retry_delay(retry_count)
                        print(f"\n⚠️ Chunk {chunk_index}: {engine_name} failed ({error_type}), retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        # Move to next engine
                        if engine_idx < len(self.ENGINE_CHAIN) - 1:
                            print(f"\n⚠️ Chunk {chunk_index}: {engine_name} failed ({error_type}), trying fallback...")
                        break
        
        # All engines failed
        processing_time = time.time() - start_time
        print(f"\n✗ Chunk {chunk_index}: All engines failed. Last error: {last_error}")
        
        return ChunkResult(
            index=chunk_index,
            text="",
            success=False,
            error=str(last_error),
            processing_time=processing_time,
            engine_used=None,
            quality_level='failed',
            retry_count=retry_count,
            fallback_reason="All engines failed"
        )
    
    def transcribe(
        self, 
        audio_file: str, 
        stream: bool = False,
        return_timestamps: bool = False,
        use_parallel: bool = True
    ) -> Optional[str]:
        """
        Transcribe with automatic fallback
        
        For full file transcription, try primary engine first,
        then fall back if needed.
        """
        # For non-parallel or small files, use simple fallback
        duration = get_audio_duration(audio_file)
        
        if not use_parallel or duration < 600:  # Less than 10 minutes
            # Try each engine in order
            for engine_name, quality, _ in self.ENGINE_CHAIN:
                if engine_name not in self.transcribers:
                    continue
                
                if not self.transcribers[engine_name].is_available():
                    continue
                
                try:
                    print(f"[Fallback] Trying {engine_name}...")
                    result = self.transcribers[engine_name].transcribe(
                        audio_file,
                        stream=stream,
                        return_timestamps=return_timestamps,
                        use_parallel=False
                    )
                    
                    if result:
                        return result
                        
                except Exception as e:
                    print(f"[Fallback] {engine_name} failed: {e}")
                    continue
            
            return None
        
        # For large files, use parallel processing with fallback
        return self._transcribe_parallel_with_fallback(
            audio_file,
            return_timestamps
        )
    
    def _transcribe_parallel_with_fallback(
        self,
        audio_file: str,
        return_timestamps: bool = False
    ) -> Optional[str]:
        """Parallel transcription with per-chunk fallback"""
        
        # Split audio into chunks
        chunk_duration = 300  # 5 minutes
        print(f"[Fallback] Splitting audio into {chunk_duration}s chunks...")
        chunk_paths = split_audio_into_chunks(audio_file, chunk_duration_seconds=chunk_duration)
        
        if not chunk_paths:
            print("[Fallback] Failed to split audio")
            return None
        
        print(f"[Fallback] Created {len(chunk_paths)} chunks")
        
        # Initialize worker pool
        worker_pool = WorkerPool(self.config)
        duration = get_audio_duration(audio_file)
        
        # Process chunks with fallback
        results = worker_pool.process_chunks(
            chunks=chunk_paths,
            processor_func=lambda chunk, idx: self.transcribe_chunk_with_fallback(
                chunk, idx, return_timestamps
            ),
            duration_seconds=int(duration),
            engine='fallback',
            verbose=self.config.VERBOSE
        )
        
        # Generate quality report
        self._generate_quality_report(results)
        
        # Merge results
        if return_timestamps:
            merged = self._merge_timestamped_results(results, chunk_duration)
        else:
            merged = worker_pool.merge_results(results, separator=" ")
        
        # Cleanup
        cleanup_temp_chunks(chunk_paths, keep_for_debug=self.config.VERBOSE)
        
        return merged if merged else None
    
    def _generate_quality_report(self, results: List[ChunkResult]):
        """Generate and display quality report"""
        total_chunks = len(results)
        successful_chunks = sum(1 for r in results if r.success)
        
        # Count by engine
        engine_counts = {}
        quality_counts = {'high': 0, 'medium': 0, 'low': 0, 'failed': 0}
        fallback_chunks = []
        
        for result in results:
            if result.success:
                engine = result.engine_used or 'unknown'
                engine_counts[engine] = engine_counts.get(engine, 0) + 1
                quality_counts[result.quality_level] = quality_counts.get(result.quality_level, 0) + 1
                
                if result.fallback_reason:
                    fallback_chunks.append((result.index, result.fallback_reason))
        
        # Calculate overall quality score
        quality_score = (
            quality_counts['high'] * 100 +
            quality_counts['medium'] * 70 +
            quality_counts['low'] * 40
        ) / total_chunks if total_chunks > 0 else 0
        
        # Determine quality rating
        if quality_score >= 90:
            quality_rating = "Excellent"
        elif quality_score >= 70:
            quality_rating = "Good"
        elif quality_score >= 50:
            quality_rating = "Moderate"
        else:
            quality_rating = "Degraded"
        
        # Display report
        print("\n" + "=" * 60)
        print("📊 Transcription Quality Report")
        print("=" * 60)
        print(f"✓ Successfully transcribed: {successful_chunks}/{total_chunks} chunks")
        print(f"📈 Overall quality: {quality_score:.0f}% ({quality_rating})")
        
        if engine_counts:
            print("\n🔧 Engine usage:")
            for engine, count in sorted(engine_counts.items()):
                quality = next((q for e, q, _ in self.ENGINE_CHAIN if e == engine), 'unknown')
                percentage = (count / total_chunks) * 100
                print(f"  - {engine} ({quality}): {count} chunks ({percentage:.0f}%)")
        
        if fallback_chunks:
            print(f"\n⚠️ {len(fallback_chunks)} chunks used fallback:")
            for chunk_idx, reason in fallback_chunks[:5]:  # Show first 5
                print(f"  - Chunk {chunk_idx + 1}: {reason}")
            if len(fallback_chunks) > 5:
                print(f"  ... and {len(fallback_chunks) - 5} more")
        
        if quality_rating == "Degraded":
            print("\n💡 Tip: Consider re-running with different settings or checking system resources")
        
        print("=" * 60)
    
    def _merge_timestamped_results(self, results: List[ChunkResult], chunk_duration: int) -> str:
        """Merge timestamped results with quality indicators"""
        merged_lines = []
        
        for result in sorted(results, key=lambda r: r.index):
            if not result.success or not result.text:
                continue
            
            # Add quality indicator at chunk boundaries
            quality_marker = {
                'high': '✓',
                'medium': '⚠',
                'low': '⚡',
                'failed': '✗'
            }.get(result.quality_level, '')
            
            if quality_marker and result.index > 0:
                merged_lines.append(f"\n[Chunk {result.index + 1} - {result.engine_used} {quality_marker}]")
            
            # Calculate time offset for this chunk
            time_offset = result.index * chunk_duration
            
            # Process chunk text (simplified, you may need to adjust timestamps)
            merged_lines.append(result.text)
        
        return '\n'.join(merged_lines)