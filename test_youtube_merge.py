#!/usr/bin/env python
"""
Test improved segment merging for YouTube transcripts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transcribers.youtube import YouTubeTranscriptAPITranscriber
from src.config import Config


def merge_segments_smart(transcript_data, min_duration=2.0, max_chars=150):
    """
    Smart merge segments from YouTube Transcript API
    
    Args:
        transcript_data: List of segment dicts from transcript.fetch()
        min_duration: Minimum duration for a merged segment (seconds)
        max_chars: Maximum character length for merged segment
    
    Returns:
        List of merged segments with text, start, duration
    """
    merged = []
    current = {
        'text': '',
        'start': None,
        'duration': 0,
        'parts': 0
    }
    
    for seg in transcript_data:
        text = seg['text'].strip()
        if not text:
            continue
        
        # Initialize start time
        if current['start'] is None:
            current['start'] = seg['start']
        
        # Calculate new duration and length
        new_duration = (seg['start'] + seg.get('duration', 0)) - current['start']
        new_text_length = len(current['text']) + len(text) + (1 if current['text'] else 0)
        
        # Decide whether to split
        should_split = False
        
        if current['text']:  # If we have existing content
            # Split if:
            # 1. Current segment ends with sentence ending AND has minimum duration
            if current['text'].endswith(('.', '!', '?', '。', '！', '？')) and current['duration'] >= min_duration:
                should_split = True
            # 2. OR adding this would exceed max length
            elif new_text_length > max_chars:
                should_split = True
            # 3. OR duration is getting too long (>15 seconds)
            elif new_duration > 15:
                should_split = True
        
        if should_split and current['text']:
            # Save current segment
            merged.append({
                'text': current['text'],
                'start': current['start'],
                'duration': current['duration'],
                'parts': current['parts']
            })
            # Start new segment
            current = {
                'text': text,
                'start': seg['start'],
                'duration': seg.get('duration', 0),
                'parts': 1
            }
        else:
            # Add to current segment
            if current['text']:
                current['text'] += ' ' + text
            else:
                current['text'] = text
            current['duration'] = new_duration
            current['parts'] += 1
    
    # Don't forget the last segment
    if current['text']:
        merged.append({
            'text': current['text'],
            'start': current['start'],
            'duration': current['duration'],
            'parts': current['parts']
        })
    
    return merged


def format_timestamp(seconds):
    """Format seconds to MM:SS or HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def test_merge_in_transcriber(url):
    """Test merging logic that will be integrated into transcriber"""
    print("=" * 60)
    print("Testing Improved YouTube Transcript Merging")
    print("=" * 60)
    
    from youtube_transcript_api import YouTubeTranscriptApi
    from src.utils.validators import extract_video_id
    
    video_id = extract_video_id(url)
    print(f"Video ID: {video_id}\n")
    
    # Get transcript using API directly
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    
    # Find best transcript
    transcript = None
    for t in transcript_list:
        transcript = t
        print(f"Using transcript: {t.language} ({t.language_code}), Auto-generated: {t.is_generated}")
        break
    
    if not transcript:
        print("No transcript found")
        return
    
    # Fetch raw segments
    raw_segments = transcript.fetch()
    
    print(f"\n1. Original segments: {len(raw_segments)}")
    print("First 5 segments:")
    for i, seg in enumerate(raw_segments[:5]):
        # Convert to dict if it's an object
        if hasattr(seg, '__dict__'):
            seg_dict = {'text': seg.text, 'start': seg.start, 'duration': seg.duration}
        else:
            seg_dict = seg
        print(f"  [{format_timestamp(seg_dict['start'])}] {seg_dict['text']}")
    
    # Test merging
    print("\n2. Testing smart merge:")
    merged_segments = merge_segments_smart(raw_segments, min_duration=2.0, max_chars=150)
    
    print(f"Merged to: {len(merged_segments)} segments")
    print(f"Reduction: {len(raw_segments)/len(merged_segments):.1f}x")
    
    print("\nFirst 5 merged segments:")
    for i, seg in enumerate(merged_segments[:5]):
        print(f"  [{format_timestamp(seg['start'])}] ({seg['parts']} parts, {seg['duration']:.1f}s)")
        print(f"    {seg['text']}")
    
    # Test formatting for return_timestamps=True
    print("\n3. Simulating return_timestamps=True output:")
    print("-" * 40)
    
    # Format as timestamp lines
    lines = []
    for seg in merged_segments[:10]:
        timestamp = format_timestamp(seg['start'])
        lines.append(f"[{timestamp}] {seg['text']}")
    
    for line in lines:
        if len(line) > 120:
            print(line[:117] + "...")
        else:
            print(line)
    
    # Statistics
    print("\n4. Statistics:")
    print("-" * 40)
    
    orig_durations = [s.get('duration', 0) for s in raw_segments]
    merged_durations = [s['duration'] for s in merged_segments]
    
    print(f"Original:")
    print(f"  Count: {len(raw_segments)}")
    print(f"  Avg duration: {sum(orig_durations)/len(orig_durations):.1f}s")
    print(f"  Avg text length: {sum(len(s['text']) for s in raw_segments)/len(raw_segments):.1f} chars")
    
    print(f"\nMerged:")
    print(f"  Count: {len(merged_segments)}")
    print(f"  Avg duration: {sum(merged_durations)/len(merged_durations):.1f}s")
    print(f"  Avg text length: {sum(len(s['text']) for s in merged_segments)/len(merged_segments):.1f} chars")
    print(f"  Avg parts per segment: {sum(s['parts'] for s in merged_segments)/len(merged_segments):.1f}")


if __name__ == "__main__":
    test_url = "https://youtu.be/3kAeA0pwoaQ"
    test_merge_in_transcriber(test_url)