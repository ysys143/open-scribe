"""
Subtitle correction module using hybrid approach
Combines YouTube transcript timecodes with GPT-4o transcription quality
"""

import re
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from difflib import SequenceMatcher

from ..config import Config


class SubtitleCorrector:
    """Hybrid subtitle correction using YouTube timecodes + GPT transcription"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.correct_model = config.OPENAI_CORRECT_MODEL
    
    def correct_with_youtube_timestamps(
        self, 
        youtube_transcript: str, 
        gpt_transcription: str,
        verbose: bool = False
    ) -> str:
        """
        Correct GPT transcription using YouTube transcript timestamps
        
        Args:
            youtube_transcript: Transcript from YouTube API with timestamps
            gpt_transcription: High-quality transcription from GPT-4o
            verbose: Show detailed processing info
            
        Returns:
            Corrected transcript with accurate timestamps and high-quality text
        """
        if not self.client:
            print("[Subtitle Corrector] Error: OpenAI API key not configured")
            return youtube_transcript
        
        # Parse YouTube transcript to extract timestamps and text
        youtube_segments = self._parse_timestamped_text(youtube_transcript)
        
        if not youtube_segments:
            print("[Subtitle Corrector] Warning: No timestamps found in YouTube transcript")
            return gpt_transcription
        
        if verbose:
            print(f"[Subtitle Corrector] Found {len(youtube_segments)} segments from YouTube")
            print(f"[Subtitle Corrector] Using {self.correct_model} for correction")
        
        # Create correction prompt
        system_prompt = """You are a subtitle correction specialist. Your task is to:
1. Align high-quality transcription text with YouTube subtitle timestamps
2. Preserve the exact timestamps from YouTube
3. Use the superior text quality from GPT transcription
4. Ensure proper sentence boundaries align with timestamps
5. Maintain natural speech flow and readability

Important rules:
- Keep ALL timestamps from YouTube transcript
- Replace YouTube text with GPT text where they match
- Handle cases where GPT has better punctuation/capitalization
- Preserve speaker changes and natural pauses
"""
        
        user_prompt = f"""Please align these two transcripts:

YOUTUBE TRANSCRIPT (with timestamps):
{youtube_transcript}

HIGH-QUALITY TRANSCRIPTION (GPT-4o):
{gpt_transcription}

Output the corrected subtitle with:
- Exact timestamps from YouTube
- Text quality from GPT transcription
- Format: [HH:MM:SS] or [MM:SS] followed by text

Return ONLY the corrected subtitle text, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.correct_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=4000
            )
            
            corrected_text = response.choices[0].message.content.strip()
            
            if verbose:
                print(f"[Subtitle Corrector] Correction completed")
                self._show_comparison(youtube_transcript, corrected_text)
            
            return corrected_text
            
        except Exception as e:
            print(f"[Subtitle Corrector] Error during correction: {e}")
            print("[Subtitle Corrector] Falling back to YouTube transcript")
            return youtube_transcript
    
    def align_timestamps_with_text(
        self,
        timestamps: List[Tuple[float, float]],  # List of (start, end) times
        text: str,
        words_per_segment: int = 10
    ) -> str:
        """
        Align timestamps with plain text (for GPT-4o timestamp generation)
        
        Args:
            timestamps: List of (start, end) timestamp pairs in seconds
            text: Plain text to align
            words_per_segment: Approximate words per timestamp segment
            
        Returns:
            Text with timestamps inserted
        """
        words = text.split()
        total_words = len(words)
        total_timestamps = len(timestamps)
        
        if total_timestamps == 0:
            return text
        
        # Calculate words per timestamp
        words_per_timestamp = max(1, total_words // total_timestamps)
        
        result = []
        word_index = 0
        
        for i, (start_time, _) in enumerate(timestamps):
            # Format timestamp
            timestamp = self._format_seconds_to_timestamp(start_time)
            
            # Calculate how many words for this segment
            if i == total_timestamps - 1:
                # Last segment gets all remaining words
                segment_words = words[word_index:]
            else:
                end_index = min(word_index + words_per_timestamp, total_words)
                segment_words = words[word_index:end_index]
                word_index = end_index
            
            if segment_words:
                segment_text = ' '.join(segment_words)
                result.append(f"[{timestamp}] {segment_text}")
        
        return '\n'.join(result)
    
    def _parse_timestamped_text(self, text: str) -> List[Dict[str, any]]:
        """
        Parse timestamped text into segments
        
        Args:
            text: Text with timestamps in format [HH:MM:SS] or [MM:SS]
            
        Returns:
            List of dicts with 'timestamp', 'time_seconds', and 'text'
        """
        segments = []
        
        # Pattern for timestamps [HH:MM:SS] or [MM:SS]
        pattern = r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?)(?=\[|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for timestamp_str, segment_text in matches:
            segments.append({
                'timestamp': timestamp_str,
                'time_seconds': self._timestamp_to_seconds(timestamp_str),
                'text': segment_text.strip()
            })
        
        return segments
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds"""
        parts = timestamp.split(':')
        if len(parts) == 3:
            # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0
    
    def _format_seconds_to_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS or MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _show_comparison(self, original: str, corrected: str):
        """Show comparison between original and corrected for debugging"""
        print("\n" + "="*60)
        print("COMPARISON (first 500 chars)")
        print("-"*60)
        print("Original YouTube:")
        print(original[:500])
        print("-"*60)
        print("Corrected:")
        print(corrected[:500])
        print("="*60 + "\n")


class HybridTranscriber:
    """
    Hybrid transcriber that combines YouTube timestamps with GPT-4o quality
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.corrector = SubtitleCorrector(config)
    
    def transcribe_hybrid(
        self,
        url: str,
        gpt_engine: str = "gpt-4o-mini-transcribe",
        verbose: bool = False
    ) -> Optional[str]:
        """
        Perform hybrid transcription
        
        Args:
            url: YouTube URL
            gpt_engine: GPT engine to use for high-quality transcription
            verbose: Show detailed progress
            
        Returns:
            Hybrid transcription with timestamps
        """
        from ..transcribers.youtube import YouTubeTranscriptAPITranscriber
        from ..transcribers.openai import GPT4OTranscriber, GPT4OMiniTranscriber
        
        # Step 1: Get YouTube transcript with timestamps
        if verbose:
            print("[Hybrid] Step 1: Fetching YouTube transcript with timestamps...")
        
        youtube_transcriber = YouTubeTranscriptAPITranscriber(self.config)
        youtube_transcript = youtube_transcriber.transcribe(
            url, 
            return_timestamps=True
        )
        
        if not youtube_transcript:
            print("[Hybrid] Error: Could not fetch YouTube transcript")
            return None
        
        # Step 2: Get high-quality transcription from GPT
        if verbose:
            print(f"[Hybrid] Step 2: Getting high-quality transcription from {gpt_engine}...")
        
        # Select GPT transcriber
        if gpt_engine == "gpt-4o-transcribe":
            gpt_transcriber = GPT4OTranscriber(self.config)
        else:
            gpt_transcriber = GPT4OMiniTranscriber(self.config)
        
        # For hybrid mode, we don't use GPT timestamps since YouTube has better ones
        gpt_transcription = gpt_transcriber.transcribe(
            url,
            return_timestamps=False  # Don't use GPT timestamps
        )
        
        if not gpt_transcription:
            print("[Hybrid] Warning: GPT transcription failed, using YouTube transcript only")
            return youtube_transcript
        
        # Step 3: Combine using correction model
        if verbose:
            print(f"[Hybrid] Step 3: Correcting with {self.config.OPENAI_CORRECT_MODEL}...")
        
        corrected_transcript = self.corrector.correct_with_youtube_timestamps(
            youtube_transcript,
            gpt_transcription,
            verbose=verbose
        )
        
        return corrected_transcript