"""
SRT subtitle format converter
Converts timestamped transcripts to SRT/VTT format
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


class SRTConverter:
    """Convert timestamped transcripts to SRT format"""
    
    @staticmethod
    def timestamp_to_srt(timestamp_text: str, max_chars_per_line: int = 42) -> str:
        """
        Convert timestamp format [MM:SS] or [HH:MM:SS] to SRT format
        
        Args:
            timestamp_text: Text with timestamps in [HH:MM:SS] or [MM:SS] format
            max_chars_per_line: Maximum characters per subtitle line (Netflix standard: 42)
            
        Returns:
            SRT formatted string
        """
        # Parse timestamped segments
        segments = SRTConverter._parse_timestamped_text(timestamp_text)
        
        if not segments:
            return ""
        
        # Convert to SRT entries
        srt_entries = []
        
        for i, segment in enumerate(segments):
            # Calculate end time (next segment start or current + duration estimate)
            if i < len(segments) - 1:
                end_time = segments[i + 1]['start_seconds']
            else:
                # Estimate duration based on text length (roughly 3 seconds per 50 chars)
                text_length = len(segment['text'])
                estimated_duration = max(2.0, min(10.0, text_length / 15))  # 2-10 seconds
                end_time = segment['start_seconds'] + estimated_duration
            
            # Format subtitle lines (break long text)
            subtitle_lines = SRTConverter._format_subtitle_lines(
                segment['text'], 
                max_chars_per_line
            )
            
            # Create SRT entry
            entry = SRTConverter._create_srt_entry(
                index=i + 1,
                start_seconds=segment['start_seconds'],
                end_seconds=end_time,
                text=subtitle_lines
            )
            
            srt_entries.append(entry)
        
        return '\n\n'.join(srt_entries)
    
    @staticmethod
    def timestamp_to_vtt(timestamp_text: str, max_chars_per_line: int = 42) -> str:
        """
        Convert timestamp format to WebVTT format
        
        Args:
            timestamp_text: Text with timestamps
            max_chars_per_line: Maximum characters per subtitle line
            
        Returns:
            WebVTT formatted string
        """
        # First convert to SRT format
        srt_content = SRTConverter.timestamp_to_srt(timestamp_text, max_chars_per_line)
        
        if not srt_content:
            return "WEBVTT\n\n"
        
        # Convert SRT to VTT
        vtt_content = "WEBVTT\n\n"
        
        # Replace SRT timecode format with VTT format
        # SRT: 00:00:00,000 --> 00:00:05,000
        # VTT: 00:00:00.000 --> 00:00:05.000
        for entry in srt_content.split('\n\n'):
            lines = entry.split('\n')
            if len(lines) >= 3:
                # Skip index line (VTT doesn't use it)
                timecode = lines[1].replace(',', '.')
                text = '\n'.join(lines[2:])
                vtt_content += f"{timecode}\n{text}\n\n"
        
        return vtt_content.strip()
    
    @staticmethod
    def _parse_timestamped_text(text: str) -> List[dict]:
        """
        Parse text with timestamps into segments
        
        Args:
            text: Text with [HH:MM:SS] or [MM:SS] timestamps
            
        Returns:
            List of segments with start time and text
        """
        segments = []
        
        # Pattern for [HH:MM:SS] or [MM:SS] followed by text
        pattern = r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^\[]+)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for timestamp_str, segment_text in matches:
            # Convert timestamp to seconds
            seconds = SRTConverter._timestamp_str_to_seconds(timestamp_str)
            
            # Clean up text
            clean_text = segment_text.strip()
            
            if clean_text:
                segments.append({
                    'timestamp': timestamp_str,
                    'start_seconds': seconds,
                    'text': clean_text
                })
        
        return segments
    
    @staticmethod
    def _timestamp_str_to_seconds(timestamp: str) -> float:
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
    
    @staticmethod
    def _seconds_to_srt_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_subtitle_lines(text: str, max_chars: int) -> str:
        """
        Format text for subtitle display
        
        Args:
            text: Text to format
            max_chars: Maximum characters per line
            
        Returns:
            Formatted text with line breaks
        """
        # Remove existing line breaks and extra spaces
        text = ' '.join(text.split())
        
        if len(text) <= max_chars:
            return text
        
        # Split into multiple lines
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # Check if adding this word exceeds the limit
            if current_length + word_length + len(current_line) > max_chars:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is too long, force split
                    lines.append(word[:max_chars])
                    current_line = [word[max_chars:]]
                    current_length = len(word[max_chars:])
            else:
                current_line.append(word)
                current_length += word_length
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 2 lines for readability
        if len(lines) > 2:
            # Redistribute words across 2 lines
            all_text = ' '.join(lines)
            mid_point = len(all_text) // 2
            
            # Find the best split point near the middle
            best_split = mid_point
            for i in range(max(0, mid_point - 10), min(len(all_text), mid_point + 10)):
                if i < len(all_text) and all_text[i] == ' ':
                    best_split = i
                    break
            
            lines = [
                all_text[:best_split].strip(),
                all_text[best_split:].strip()
            ]
        
        return '\n'.join(lines)
    
    @staticmethod
    def _create_srt_entry(index: int, start_seconds: float, end_seconds: float, text: str) -> str:
        """
        Create a single SRT entry
        
        Args:
            index: Subtitle index (1-based)
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            text: Subtitle text
            
        Returns:
            SRT formatted entry
        """
        start_time = SRTConverter._seconds_to_srt_timestamp(start_seconds)
        end_time = SRTConverter._seconds_to_srt_timestamp(end_seconds)
        
        return f"{index}\n{start_time} --> {end_time}\n{text}"
    
    @staticmethod
    def save_srt_file(timestamp_text: str, output_path: Path, format: str = 'srt') -> Path:
        """
        Save timestamped text as SRT or VTT file
        
        Args:
            timestamp_text: Text with timestamps
            output_path: Output file path (without extension)
            format: 'srt' or 'vtt'
            
        Returns:
            Path to saved file
        """
        # Convert based on format
        if format == 'vtt':
            content = SRTConverter.timestamp_to_vtt(timestamp_text)
            extension = '.vtt'
        else:
            content = SRTConverter.timestamp_to_srt(timestamp_text)
            extension = '.srt'
        
        # Create output path with correct extension
        output_file = output_path.with_suffix(extension)
        
        # Save file
        output_file.write_text(content, encoding='utf-8')
        
        return output_file


def convert_transcript_to_srt(input_file: Path, output_file: Optional[Path] = None) -> Path:
    """
    Convenience function to convert a transcript file to SRT
    
    Args:
        input_file: Path to transcript file with timestamps
        output_file: Optional output path (defaults to same name with .srt extension)
        
    Returns:
        Path to created SRT file
    """
    # Read input file
    transcript_text = input_file.read_text(encoding='utf-8')
    
    # Check if text has timestamps
    if not re.search(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', transcript_text):
        raise ValueError("Input file does not contain timestamps in [MM:SS] or [HH:MM:SS] format")
    
    # Determine output path
    if output_file is None:
        output_file = input_file.with_suffix('.srt')
    
    # Convert and save
    converter = SRTConverter()
    srt_content = converter.timestamp_to_srt(transcript_text)
    
    output_file.write_text(srt_content, encoding='utf-8')
    
    return output_file