#!/usr/bin/env python
"""Test worker optimization logic"""

from src.utils.worker_pool import WorkerCalculator

def test_worker_calculation():
    """Test various duration scenarios"""
    
    test_cases = [
        # (duration, engine, expected description)
        (972, 'whisper-cpp', "16min video -> 4 chunks"),
        (1800, 'whisper-cpp', "30min video -> 6 chunks"),
        (600, 'whisper-cpp', "10min video -> 2 chunks"),
        (1500, 'whisper-cpp', "25min video -> 5 chunks"),
        (3600, 'whisper-cpp', "60min video -> 12 chunks"),
    ]
    
    print("Worker Optimization Test Results")
    print("=" * 60)
    
    for duration, engine, description in test_cases:
        # Default chunk size calculation
        chunk_size = WorkerCalculator.CHUNK_SIZES[engine]
        import math
        total_chunks = math.ceil(duration / chunk_size)
        
        # Calculate optimal workers
        workers = WorkerCalculator.calculate_optimal_workers(
            duration, engine, min_workers=1, max_workers=10
        )
        
        # Check if workers is a divisor
        is_divisor = (total_chunks % workers == 0) if workers > 0 else False
        chunks_per_worker = total_chunks / workers if workers > 0 else 0
        
        print(f"\n{description}")
        print(f"  Duration: {duration}s")
        print(f"  Chunks: {total_chunks} (@ {chunk_size}s each)")
        print(f"  Workers: {workers}")
        print(f"  Divisor: {'✓' if is_divisor else '✗'}")
        print(f"  Chunks/Worker: {chunks_per_worker:.1f}")
        
        # Test adaptive chunk sizing
        adaptive_chunk, expected_chunks = WorkerCalculator.calculate_adaptive_chunk_size(
            duration, engine, target_workers=workers
        )
        print(f"  Adaptive: {expected_chunks} chunks @ {adaptive_chunk}s")

if __name__ == "__main__":
    test_worker_calculation()