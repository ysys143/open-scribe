#!/usr/bin/env python
"""
Test script to improve YouTube transcript segment merging
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transcribers.youtube import YouTubeTranscriptAPITranscriber
from src.config import Config

def format_timestamp(seconds):
    """Format seconds to MM:SS or HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def merge_segments_by_sentence(segments, min_duration=2.0):
    """
    Merge short segments into complete sentences based on punctuation
    
    Args:
        segments: List of segment dictionaries with 'text', 'start', 'duration'
        min_duration: Minimum duration for a segment (seconds)
    """
    merged = []
    current = {
        'text': '',
        'start': None,
        'duration': 0,
        'parts': []
    }
    
    for seg in segments:
        text = seg['text'].strip()
        if not text:
            continue
        
        # Initialize start time
        if current['start'] is None:
            current['start'] = seg['start']
        
        # Add text
        if current['text']:
            current['text'] += ' ' + text
        else:
            current['text'] = text
        
        # Update duration
        current['duration'] = (seg['start'] + seg.get('duration', 0)) - current['start']
        current['parts'].append(seg)
        
        # Check if we should split here
        should_split = False
        
        # Split on sentence endings
        if text.endswith(('.', '!', '?', '。', '！', '？')):
            # But only if we've accumulated enough duration
            if current['duration'] >= min_duration:
                should_split = True
        # Or split if duration is getting too long (>15 seconds)
        elif current['duration'] > 15:
            should_split = True
        
        if should_split:
            merged.append({
                'text': current['text'],
                'start': current['start'],
                'duration': current['duration'],
                'part_count': len(current['parts'])
            })
            current = {
                'text': '',
                'start': None,
                'duration': 0,
                'parts': []
            }
    
    # Don't forget the last segment
    if current['text']:
        merged.append({
            'text': current['text'],
            'start': current['start'],
            'duration': current['duration'],
            'part_count': len(current['parts'])
        })
    
    return merged


def test_transcriber_with_timestamps(url):
    """Test the existing transcriber with timestamp output"""
    print("=" * 60)
    print("Testing YouTube Transcript API with timestamps")
    print("=" * 60)
    
    config = Config()
    transcriber = YouTubeTranscriptAPITranscriber(config)
    
    # Test 1: Get raw segments (internal method)
    print("\n1. Getting raw segments from YouTube API...")
    
    from youtube_transcript_api import YouTubeTranscriptApi
    from src.utils.validators import extract_video_id
    
    video_id = extract_video_id(url)
    print(f"Video ID: {video_id}")
    
    # Get transcript directly
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    
    # Try to find a transcript
    transcript = None
    for t in transcript_list:
        transcript = t
        print(f"Found transcript: {t.language} ({t.language_code}), Generated: {t.is_generated}")
        break
    
    if transcript:
        raw_segments = transcript.fetch()
        
        print(f"\nTotal segments: {len(raw_segments)}")
        print("\nFirst 10 raw segments:")
        print("-" * 40)
        for i, seg in enumerate(raw_segments[:10]):
            print(f"[{i:2d}] {seg['start']:6.2f}s ({seg.get('duration', 0):4.2f}s): {seg['text']}")
        
        # Test 2: Current timestamp implementation
        print("\n2. Current implementation (with timestamps):")
        print("-" * 40)
        result_with_ts = transcriber.transcribe(url, return_timestamps=True)
        if result_with_ts:
            lines = result_with_ts.split('\n')[:10]
            for line in lines:
                print(line)
        
        # Test 3: Improved merging
        print("\n3. Improved sentence-based merging:")
        print("-" * 40)
        merged_segments = merge_segments_by_sentence(raw_segments)
        
        print(f"Merged from {len(raw_segments)} to {len(merged_segments)} segments")
        print("\nFirst 10 merged segments:")
        for i, seg in enumerate(merged_segments[:10]):
            timestamp = format_timestamp(seg['start'])
            print(f"[{timestamp}] ({seg['part_count']} parts, {seg['duration']:.1f}s): {seg['text'][:100]}...")
        
        # Statistics
        print("\n4. Statistics:")
        print("-" * 40)
        
        # Original segments
        orig_durations = [s.get('duration', 0) for s in raw_segments]
        avg_orig_duration = sum(orig_durations) / len(orig_durations) if orig_durations else 0
        
        # Merged segments
        merged_durations = [s['duration'] for s in merged_segments]
        avg_merged_duration = sum(merged_durations) / len(merged_durations) if merged_durations else 0
        
        print(f"Original segments: {len(raw_segments)}")
        print(f"  Average duration: {avg_orig_duration:.2f}s")
        print(f"  Min duration: {min(orig_durations):.2f}s")
        print(f"  Max duration: {max(orig_durations):.2f}s")
        
        print(f"\nMerged segments: {len(merged_segments)}")
        print(f"  Average duration: {avg_merged_duration:.2f}s")
        print(f"  Min duration: {min(merged_durations):.2f}s")
        print(f"  Max duration: {max(merged_durations):.2f}s")
        print(f"  Reduction ratio: {len(raw_segments)/len(merged_segments):.1f}x")


if __name__ == "__main__":
    # Test URL
    test_url = "https://youtu.be/3kAeA0pwoaQ"
    
    test_transcriber_with_timestamps(test_url)