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
                # Include timestamps
                lines = []
                for entry in transcript_data:
                    timestamp = self._format_timestamp(entry.start)
                    text = entry.text.replace('\n', ' ')
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
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS or MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"