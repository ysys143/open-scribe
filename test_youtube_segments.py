#!/usr/bin/env python
"""
Test script to improve YouTube transcript segment merging
Focus on post-processing the output from existing module
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transcribers.youtube import YouTubeTranscriptAPITranscriber
from src.config import Config


def merge_timestamp_lines_by_sentence(transcript_with_timestamps):
    """
    Merge timestamp lines that are too short into sentence-based chunks
    
    Input format: 
    [00:00] text1
    [00:02] text2
    [00:04] text3.
    [00:06] text4
    
    Output format:
    [00:00] text1 text2 text3.
    [00:06] text4
    """
    if not transcript_with_timestamps:
        return None
    
    lines = transcript_with_timestamps.strip().split('\n')
    merged_lines = []
    current_segment = {
        'timestamp': None,
        'text': ''
    }
    
    for line in lines:
        # Parse timestamp and text
        match = re.match(r'\[([^\]]+)\]\s*(.*)', line)
        if not match:
            continue
        
        timestamp, text = match.groups()
        text = text.strip()
        
        if not text:
            continue
        
        # If this is the first segment
        if current_segment['timestamp'] is None:
            current_segment['timestamp'] = timestamp
            current_segment['text'] = text
        else:
            # Add to current segment
            current_segment['text'] += ' ' + text
        
        # Check if we should split here (sentence ending)
        if text.endswith(('.', '!', '?', '。', '！', '？')):
            # Save the completed sentence
            merged_lines.append(f"[{current_segment['timestamp']}] {current_segment['text']}")
            current_segment = {
                'timestamp': None,
                'text': ''
            }
    
    # Don't forget the last segment
    if current_segment['text']:
        merged_lines.append(f"[{current_segment['timestamp']}] {current_segment['text']}")
    
    return '\n'.join(merged_lines)


def merge_timestamp_lines_smart(transcript_with_timestamps, max_chars=200):
    """
    Smart merge: combine until sentence end OR character limit
    """
    if not transcript_with_timestamps:
        return None
    
    lines = transcript_with_timestamps.strip().split('\n')
    merged_lines = []
    current_segment = {
        'timestamp': None,
        'text': '',
        'parts': 0
    }
    
    for line in lines:
        # Parse timestamp and text
        match = re.match(r'\[([^\]]+)\]\s*(.*)', line)
        if not match:
            continue
        
        timestamp, text = match.groups()
        text = text.strip()
        
        if not text:
            continue
        
        # Check if adding this would exceed limits
        potential_length = len(current_segment['text']) + len(text) + 1
        
        # Decide whether to start new segment
        should_split = False
        
        if current_segment['text']:  # If we have existing content
            # Split if sentence ends
            if current_segment['text'].endswith(('.', '!', '?', '。', '！', '？')):
                should_split = True
            # Or if adding this would make it too long
            elif potential_length > max_chars:
                should_split = True
        
        if should_split and current_segment['text']:
            # Save current segment
            merged_lines.append(f"[{current_segment['timestamp']}] {current_segment['text']} ({current_segment['parts']} parts)")
            # Start new segment
            current_segment = {
                'timestamp': timestamp,
                'text': text,
                'parts': 1
            }
        else:
            # Add to current segment
            if current_segment['timestamp'] is None:
                current_segment['timestamp'] = timestamp
                current_segment['text'] = text
            else:
                current_segment['text'] += ' ' + text
            current_segment['parts'] += 1
    
    # Don't forget the last segment
    if current_segment['text']:
        merged_lines.append(f"[{current_segment['timestamp']}] {current_segment['text']} ({current_segment['parts']} parts)")
    
    return '\n'.join(merged_lines)


def test_merge_methods(url):
    """Test different merging methods on existing transcriber output"""
    print("=" * 60)
    print("Testing YouTube Transcript Segment Merging")
    print("=" * 60)
    
    config = Config()
    transcriber = YouTubeTranscriptAPITranscriber(config)
    
    # Get transcript with timestamps using existing module
    print("\n1. Getting transcript with timestamps (current implementation):")
    print("-" * 40)
    
    result_with_timestamps = transcriber.transcribe(url, return_timestamps=True)
    
    if not result_with_timestamps:
        print("Failed to get transcript")
        return
    
    # Show sample of original output
    lines = result_with_timestamps.split('\n')
    print(f"Total lines: {len(lines)}")
    print("\nFirst 20 lines (original):")
    for line in lines[:20]:
        print(line)
    
    # Test merging method 1: By sentence
    print("\n2. Merged by sentence endings:")
    print("-" * 40)
    
    merged_by_sentence = merge_timestamp_lines_by_sentence(result_with_timestamps)
    merged_lines = merged_by_sentence.split('\n')
    
    print(f"Merged to {len(merged_lines)} lines (from {len(lines)})")
    print(f"Reduction: {len(lines)/len(merged_lines):.1f}x")
    print("\nFirst 10 merged lines:")
    for line in merged_lines[:10]:
        # Truncate long lines for display
        if len(line) > 120:
            print(line[:117] + "...")
        else:
            print(line)
    
    # Test merging method 2: Smart merge
    print("\n3. Smart merge (sentence + length limit):")
    print("-" * 40)
    
    smart_merged = merge_timestamp_lines_smart(result_with_timestamps, max_chars=150)
    smart_lines = smart_merged.split('\n')
    
    print(f"Smart merged to {len(smart_lines)} lines (from {len(lines)})")
    print(f"Reduction: {len(lines)/len(smart_lines):.1f}x")
    print("\nFirst 10 smart-merged lines:")
    for line in smart_lines[:10]:
        # Truncate long lines for display
        if len(line) > 120:
            print(line[:117] + "...")
        else:
            print(line)
    
    # Statistics
    print("\n4. Comparison:")
    print("-" * 40)
    print(f"Original lines: {len(lines)}")
    print(f"Sentence-merged: {len(merged_lines)} (reduction: {len(lines)/len(merged_lines):.1f}x)")
    print(f"Smart-merged: {len(smart_lines)} (reduction: {len(lines)/len(smart_lines):.1f}x)")
    
    # Calculate average line lengths
    orig_avg_len = sum(len(line) for line in lines) / len(lines) if lines else 0
    sentence_avg_len = sum(len(line) for line in merged_lines) / len(merged_lines) if merged_lines else 0
    smart_avg_len = sum(len(line) for line in smart_lines) / len(smart_lines) if smart_lines else 0
    
    print(f"\nAverage line length:")
    print(f"  Original: {orig_avg_len:.1f} chars")
    print(f"  Sentence-merged: {sentence_avg_len:.1f} chars")
    print(f"  Smart-merged: {smart_avg_len:.1f} chars")


if __name__ == "__main__":
    # Test URL
    test_url = "https://youtu.be/3kAeA0pwoaQ"
    
    test_merge_methods(test_url)