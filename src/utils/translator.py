"""
Subtitle translation module with automatic language detection
"""

import re
from typing import Optional, Dict, List, Tuple
from collections import Counter
from openai import OpenAI

from ..config import Config


class LanguageDetector:
    """Detect language using character-based heuristics"""
    
    # Language character patterns
    PATTERNS = {
        'korean': re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\ud7b0-\ud7ff]'),
        'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3400-\u4dbf]'),
        'chinese': re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f]'),
        'arabic': re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]'),
        'hebrew': re.compile(r'[\u0590-\u05ff]'),
        'cyrillic': re.compile(r'[\u0400-\u04ff\u0500-\u052f\u2de0-\u2dff\ua640-\ua69f]'),
        'thai': re.compile(r'[\u0e00-\u0e7f]'),
        'devanagari': re.compile(r'[\u0900-\u097f\ua8e0-\ua8ff]'),  # Hindi, Sanskrit
    }
    
    # Common words for additional verification
    COMMON_WORDS = {
        'english': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'for', 'with', 'as', 'on', 'was', 'at'],
        'korean': ['이', '그', '저', '것', '은', '는', '을', '를', '에', '의', '와', '과', '하다', '있다', '되다'],
        'japanese': ['の', 'に', 'は', 'を', 'が', 'で', 'と', 'から', 'です', 'ます', 'こと', 'する', 'ある', 'いる'],
        'chinese': ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这', '中', '大', '为', '上', '个'],
        'spanish': ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber', 'por', 'con', 'su'],
        'french': ['le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'son', 'que', 'se', 'qui', 'ce'],
        'german': ['der', 'die', 'und', 'in', 'das', 'von', 'zu', 'mit', 'sich', 'auf', 'für', 'ist', 'nicht', 'ein'],
        'portuguese': ['o', 'de', 'e', 'a', 'que', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no'],
        'russian': ['и', 'в', 'не', 'на', 'я', 'с', 'что', 'а', 'по', 'он', 'она', 'это', 'к', 'но', 'из'],
    }
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect the primary language of the text
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language name (e.g., 'korean', 'english', 'japanese')
        """
        if not text:
            return 'unknown'
        
        # Clean text for analysis
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Count character types
        char_counts = {}
        total_chars = 0
        
        for lang, pattern in LanguageDetector.PATTERNS.items():
            matches = pattern.findall(text)
            count = len(matches)
            if count > 0:
                char_counts[lang] = count
                total_chars += count
        
        # Check for Latin script (could be many languages)
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        if latin_chars > total_chars * 0.5:  # More than 50% Latin
            # Use common words to distinguish between Latin-script languages
            lang_scores = {}
            
            for lang, common_words in LanguageDetector.COMMON_WORDS.items():
                if lang in ['korean', 'japanese', 'chinese', 'russian']:
                    continue  # Skip non-Latin languages
                
                score = sum(1 for word in common_words if word in words)
                if score > 0:
                    lang_scores[lang] = score
            
            if lang_scores:
                # Return language with highest score
                return max(lang_scores, key=lang_scores.get)
            else:
                return 'english'  # Default to English for Latin script
        
        # For non-Latin scripts, use character counts
        if char_counts:
            # Get language with most characters
            primary_lang = max(char_counts, key=char_counts.get)
            
            # Special handling for CJK languages
            if primary_lang == 'chinese':
                # Check if it might be Japanese (has hiragana/katakana)
                if 'japanese' in char_counts and char_counts['japanese'] > 10:
                    return 'japanese'
            
            return primary_lang
        
        return 'english'  # Default fallback
    
    @staticmethod
    def get_language_code(language: str) -> str:
        """Convert language name to ISO 639-1 code"""
        language_codes = {
            'english': 'en',
            'korean': 'ko',
            'japanese': 'ja',
            'chinese': 'zh',
            'spanish': 'es',
            'french': 'fr',
            'german': 'de',
            'portuguese': 'pt',
            'russian': 'ru',
            'arabic': 'ar',
            'hebrew': 'he',
            'thai': 'th',
            'hindi': 'hi',
        }
        return language_codes.get(language.lower(), 'en')


class SubtitleTranslator:
    """Translate subtitles using OpenAI API with automatic language detection"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.translate_model = config.OPENAI_TRANSLATE_MODEL
        self.target_language = config.OPENAI_TRANSLATE_LANGUAGE
        self.detector = LanguageDetector()
    
    def translate_text(
        self, 
        text: str, 
        target_language: Optional[str] = None,
        preserve_timestamps: bool = True,
        verbose: bool = False
    ) -> Tuple[str, bool]:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language (uses config default if not specified)
            preserve_timestamps: Keep timestamp markers in translation
            verbose: Show detailed progress
            
        Returns:
            Tuple of (translated_text, was_translated)
        """
        if not self.client:
            print("[Translator] Error: OpenAI API key not configured")
            return text, False
        
        # Use provided target or default from config
        target_lang = target_language or self.target_language
        
        # Detect source language
        source_lang = self.detector.detect_language(text)
        
        if verbose:
            print(f"[Translator] Detected language: {source_lang}")
            print(f"[Translator] Target language: {target_lang.lower()}")
        
        # Check if translation is needed
        if self._same_language(source_lang, target_lang):
            if verbose:
                print(f"[Translator] Source and target languages are the same ({source_lang}). Skipping translation.")
            return text, False
        
        # Handle timestamped text
        if preserve_timestamps and self._has_timestamps(text):
            return self._translate_timestamped_text(text, source_lang, target_lang, verbose)
        
        # Translate plain text
        return self._translate_plain_text(text, source_lang, target_lang, verbose)
    
    def _same_language(self, lang1: str, lang2: str) -> bool:
        """Check if two language identifiers refer to the same language"""
        # Normalize language names
        lang1_norm = lang1.lower().strip()
        lang2_norm = lang2.lower().strip()
        
        # Direct match
        if lang1_norm == lang2_norm:
            return True
        
        # Check aliases
        aliases = {
            'korean': ['ko', 'kor', '한국어', '한글'],
            'english': ['en', 'eng', '영어'],
            'japanese': ['ja', 'jp', 'jpn', '일본어', '일어'],
            'chinese': ['zh', 'cn', 'chi', '중국어', '중어'],
            'spanish': ['es', 'esp', 'spa', '스페인어'],
            'french': ['fr', 'fra', 'fre', '프랑스어', '불어'],
            'german': ['de', 'deu', 'ger', '독일어', '독어'],
        }
        
        for lang, alias_list in aliases.items():
            if lang1_norm in alias_list and lang2_norm in alias_list:
                return True
            if (lang1_norm == lang or lang1_norm in alias_list) and \
               (lang2_norm == lang or lang2_norm in alias_list):
                return True
        
        return False
    
    def _has_timestamps(self, text: str) -> bool:
        """Check if text contains timestamps"""
        return bool(re.search(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', text))
    
    def _translate_timestamped_text(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        verbose: bool
    ) -> Tuple[str, bool]:
        """Translate text while preserving timestamps"""
        
        # Parse timestamped segments
        segments = []
        pattern = r'(\[\d{1,2}:\d{2}(?::\d{2})?\])\s*([^\[]*)'
        matches = re.findall(pattern, text)
        
        if not matches:
            return text, False
        
        if verbose:
            print(f"[Translator] Translating {len(matches)} segments...")
        
        # Collect all text for batch translation
        texts_to_translate = [segment_text.strip() for _, segment_text in matches if segment_text.strip()]
        
        if not texts_to_translate:
            return text, False
        
        # Create translation prompt
        system_prompt = f"""You are a professional subtitle translator.
Translate the following subtitles from {source_lang} to {target_lang}.
Maintain natural speech patterns and timing appropriate for subtitles.
Keep translations concise and readable.
Preserve any speaker names or sound descriptions in brackets.
"""
        
        # Create numbered list for translation
        numbered_texts = '\n'.join([f"{i+1}. {text}" for i, text in enumerate(texts_to_translate)])
        
        user_prompt = f"""Translate these subtitle segments to {target_lang}:

{numbered_texts}

Return ONLY the translations in the same numbered format, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.translate_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent translation
                max_tokens=4000
            )
            
            translated_content = response.choices[0].message.content.strip()
            
            # Parse translations
            translations = {}
            for line in translated_content.split('\n'):
                match = re.match(r'^(\d+)\.\s*(.+)', line.strip())
                if match:
                    idx = int(match.group(1)) - 1
                    translation = match.group(2).strip()
                    if 0 <= idx < len(texts_to_translate):
                        translations[idx] = translation
            
            # Reconstruct timestamped text
            result = []
            text_idx = 0
            
            for timestamp, segment_text in matches:
                if segment_text.strip():
                    if text_idx in translations:
                        result.append(f"{timestamp} {translations[text_idx]}")
                    else:
                        # Fallback to original if translation missing
                        result.append(f"{timestamp} {segment_text.strip()}")
                    text_idx += 1
                else:
                    result.append(timestamp)
            
            translated_text = '\n'.join(result)
            
            if verbose:
                print(f"[Translator] Translation completed")
            
            return translated_text, True
            
        except Exception as e:
            print(f"[Translator] Error during translation: {e}")
            return text, False
    
    def _translate_plain_text(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        verbose: bool
    ) -> Tuple[str, bool]:
        """Translate plain text without timestamps"""
        
        system_prompt = f"""You are a professional translator.
Translate from {source_lang} to {target_lang}.
Maintain the original tone and style.
Preserve any formatting or line breaks."""
        
        user_prompt = f"""Translate this text to {target_lang}:

{text}

Return ONLY the translation, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.translate_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            if verbose:
                print(f"[Translator] Translation completed")
            
            return translated_text, True
            
        except Exception as e:
            print(f"[Translator] Error during translation: {e}")
            return text, False
    
    def translate_srt(
        self, 
        srt_content: str, 
        target_language: Optional[str] = None,
        verbose: bool = False
    ) -> Tuple[str, bool]:
        """
        Translate SRT subtitle file content
        
        Args:
            srt_content: SRT formatted content
            target_language: Target language
            verbose: Show detailed progress
            
        Returns:
            Tuple of (translated_srt, was_translated)
        """
        target_lang = target_language or self.target_language
        
        # Parse SRT entries
        entries = srt_content.strip().split('\n\n')
        translated_entries = []
        
        any_translated = False
        
        for entry in entries:
            lines = entry.split('\n')
            if len(lines) >= 3:
                # Keep index and timecode
                index = lines[0]
                timecode = lines[1]
                subtitle_text = '\n'.join(lines[2:])
                
                # Translate subtitle text
                translated_text, was_translated = self.translate_text(
                    subtitle_text,
                    target_lang,
                    preserve_timestamps=False,
                    verbose=False
                )
                
                if was_translated:
                    any_translated = True
                
                # Reconstruct entry
                translated_entry = f"{index}\n{timecode}\n{translated_text}"
                translated_entries.append(translated_entry)
            else:
                # Keep malformed entries as-is
                translated_entries.append(entry)
        
        if verbose and any_translated:
            print(f"[Translator] SRT translation completed")
        
        return '\n\n'.join(translated_entries), any_translated