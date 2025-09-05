#!/usr/bin/env python3
"""Test parallel processing to diagnose the issue"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_chunk(chunk_id):
    """Simulate chunk processing"""
    print(f"Starting chunk {chunk_id} on thread {threading.get_ident()}")
    time.sleep(2)  # Simulate work
    print(f"Completed chunk {chunk_id}")
    return f"Result_{chunk_id}"

def main():
    chunks = list(range(6))
    num_workers = 3
    
    print(f"Processing {len(chunks)} chunks with {num_workers} workers")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for i in chunks:
            future = executor.submit(process_chunk, i)
            futures[future] = i
            print(f"Submitted chunk {i}")
        
        print(f"All chunks submitted, waiting for completion...")
        
        for future in as_completed(futures):
            chunk_id = futures[future]
            try:
                result = future.result(timeout=10)
                print(f"Got result for chunk {chunk_id}: {result}")
            except Exception as e:
                print(f"Error in chunk {chunk_id}: {e}")
    
    print("All done!")

if __name__ == "__main__":
    main()