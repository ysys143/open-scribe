"""
YouTube Transcript API transcriber
"""

import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from .base import BaseTranscriber
from ..utils.validators import extract_video_id


class YouTubeTranscriptAPITranscriber(BaseTranscriber):
    """Transcriber using YouTube's official transcript API"""
    
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def name(self) -> str:
        """Get the name of this transcriber"""
        return "YouTube Transcript API"
    
    @property
    def requires_api_key(self) -> bool:
        """YouTube Transcript API doesn't require an API key"""
        return False
        
    def is_available(self) -> bool:
        """Check if YouTube Transcript API is available"""
        try:
            import youtube_transcript_api
            return True
        except ImportError:
            return False
    
    def transcribe(self, audio_path: str, stream: bool = False, 
                  return_timestamps: bool = False, **kwargs) -> Optional[str]:
        """
        Get transcript using YouTube Transcript API
        
        Args:
            audio_path: YouTube URL or video ID
            stream: Streaming mode (not applicable for this transcriber)
            return_timestamps: Whether to include timestamps
            **kwargs: Additional parameters (ignored)
            
        Returns:
            str: Transcription text or None if failed
        """
        # Extract video ID from the URL/path
        video_id = extract_video_id(audio_path)
        if not video_id:
            # Try to extract from the filename if it's a path
            import os
            filename = os.path.basename(audio_path)
            # Remove extension and try to extract ID
            video_id_match = re.search(r'([a-zA-Z0-9_-]{11})', filename)
            if video_id_match:
                video_id = video_id_match.group(1)
            else:
                print("Error: Could not extract video ID from input")
                return None
        
        try:
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Get available transcripts
            transcript_list = api.list(video_id)
            
            # Try to get manual transcript first, then auto-generated
            transcript = None
            try:
                # Try manual transcripts in preferred languages
                for lang in ['en', 'ko', 'ja', 'zh']:
                    try:
                        transcript = transcript_list.find_manually_created_transcript([lang])
                        print(f"Found manual transcript in {lang}")
                        break
                    except:
                        continue
                
                # If no manual transcript, try any manual transcript
                if not transcript:
                    for t in transcript_list:
                        if not t.is_generated:
                            transcript = t
                            print(f"Found manual transcript in {t.language_code}")
                            break
            except:
                pass
            
            # Fall back to auto-generated if no manual found
            if not transcript:
                try:
                    # Try auto-generated in preferred languages
                    for lang in ['en', 'ko', 'ja', 'zh']:
                        try:
                            transcript = transcript_list.find_generated_transcript([lang])
                            print(f"Found auto-generated transcript in {lang}")
                            break
                        except:
                            continue
                    
                    # If still no transcript, get first available
                    if not transcript:
                        for t in transcript_list:
                            transcript = t
                            print(f"Found {'auto-generated' if t.is_generated else 'manual'} transcript in {t.language_code}")
                            break
                except:
                    pass
            
            if not transcript:
                print("Error: No transcripts available for this video")
                return None
            
            # Fetch the transcript
            transcript_data = transcript.fetch()
            
            # Format the output
            if return_timestamps:
                # Merge segments for better readability
                merged_segments = self._merge_segments_smart(transcript_data)
                
                # Format with timestamps
                lines = []
                for seg in merged_segments:
                    timestamp = self._format_timestamp(seg['start'])
                    text = seg['text'].replace('\n', ' ')
                    lines.append(f"[{timestamp}] {text}")
                return '\n'.join(lines)
            else:
                # Just concatenate text with proper spacing
                texts = []
                for entry in transcript_data:
                    text = entry.text.replace('\n', ' ').strip()
                    if text:
                        texts.append(text)
                # Join with spaces, then clean up multiple spaces
                result = ' '.join(texts)
                result = re.sub(r'\s+', ' ', result)
                # Add basic sentence breaks
                result = re.sub(r'([.!?])\s*', r'\1\n', result)
                return result.strip()
                
        except TranscriptsDisabled:
            print("Error: Transcripts are disabled for this video")
            return None
        except NoTranscriptFound:
            print("Error: No transcript found for this video")
            return None
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None
    
    def _merge_segments_smart(self, transcript_data, min_duration=2.0, max_chars=150):
        """
        Smart merge segments from YouTube Transcript API
        
        Args:
            transcript_data: List of segment objects from transcript.fetch()
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
            # Handle segment object attributes
            text = seg.text.strip() if hasattr(seg, 'text') else seg['text'].strip()
            start = seg.start if hasattr(seg, 'start') else seg['start']
            duration = seg.duration if hasattr(seg, 'duration') else seg.get('duration', 0)
            
            if not text:
                continue
            
            # Initialize start time
            if current['start'] is None:
                current['start'] = start
            
            # Calculate new duration and length
            new_duration = (start + duration) - current['start']
            new_text_length = len(current['text']) + len(text) + (1 if current['text'] else 0)
            
            # Decide whether to split
            should_split = False
            
            if current['text']:  # If we have existing content
                # Split if sentence ends AND has minimum duration
                if current['text'].endswith(('.', '!', '?', '。', '！', '？')) and current['duration'] >= min_duration:
                    should_split = True
                # Or if adding this would exceed max length
                elif new_text_length > max_chars:
                    should_split = True
                # Or if duration is getting too long (>15 seconds)
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
                    'start': start,
                    'duration': duration,
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
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS or MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"