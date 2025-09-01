"""
Unit tests for translator module
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.utils.translator import LanguageDetector, SubtitleTranslator
from src.config import Config


class TestLanguageDetector(unittest.TestCase):
    """Test cases for language detection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = LanguageDetector()
    
    def test_detect_korean(self):
        """Test Korean language detection"""
        korean_texts = [
            "안녕하세요. 반갑습니다.",
            "이것은 한국어 텍스트입니다.",
            "오늘 날씨가 좋네요.",
            "한글은 세종대왕이 만든 문자입니다."
        ]
        
        for text in korean_texts:
            detected = self.detector.detect_language(text)
            self.assertEqual(detected, 'korean', f"Failed to detect Korean in: {text}")
    
    def test_detect_english(self):
        """Test English language detection"""
        english_texts = [
            "Hello, how are you today?",
            "This is an English text.",
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is fascinating."
        ]
        
        for text in english_texts:
            detected = self.detector.detect_language(text)
            self.assertEqual(detected, 'english', f"Failed to detect English in: {text}")
    
    def test_detect_japanese(self):
        """Test Japanese language detection"""
        japanese_texts = [
            "こんにちは、元気ですか？",
            "今日はいい天気ですね。",
            "日本語を勉強しています。",
            "ありがとうございます。"
        ]
        
        for text in japanese_texts:
            detected = self.detector.detect_language(text)
            self.assertEqual(detected, 'japanese', f"Failed to detect Japanese in: {text}")
    
    def test_detect_chinese(self):
        """Test Chinese language detection"""
        chinese_texts = [
            "你好，很高兴见到你。",
            "今天天气很好。",
            "我正在学习中文。",
            "这是一个测试。"
        ]
        
        for text in chinese_texts:
            detected = self.detector.detect_language(text)
            self.assertIn(detected, ['chinese', 'japanese'], f"Failed to detect CJK in: {text}")
    
    def test_detect_mixed_language(self):
        """Test mixed language detection (should detect dominant language)"""
        # Mostly Korean with some English
        mixed_korean = "안녕하세요. This is a test. 한국어가 더 많습니다."
        self.assertEqual(self.detector.detect_language(mixed_korean), 'korean')
        
        # Mostly English with some Korean
        mixed_english = "This is mainly English text with some 한글 mixed in."
        self.assertEqual(self.detector.detect_language(mixed_english), 'english')
    
    def test_detect_empty_text(self):
        """Test empty text handling"""
        self.assertEqual(self.detector.detect_language(""), 'unknown')
        self.assertEqual(self.detector.detect_language(None), 'unknown')
    
    def test_get_language_code(self):
        """Test language code conversion"""
        self.assertEqual(self.detector.get_language_code('english'), 'en')
        self.assertEqual(self.detector.get_language_code('korean'), 'ko')
        self.assertEqual(self.detector.get_language_code('japanese'), 'ja')
        self.assertEqual(self.detector.get_language_code('chinese'), 'zh')
        self.assertEqual(self.detector.get_language_code('unknown'), 'en')  # Default


class TestSubtitleTranslator(unittest.TestCase):
    """Test cases for subtitle translation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.config = Mock(spec=Config)
        self.config.OPENAI_API_KEY = "test-key"
        self.config.OPENAI_TRANSLATE_MODEL = "gpt-4o-mini"
        self.config.OPENAI_TRANSLATE_LANGUAGE = "Korean"
        
        # Create translator with mocked OpenAI client
        with patch('src.utils.translator.OpenAI'):
            self.translator = SubtitleTranslator(self.config)
            self.translator.client = MagicMock()
    
    def test_same_language_detection(self):
        """Test same language detection"""
        # Direct matches
        self.assertTrue(self.translator._same_language('korean', 'korean'))
        self.assertTrue(self.translator._same_language('Korean', 'korean'))
        self.assertTrue(self.translator._same_language('KOREAN', 'korean'))
        
        # Alias matches
        self.assertTrue(self.translator._same_language('korean', 'ko'))
        self.assertTrue(self.translator._same_language('한국어', 'korean'))
        self.assertTrue(self.translator._same_language('en', 'english'))
        self.assertTrue(self.translator._same_language('영어', 'english'))
        
        # Different languages
        self.assertFalse(self.translator._same_language('korean', 'english'))
        self.assertFalse(self.translator._same_language('ja', 'zh'))
    
    def test_has_timestamps(self):
        """Test timestamp detection"""
        # With timestamps
        self.assertTrue(self.translator._has_timestamps("[00:00] Text"))
        self.assertTrue(self.translator._has_timestamps("[00:00:00] Text"))
        self.assertTrue(self.translator._has_timestamps("Text [01:30] more text"))
        
        # Without timestamps
        self.assertFalse(self.translator._has_timestamps("Plain text"))
        self.assertFalse(self.translator._has_timestamps("Time is 00:00"))
        self.assertFalse(self.translator._has_timestamps("[not-a-timestamp]"))
    
    def test_skip_translation_same_language(self):
        """Test that translation is skipped for same language"""
        # Mock language detection to return Korean
        with patch.object(self.translator.detector, 'detect_language', return_value='korean'):
            text = "안녕하세요"
            translated, was_translated = self.translator.translate_text(text, target_language='Korean')
            
            # Should return original text without translation
            self.assertEqual(translated, text)
            self.assertFalse(was_translated)
            
            # OpenAI API should not be called
            self.translator.client.chat.completions.create.assert_not_called()
    
    def test_translate_different_language(self):
        """Test translation for different language"""
        # Mock language detection and OpenAI response
        with patch.object(self.translator.detector, 'detect_language', return_value='english'):
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "안녕하세요"
            self.translator.client.chat.completions.create.return_value = mock_response
            
            text = "Hello"
            translated, was_translated = self.translator.translate_text(text, target_language='Korean')
            
            # Should return translated text
            self.assertEqual(translated, "안녕하세요")
            self.assertTrue(was_translated)
            
            # OpenAI API should be called
            self.translator.client.chat.completions.create.assert_called_once()
    
    def test_translate_timestamped_text(self):
        """Test translation of timestamped text"""
        timestamped_text = "[00:00] Hello world\n[00:05] How are you?"
        
        with patch.object(self.translator.detector, 'detect_language', return_value='english'):
            # Mock OpenAI response with numbered translations
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "1. 안녕하세요 세계\n2. 어떻게 지내세요?"
            self.translator.client.chat.completions.create.return_value = mock_response
            
            translated, was_translated = self.translator.translate_text(
                timestamped_text,
                target_language='Korean',
                preserve_timestamps=True
            )
            
            # Should preserve timestamps
            self.assertIn("[00:00]", translated)
            self.assertIn("[00:05]", translated)
            self.assertIn("안녕하세요 세계", translated)
            self.assertIn("어떻게 지내세요?", translated)
            self.assertTrue(was_translated)
    
    def test_translate_srt_content(self):
        """Test SRT content translation"""
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Hello world

2
00:00:05,000 --> 00:00:10,000
How are you?"""
        
        with patch.object(self.translator.detector, 'detect_language', return_value='english'):
            # Mock translations
            def mock_translate(text, target, preserve_timestamps, verbose):
                translations = {
                    "Hello world": ("안녕하세요 세계", True),
                    "How are you?": ("어떻게 지내세요?", True)
                }
                return translations.get(text, (text, False))
            
            with patch.object(self.translator, 'translate_text', side_effect=mock_translate):
                translated_srt, was_translated = self.translator.translate_srt(
                    srt_content,
                    target_language='Korean'
                )
                
                # Should preserve SRT structure
                self.assertIn("00:00:00,000 --> 00:00:05,000", translated_srt)
                self.assertIn("안녕하세요 세계", translated_srt)
                self.assertIn("어떻게 지내세요?", translated_srt)
                self.assertTrue(was_translated)
    
    def test_no_api_key_error(self):
        """Test error handling when API key is missing"""
        # Create translator without API key
        config_no_key = Mock(spec=Config)
        config_no_key.OPENAI_API_KEY = None
        config_no_key.OPENAI_TRANSLATE_MODEL = "gpt-4o-mini"
        config_no_key.OPENAI_TRANSLATE_LANGUAGE = "Korean"
        
        translator_no_key = SubtitleTranslator(config_no_key)
        
        text = "Hello"
        translated, was_translated = translator_no_key.translate_text(text)
        
        # Should return original text
        self.assertEqual(translated, text)
        self.assertFalse(was_translated)
    
    def test_api_error_handling(self):
        """Test handling of API errors"""
        with patch.object(self.translator.detector, 'detect_language', return_value='english'):
            # Mock API error
            self.translator.client.chat.completions.create.side_effect = Exception("API Error")
            
            text = "Hello"
            translated, was_translated = self.translator.translate_text(text, target_language='Korean')
            
            # Should return original text on error
            self.assertEqual(translated, text)
            self.assertFalse(was_translated)
    
    def test_empty_text_translation(self):
        """Test handling of empty text"""
        translated, was_translated = self.translator.translate_text("", target_language='Korean')
        self.assertEqual(translated, "")
        self.assertFalse(was_translated)
    
    def test_language_normalization(self):
        """Test language name normalization in same_language check"""
        # Test various formats
        test_cases = [
            ('Korean', 'korean', True),
            ('ko', 'Korean', True),
            ('한국어', 'Korean', True),
            ('한글', 'ko', True),
            ('English', 'en', True),
            ('eng', 'English', True),
            ('Japanese', 'ja', True),
            ('일본어', 'Japanese', True),
            ('Korean', 'Japanese', False),
            ('en', 'ko', False),
        ]
        
        for lang1, lang2, expected in test_cases:
            result = self.translator._same_language(lang1, lang2)
            self.assertEqual(result, expected, 
                           f"Failed for {lang1} vs {lang2}: expected {expected}, got {result}")


if __name__ == '__main__':
    unittest.main()