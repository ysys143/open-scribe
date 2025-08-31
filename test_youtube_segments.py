#!/usr/bin/env python
"""
Test script to analyze YouTube transcript segments and merge them by sentences
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re

def analyze_segments(video_id):
    """Analyze segment structure from YouTube transcript"""
    print(f"Analyzing video: {video_id}")
    print("=" * 60)
    
    # Get transcript
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    
    # Show first 10 segments
    print("\n1. First 10 segments (raw):")
    print("-" * 40)
    for i, entry in enumerate(transcript_data[:10]):
        print(f"[{i:2d}] {entry['start']:6.2f}s: {entry['text']}")
    
    # Analyze patterns
    print("\n2. Segment Statistics:")
    print("-" * 40)
    total_segments = len(transcript_data)
    segments_with_period = sum(1 for e in transcript_data if '.' in e['text'])
    segments_with_question = sum(1 for e in transcript_data if '?' in e['text'])
    segments_with_exclamation = sum(1 for e in transcript_data if '!' in e['text'])
    
    print(f"Total segments: {total_segments}")
    print(f"Segments with period (.): {segments_with_period}")
    print(f"Segments with question (?): {segments_with_question}")
    print(f"Segments with exclamation (!): {segments_with_exclamation}")
    
    # Calculate average duration
    durations = [e.get('duration', 0) for e in transcript_data]
    avg_duration = sum(durations) / len(durations) if durations else 0
    print(f"Average segment duration: {avg_duration:.2f} seconds")
    
    return transcript_data


def merge_segments_by_sentence(transcript_data):
    """Merge segments into complete sentences based on punctuation"""
    print("\n3. Merging segments by sentences:")
    print("-" * 40)
    
    merged_sentences = []
    current_sentence = {
        'text': '',
        'start': None,
        'end': None,
        'segments': []
    }
    
    for entry in transcript_data:
        text = entry['text'].strip()
        if not text:
            continue
        
        # If this is the first segment of a sentence
        if current_sentence['start'] is None:
            current_sentence['start'] = entry['start']
        
        # Add to current sentence
        if current_sentence['text']:
            current_sentence['text'] += ' ' + text
        else:
            current_sentence['text'] = text
        
        current_sentence['end'] = entry['start'] + entry.get('duration', 0)
        current_sentence['segments'].append(entry)
        
        # Check if sentence ends with punctuation
        if text.endswith(('.', '!', '?', '。', '！', '？')):
            # Save the completed sentence
            merged_sentences.append({
                'text': current_sentence['text'],
                'start': current_sentence['start'],
                'end': current_sentence['end'],
                'segment_count': len(current_sentence['segments'])
            })
            
            # Reset for next sentence
            current_sentence = {
                'text': '',
                'start': None,
                'end': None,
                'segments': []
            }
    
    # Don't forget the last sentence if it doesn't end with punctuation
    if current_sentence['text']:
        merged_sentences.append({
            'text': current_sentence['text'],
            'start': current_sentence['start'],
            'end': current_sentence['end'],
            'segment_count': len(current_sentence['segments'])
        })
    
    return merged_sentences


def merge_segments_smart(transcript_data, max_duration=10.0, max_length=200):
    """
    Smart merge: combine segments until hitting punctuation OR limits
    
    Args:
        transcript_data: Raw transcript segments
        max_duration: Maximum duration for merged segment (seconds)
        max_length: Maximum character length for merged segment
    """
    print("\n4. Smart merging with limits:")
    print("-" * 40)
    print(f"Max duration: {max_duration}s, Max length: {max_length} chars")
    
    merged_segments = []
    current_segment = {
        'text': '',
        'start': None,
        'duration': 0,
        'parts': 0
    }
    
    for entry in transcript_data:
        text = entry['text'].strip()
        if not text:
            continue
        
        # Calculate if adding this would exceed limits
        new_duration = current_segment['duration'] + entry.get('duration', 0)
        new_length = len(current_segment['text']) + len(text) + 1  # +1 for space
        
        # Check if we should start a new segment
        should_split = False
        if current_segment['text']:  # If we have existing content
            # Split if: sentence ends, OR exceeds duration, OR exceeds length
            if (text.endswith(('.', '!', '?', '。', '！', '？')) or 
                new_duration > max_duration or 
                new_length > max_length):
                should_split = True
        
        if should_split and current_segment['text']:
            # Save current segment
            merged_segments.append(dict(current_segment))
            # Start new segment
            current_segment = {
                'text': text,
                'start': entry['start'],
                'duration': entry.get('duration', 0),
                'parts': 1
            }
        else:
            # Add to current segment
            if current_segment['start'] is None:
                current_segment['start'] = entry['start']
            
            if current_segment['text']:
                current_segment['text'] += ' ' + text
            else:
                current_segment['text'] = text
            
            current_segment['duration'] = new_duration
            current_segment['parts'] += 1
    
    # Don't forget the last segment
    if current_segment['text']:
        merged_segments.append(current_segment)
    
    return merged_segments


def format_timestamp(seconds):
    """Format seconds to MM:SS or HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def test_merge_methods(video_id='3kAeA0pwoaQ'):
    """Test different merging methods"""
    
    # Get transcript
    transcript_data = analyze_segments(video_id)
    
    # Method 1: Merge by sentence endings
    sentence_merged = merge_segments_by_sentence(transcript_data)
    print(f"\nMerged into {len(sentence_merged)} sentences")
    print("First 5 merged sentences:")
    for i, sent in enumerate(sentence_merged[:5]):
        timestamp = format_timestamp(sent['start'])
        print(f"[{timestamp}] ({sent['segment_count']} segments) {sent['text'][:100]}...")
    
    # Method 2: Smart merge with limits
    smart_merged = merge_segments_smart(transcript_data)
    print(f"\nSmart merged into {len(smart_merged)} segments")
    print("First 5 smart-merged segments:")
    for i, seg in enumerate(smart_merged[:5]):
        timestamp = format_timestamp(seg['start'])
        print(f"[{timestamp}] ({seg['parts']} parts, {seg['duration']:.1f}s) {seg['text'][:100]}...")
    
    # Compare with original
    print("\n5. Comparison:")
    print("-" * 40)
    print(f"Original segments: {len(transcript_data)}")
    print(f"Sentence-merged: {len(sentence_merged)}")
    print(f"Smart-merged: {len(smart_merged)}")
    
    # Calculate average lengths
    if sentence_merged:
        avg_sentence_segments = sum(s['segment_count'] for s in sentence_merged) / len(sentence_merged)
        print(f"Average segments per sentence: {avg_sentence_segments:.1f}")
    
    if smart_merged:
        avg_smart_parts = sum(s['parts'] for s in smart_merged) / len(smart_merged)
        avg_smart_duration = sum(s['duration'] for s in smart_merged) / len(smart_merged)
        print(f"Average parts per smart segment: {avg_smart_parts:.1f}")
        print(f"Average duration per smart segment: {avg_smart_duration:.1f}s")


if __name__ == "__main__":
    # Test with the video you mentioned
    test_merge_methods('3kAeA0pwoaQ')
    
    print("\n" + "=" * 60)
    print("Test another video? Uncomment below:")
    # test_merge_methods('YOUR_VIDEO_ID_HERE')