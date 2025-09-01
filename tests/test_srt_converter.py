"""
Unit tests for SRT converter module
"""

import unittest
from pathlib import Path
import tempfile
import os

from src.utils.srt_converter import SRTConverter, convert_transcript_to_srt


class TestSRTConverter(unittest.TestCase):
    """Test cases for SRT converter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = SRTConverter()
        
        # Sample timestamped text
        self.sample_timestamp_text = """[00:00] Hello, this is the first segment.
[00:05] This is the second segment with more text.
[00:12] And here's the third segment.
[01:30] This is after a longer pause."""
        
        self.sample_timestamp_text_hms = """[00:00:00] Opening segment.
[00:00:15] Middle segment with details.
[00:01:45] Final segment of the video.
[01:30:00] This is after an hour and half."""
    
    def test_parse_timestamped_text(self):
        """Test parsing of timestamped text"""
        segments = self.converter._parse_timestamped_text(self.sample_timestamp_text)
        
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0]['text'], "Hello, this is the first segment.")
        self.assertEqual(segments[0]['start_seconds'], 0)
        self.assertEqual(segments[1]['start_seconds'], 5)
        self.assertEqual(segments[3]['start_seconds'], 90)
    
    def test_parse_hms_timestamps(self):
        """Test parsing of HH:MM:SS format timestamps"""
        segments = self.converter._parse_timestamped_text(self.sample_timestamp_text_hms)
        
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0]['start_seconds'], 0)
        self.assertEqual(segments[1]['start_seconds'], 15)
        self.assertEqual(segments[2]['start_seconds'], 105)
        self.assertEqual(segments[3]['start_seconds'], 5400)  # 1:30:00
    
    def test_timestamp_str_to_seconds(self):
        """Test timestamp string to seconds conversion"""
        # MM:SS format
        self.assertEqual(self.converter._timestamp_str_to_seconds("00:00"), 0)
        self.assertEqual(self.converter._timestamp_str_to_seconds("01:30"), 90)
        self.assertEqual(self.converter._timestamp_str_to_seconds("10:05"), 605)
        
        # HH:MM:SS format
        self.assertEqual(self.converter._timestamp_str_to_seconds("00:00:00"), 0)
        self.assertEqual(self.converter._timestamp_str_to_seconds("01:30:00"), 5400)
        self.assertEqual(self.converter._timestamp_str_to_seconds("02:15:30"), 8130)
    
    def test_seconds_to_srt_timestamp(self):
        """Test seconds to SRT timestamp format conversion"""
        self.assertEqual(self.converter._seconds_to_srt_timestamp(0), "00:00:00,000")
        self.assertEqual(self.converter._seconds_to_srt_timestamp(90), "00:01:30,000")
        self.assertEqual(self.converter._seconds_to_srt_timestamp(3661.5), "01:01:01,500")
        self.assertEqual(self.converter._seconds_to_srt_timestamp(5.123), "00:00:05,123")
    
    def test_format_subtitle_lines(self):
        """Test subtitle line formatting"""
        # Short text (no break needed)
        short_text = "This is a short line"
        formatted = self.converter._format_subtitle_lines(short_text, 42)
        self.assertEqual(formatted, short_text)
        
        # Long text (needs line break)
        long_text = "This is a very long subtitle text that definitely needs to be broken into multiple lines for better readability"
        formatted = self.converter._format_subtitle_lines(long_text, 42)
        lines = formatted.split('\n')
        self.assertLessEqual(len(lines), 2)  # Should be max 2 lines
        for line in lines:
            self.assertLessEqual(len(line), 50)  # Some flexibility for word boundaries
    
    def test_create_srt_entry(self):
        """Test SRT entry creation"""
        entry = self.converter._create_srt_entry(
            index=1,
            start_seconds=5.0,
            end_seconds=10.0,
            text="Test subtitle"
        )
        
        expected = "1\n00:00:05,000 --> 00:00:10,000\nTest subtitle"
        self.assertEqual(entry, expected)
    
    def test_timestamp_to_srt_conversion(self):
        """Test full timestamp to SRT conversion"""
        srt_content = self.converter.timestamp_to_srt(self.sample_timestamp_text)
        
        # Check SRT format
        self.assertIn("1\n00:00:00,000 --> 00:00:05,000", srt_content)
        self.assertIn("Hello, this is the first segment.", srt_content)
        
        # Check multiple entries
        entries = srt_content.split('\n\n')
        self.assertEqual(len(entries), 4)
        
        # Check entry format
        for entry in entries:
            lines = entry.split('\n')
            self.assertGreaterEqual(len(lines), 3)  # Index, timecode, text
            self.assertRegex(lines[1], r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    
    def test_timestamp_to_vtt_conversion(self):
        """Test timestamp to WebVTT conversion"""
        vtt_content = self.converter.timestamp_to_vtt(self.sample_timestamp_text)
        
        # Check VTT header
        self.assertTrue(vtt_content.startswith("WEBVTT"))
        
        # Check VTT format (uses . instead of ,)
        self.assertIn("00:00:00.000 --> 00:00:05.000", vtt_content)
        self.assertNotIn(",", vtt_content)  # VTT uses dots, not commas
        
        # Check no index numbers (VTT doesn't use them)
        self.assertNotRegex(vtt_content, r'^\d+$', re.MULTILINE)
    
    def test_empty_input(self):
        """Test handling of empty input"""
        srt_content = self.converter.timestamp_to_srt("")
        self.assertEqual(srt_content, "")
        
        vtt_content = self.converter.timestamp_to_vtt("")
        self.assertEqual(vtt_content, "WEBVTT\n\n")
    
    def test_save_srt_file(self):
        """Test saving SRT file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test"
            
            # Save as SRT
            srt_file = self.converter.save_srt_file(
                self.sample_timestamp_text,
                output_path,
                format='srt'
            )
            
            self.assertTrue(srt_file.exists())
            self.assertEqual(srt_file.suffix, '.srt')
            
            content = srt_file.read_text(encoding='utf-8')
            self.assertIn("00:00:00,000 --> 00:00:05,000", content)
    
    def test_save_vtt_file(self):
        """Test saving VTT file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test"
            
            # Save as VTT
            vtt_file = self.converter.save_srt_file(
                self.sample_timestamp_text,
                output_path,
                format='vtt'
            )
            
            self.assertTrue(vtt_file.exists())
            self.assertEqual(vtt_file.suffix, '.vtt')
            
            content = vtt_file.read_text(encoding='utf-8')
            self.assertTrue(content.startswith("WEBVTT"))
    
    def test_convert_transcript_to_srt_function(self):
        """Test the convenience function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input file
            input_file = Path(tmpdir) / "transcript.txt"
            input_file.write_text(self.sample_timestamp_text, encoding='utf-8')
            
            # Convert
            output_file = convert_transcript_to_srt(input_file)
            
            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.suffix, '.srt')
            
            # Check content
            content = output_file.read_text(encoding='utf-8')
            self.assertIn("00:00:00,000 --> 00:00:05,000", content)
    
    def test_no_timestamps_error(self):
        """Test error handling for text without timestamps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "no_timestamps.txt"
            input_file.write_text("This text has no timestamps", encoding='utf-8')
            
            with self.assertRaises(ValueError) as context:
                convert_transcript_to_srt(input_file)
            
            self.assertIn("does not contain timestamps", str(context.exception))
    
    def test_mixed_timestamp_formats(self):
        """Test handling of mixed MM:SS and HH:MM:SS formats"""
        mixed_text = """[00:30] Short format start.
[00:00:45] Long format follows.
[01:15] Back to short format.
[00:02:00] Long format again."""
        
        srt_content = self.converter.timestamp_to_srt(mixed_text)
        
        # Should handle both formats correctly
        self.assertIn("00:00:30,000", srt_content)  # 00:30 -> 00:00:30
        self.assertIn("00:00:45,000", srt_content)  # Already in HH:MM:SS
        self.assertIn("00:01:15,000", srt_content)  # 01:15 -> 00:01:15
        self.assertIn("00:02:00,000", srt_content)  # Already in HH:MM:SS
    
    def test_long_text_splitting(self):
        """Test splitting of long subtitle text"""
        long_segment = "[00:00] " + "word " * 30  # Very long text
        srt_content = self.converter.timestamp_to_srt(long_segment, max_chars_per_line=42)
        
        # Extract the text part
        lines = srt_content.split('\n')
        text_lines = [line for line in lines[2:] if line and not line[0].isdigit()]
        
        # Should be split into multiple lines
        for line in text_lines:
            self.assertLessEqual(len(line), 50)  # Some flexibility


if __name__ == '__main__':
    unittest.main()