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
        
        # For small number of chunks, use chunk count as worker count
        if total_chunks <= max_workers:
            # Find divisors of total_chunks that are within worker bounds
            divisors = []
            for i in range(min_workers, min(total_chunks + 1, max_workers + 1)):
                if total_chunks % i == 0:
                    divisors.append(i)
            
            # If we have divisors, prefer the largest one for better parallelism
            if divisors:
                optimal = divisors[-1]
            else:
                # No perfect divisor, use chunk count if within bounds
                optimal = min(total_chunks, max_workers)
        else:
            # For large number of chunks, find best divisor within max_workers
            divisors = []
            for i in range(min_workers, max_workers + 1):
                if total_chunks % i == 0:
                    divisors.append(i)
            
            if divisors:
                # Prefer divisors that give reasonable chunks per worker (2-10)
                best_divisor = max_workers
                for d in reversed(divisors):
                    chunks_per_worker = total_chunks // d
                    if 2 <= chunks_per_worker <= 10:
                        best_divisor = d
                        break
                optimal = best_divisor
            else:
                # No perfect divisor, use heuristic
                if total_chunks <= 20:
                    optimal = min(7, max_workers)
                else:
                    # For very long videos: use a reasonable number
                    optimal = min(max(total_chunks // 4, 5), max_workers)
        
        # Adjust based on available memory
        optimal = WorkerCalculator.adjust_by_memory(optimal, engine)
        
        # Ensure within bounds
        return max(min_workers, min(optimal, max_workers))
    
    @staticmethod
    def calculate_adaptive_chunk_size(
        duration_seconds: int,
        engine: str,
        target_workers: int = None,
        min_chunks: int = 2,
        max_chunk_size: int = 1200  # 20 minutes max
    ) -> tuple[int, int]:
        """
        Calculate adaptive chunk size to optimize worker utilization
        
        Args:
            duration_seconds: Total duration in seconds
            engine: Transcription engine name
            target_workers: Desired number of workers (None for auto)
            min_chunks: Minimum number of chunks to create
            max_chunk_size: Maximum chunk size in seconds
            
        Returns:
            tuple: (chunk_size, expected_chunks)
        """
        default_chunk_size = WorkerCalculator.CHUNK_SIZES.get(engine, 600)
        
        # If no target workers specified, use default chunk size
        if target_workers is None:
            chunk_size = min(default_chunk_size, max_chunk_size)
            expected_chunks = math.ceil(duration_seconds / chunk_size)
            return chunk_size, expected_chunks
        
        # Calculate ideal chunk size for target workers
        ideal_chunk_size = duration_seconds / target_workers
        
        # Constrain to reasonable bounds
        min_chunk_size = max(60, duration_seconds // (target_workers * 10))  # At least 1 minute
        max_allowed = min(default_chunk_size * 2, max_chunk_size)
        
        # Round to nearest 30 seconds for cleaner chunks
        chunk_size = round(ideal_chunk_size / 30) * 30
        chunk_size = max(min_chunk_size, min(chunk_size, max_allowed))
        
        expected_chunks = math.ceil(duration_seconds / chunk_size)
        
        # Verify we have reasonable distribution
        if expected_chunks < min_chunks:
            # Too few chunks, reduce chunk size
            chunk_size = duration_seconds // min_chunks
            chunk_size = round(chunk_size / 30) * 30
            expected_chunks = math.ceil(duration_seconds / chunk_size)
        
        return chunk_size, expected_chunks
    
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
        self.chunk_progress = {}  # Track progress within each chunk
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.worker_times = {}
        self.last_display_time = 0
        self.display_interval = 0.1  # Update display every 100ms max
    
    def start_chunk(self, worker_id: int, chunk_index: int):
        """Mark a chunk as started by a worker"""
        with self.lock:
            self.in_progress[worker_id] = {
                'chunk': chunk_index,
                'start_time': time.time()
            }
            self.chunk_progress[chunk_index] = 0  # Initialize chunk progress at 0%
    
    def update_chunk_progress(self, chunk_index: int, progress: float):
        """Update progress for a specific chunk (0-100)"""
        with self.lock:
            self.chunk_progress[chunk_index] = min(100, max(0, progress))
            # Only update display if enough time has passed
            current_time = time.time()
            if current_time - self.last_display_time > self.display_interval:
                self._display_progress()
                self.last_display_time = current_time
    
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
            
            # Mark chunk as 100% complete
            if chunk_index in self.chunk_progress:
                self.chunk_progress[chunk_index] = 100
            
            self.completed += 1
            self._display_progress()
    
    def _display_progress(self):
        """Display current progress with two-level detail"""
        elapsed = time.time() - self.start_time
        
        # Calculate total progress including partial chunks
        total_progress = self.completed
        for chunk_idx, progress in self.chunk_progress.items():
            if progress < 100:  # Only add partial progress for incomplete chunks
                total_progress += progress / 100.0
        
        # Calculate overall percentage
        overall_pct = (total_progress / self.total_chunks * 100) if self.total_chunks > 0 else 0
        
        # Calculate speed and ETA
        if total_progress > 0:
            speed = total_progress / elapsed  # chunks per second
            remaining = self.total_chunks - total_progress
            eta_seconds = remaining / speed if speed > 0 else 0
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
        
        # Build display lines
        lines = []
        
        # Overall progress bar
        bar_length = 40
        filled = int(bar_length * overall_pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Main status line (convert speed to per minute for readability)
        speed_per_min = speed * 60 if speed > 0 else 0
        main_line = (f"Overall: [{bar}] {overall_pct:.1f}% ({total_progress:.1f}/{self.total_chunks} chunks) | "
                    f"Speed: {speed_per_min:.2f} chunks/min | ETA: {eta_str}")
        
        # Worker details (only show active workers)
        worker_lines = []
        for worker_id, info in self.in_progress.items():
            chunk_idx = info['chunk']
            chunk_pct = self.chunk_progress.get(chunk_idx, 0)
            # Mini progress bar for each worker
            mini_bar_length = 10
            mini_filled = int(mini_bar_length * chunk_pct / 100)
            mini_bar = '█' * mini_filled + '░' * (mini_bar_length - mini_filled)
            worker_lines.append(f"  Worker {worker_id % 1000:02d}: Chunk {chunk_idx + 1:3d} [{mini_bar}] {chunk_pct:3.0f}%")
        
        # Clear previous lines and print new ones
        # Use \r to return to start of line, then clear with spaces
        clear_line = ' ' * 100
        
        # Print main line
        print(f"\r{clear_line}\r{main_line}", end='', flush=True)
        
        # If we have active workers and verbose mode, show them on next lines
        if worker_lines and len(self.in_progress) > 0:
            # Note: Multi-line progress is tricky in terminal, keeping single line for now
            # Could be enhanced with terminal control codes later
            pass
    
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
        verbose: bool = False,
        progress_monitor: Optional[ParallelProgressMonitor] = None
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
        
        # Initialize progress monitor (use provided or create new)
        progress = progress_monitor if progress_monitor else ParallelProgressMonitor(len(chunks), num_workers)
        self.progress = progress  # Store for access by processor functions
        
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