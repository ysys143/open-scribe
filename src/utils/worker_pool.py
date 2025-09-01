"""
Worker Pool management for parallel processing
"""

import math
import time
import threading
from pathlib import Path
from typing import List, Callable, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import psutil

from ..config import Config


@dataclass
class ChunkResult:
    """Result from processing a single chunk"""
    index: int
    text: str
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0


class WorkerCalculator:
    """Calculate optimal number of workers based on various factors"""
    
    # Default chunk sizes in seconds for different engines
    CHUNK_SIZES = {
        'whisper-cpp': 300,          # 5 minutes
        'whisper-api': 600,          # 10 minutes
        'gpt-4o-transcribe': 600,    # 10 minutes
        'gpt-4o-mini-transcribe': 600,  # 10 minutes
        'youtube-transcript-api': 0,    # No chunking needed
    }
    
    # Estimated memory per worker in GB
    MEMORY_PER_WORKER = {
        'whisper-cpp': 2.5,          # large-v3 model
        'whisper-api': 0.1,          # API calls
        'gpt-4o-transcribe': 0.1,
        'gpt-4o-mini-transcribe': 0.1,
        'youtube-transcript-api': 0.05,
    }
    
    @staticmethod
    def calculate_optimal_workers(
        duration_seconds: int,
        engine: str,
        min_workers: int = 1,
        max_workers: int = 10
    ) -> int:
        """
        Calculate optimal number of workers based on duration and engine
        
        Args:
            duration_seconds: Total duration in seconds
            engine: Transcription engine name
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            
        Returns:
            Optimal number of workers
        """
        # Get chunk size for engine
        chunk_size = WorkerCalculator.CHUNK_SIZES.get(engine, 600)
        
        # YouTube API doesn't need workers
        if chunk_size == 0:
            return 1
        
        # Calculate total chunks
        total_chunks = math.ceil(duration_seconds / chunk_size)
        
        # Dynamic worker calculation based on chunks
        if total_chunks <= 2:
            optimal = min_workers
        elif total_chunks <= 5:
            optimal = min(3, max_workers)
        elif total_chunks <= 10:
            optimal = min(5, max_workers)
        elif total_chunks <= 20:
            optimal = min(7, max_workers)
        else:
            # For very long videos: use half the chunks or max workers
            optimal = min(max(total_chunks // 2, 5), max_workers)
        
        # Adjust based on available memory
        optimal = WorkerCalculator.adjust_by_memory(optimal, engine)
        
        # Ensure within bounds
        return max(min_workers, min(optimal, max_workers))
    
    @staticmethod
    def adjust_by_memory(workers: int, engine: str) -> int:
        """
        Adjust worker count based on available system memory
        
        Args:
            workers: Proposed number of workers
            engine: Transcription engine name
            
        Returns:
            Adjusted number of workers
        """
        try:
            # Get available memory
            mem = psutil.virtual_memory()
            available_gb = mem.available / (1024 ** 3)
            
            # Get memory requirement per worker
            mem_per_worker = WorkerCalculator.MEMORY_PER_WORKER.get(engine, 1.0)
            
            # Use 70% of available memory maximum
            safe_memory_gb = available_gb * 0.7
            
            # Calculate max workers based on memory
            max_by_memory = int(safe_memory_gb / mem_per_worker)
            
            # Return minimum of proposed and memory-limited workers
            adjusted = min(workers, max_by_memory)
            
            if adjusted < workers:
                print(f"[WorkerPool] Reducing workers from {workers} to {adjusted} due to memory constraints")
                print(f"[WorkerPool] Available: {available_gb:.1f}GB, Required per worker: {mem_per_worker:.1f}GB")
            
            return max(1, adjusted)  # At least 1 worker
            
        except Exception as e:
            print(f"[WorkerPool] Warning: Could not check memory: {e}")
            return workers


class ParallelProgressMonitor:
    """Monitor progress of parallel processing"""
    
    def __init__(self, total_chunks: int, num_workers: int):
        self.total_chunks = total_chunks
        self.num_workers = num_workers
        self.completed = 0
        self.in_progress = {}
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.worker_times = {}
    
    def start_chunk(self, worker_id: int, chunk_index: int):
        """Mark a chunk as started by a worker"""
        with self.lock:
            self.in_progress[worker_id] = {
                'chunk': chunk_index,
                'start_time': time.time()
            }
    
    def complete_chunk(self, worker_id: int, chunk_index: int):
        """Mark a chunk as completed"""
        with self.lock:
            if worker_id in self.in_progress:
                start_time = self.in_progress[worker_id]['start_time']
                elapsed = time.time() - start_time
                
                # Track worker performance
                if worker_id not in self.worker_times:
                    self.worker_times[worker_id] = []
                self.worker_times[worker_id].append(elapsed)
                
                del self.in_progress[worker_id]
            
            self.completed += 1
            self._display_progress()
    
    def _display_progress(self):
        """Display current progress"""
        elapsed = time.time() - self.start_time
        
        # Calculate speed
        if self.completed > 0:
            speed = self.completed / elapsed  # chunks per second
            eta_seconds = (self.total_chunks - self.completed) / speed if speed > 0 else 0
        else:
            speed = 0
            eta_seconds = 0
        
        # Format ETA
        if eta_seconds > 0:
            eta_min = int(eta_seconds / 60)
            eta_sec = int(eta_seconds % 60)
            eta_str = f"{eta_min}m {eta_sec}s"
        else:
            eta_str = "calculating..."
        
        # Progress bar
        progress_pct = (self.completed / self.total_chunks) * 100 if self.total_chunks > 0 else 0
        bar_length = 40
        filled = int(bar_length * self.completed / self.total_chunks) if self.total_chunks > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Display
        print(f"\r[{bar}] {progress_pct:.1f}% | "
              f"{self.completed}/{self.total_chunks} chunks | "
              f"Workers: {self.num_workers} | "
              f"Speed: {speed:.1f} chunks/s | "
              f"ETA: {eta_str}", end='', flush=True)
    
    def finish(self):
        """Finalize progress display"""
        elapsed = time.time() - self.start_time
        elapsed_min = int(elapsed / 60)
        elapsed_sec = int(elapsed % 60)
        
        print(f"\n[WorkerPool] Completed {self.completed} chunks in {elapsed_min}m {elapsed_sec}s")
        
        # Show worker statistics
        if self.worker_times:
            for worker_id, times in self.worker_times.items():
                avg_time = sum(times) / len(times)
                print(f"[WorkerPool] Worker {worker_id}: Processed {len(times)} chunks, "
                      f"avg time: {avg_time:.1f}s")


class WorkerPool:
    """Manage parallel processing with multiple workers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.min_workers = config.MIN_WORKER
        self.max_workers = config.MAX_WORKER
        self.calculator = WorkerCalculator()
    
    def process_chunks(
        self,
        chunks: List[Any],
        processor_func: Callable,
        duration_seconds: int,
        engine: str,
        verbose: bool = False
    ) -> List[ChunkResult]:
        """
        Process chunks in parallel
        
        Args:
            chunks: List of chunks to process
            processor_func: Function to process each chunk
            duration_seconds: Total duration for worker calculation
            engine: Engine name for optimization
            verbose: Show detailed progress
            
        Returns:
            List of ChunkResult objects
        """
        if not chunks:
            return []
        
        # Calculate optimal workers
        optimal_workers = self.calculator.calculate_optimal_workers(
            duration_seconds,
            engine,
            self.min_workers,
            self.max_workers
        )
        
        # Limit workers to number of chunks
        num_workers = min(optimal_workers, len(chunks))
        
        if verbose:
            print(f"[WorkerPool] Processing {len(chunks)} chunks with {num_workers} workers")
            print(f"[WorkerPool] Engine: {engine}, Duration: {duration_seconds}s")
        
        # Initialize progress monitor
        progress = ParallelProgressMonitor(len(chunks), num_workers)
        
        # Process chunks in parallel
        results = [None] * len(chunks)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, chunk in enumerate(chunks):
                future = executor.submit(self._process_single_chunk, 
                                        processor_func, chunk, i, progress)
                futures[future] = i
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_index = futures[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per chunk
                    results[chunk_index] = result
                except Exception as e:
                    print(f"\n[WorkerPool] Error processing chunk {chunk_index}: {e}")
                    results[chunk_index] = ChunkResult(
                        index=chunk_index,
                        text="",
                        success=False,
                        error=str(e)
                    )
        
        progress.finish()
        
        # Return results
        return [r for r in results if r is not None]
    
    def _process_single_chunk(
        self,
        processor_func: Callable,
        chunk: Any,
        index: int,
        progress: ParallelProgressMonitor
    ) -> ChunkResult:
        """
        Process a single chunk with error handling
        
        Args:
            processor_func: Function to process the chunk
            chunk: The chunk to process
            index: Chunk index
            progress: Progress monitor
            
        Returns:
            ChunkResult object
        """
        worker_id = threading.get_ident()
        progress.start_chunk(worker_id, index)
        
        start_time = time.time()
        
        try:
            # Call processor function
            # Expected signature: processor_func(chunk, index) -> text
            text = processor_func(chunk, index)
            
            processing_time = time.time() - start_time
            
            progress.complete_chunk(worker_id, index)
            
            return ChunkResult(
                index=index,
                text=text if text else "",
                success=bool(text),
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            progress.complete_chunk(worker_id, index)
            
            return ChunkResult(
                index=index,
                text="",
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def merge_results(self, results: List[ChunkResult], separator: str = " ") -> str:
        """
        Merge chunk results in order
        
        Args:
            results: List of ChunkResult objects
            separator: String to join chunks
            
        Returns:
            Merged text
        """
        # Sort by index
        sorted_results = sorted(results, key=lambda r: r.index)
        
        # Extract successful texts
        texts = []
        failed_chunks = []
        
        for result in sorted_results:
            if result.success and result.text:
                texts.append(result.text)
            else:
                failed_chunks.append(result.index)
        
        if failed_chunks:
            print(f"[WorkerPool] Warning: Failed chunks: {failed_chunks}")
        
        return separator.join(texts)