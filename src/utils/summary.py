"""
Summary generation utilities
"""

import os
import sys
from pathlib import Path
from typing import Optional
from openai import OpenAI

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import Config


def generate_summary(transcript: str, verbose: bool = False) -> Optional[str]:
    """
    Generate AI summary of transcript using OpenAI
    
    Args:
        transcript: The transcript text to summarize
        verbose: Whether to print verbose output
        
    Returns:
        str: Summary text or None if failed
    """
    if not Config.OPENAI_API_KEY:
        if verbose:
            print("Error: OPENAI_API_KEY not set")
        return None
    
    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Get model from config
        model = Config.OPENAI_SUMMARY_MODEL
        
        # Get language preference from config
        summary_lang = Config.OPENAI_SUMMARY_LANGUAGE
        
        # Prepare the prompt
        system_prompt = """You are a helpful assistant that creates concise, well-structured summaries of video transcripts.
Your summaries should:
1. Capture the main topics and key points
2. Be organized with clear sections if the content covers multiple topics
3. Include important details, facts, or insights mentioned
4. Be written in clear, professional language
5. Use bullet points for lists when appropriate"""

        # Add language instruction based on preference
        if summary_lang.lower() == 'auto':
            # auto - use source language
            system_prompt += "\n\nProvide the summary in the same language as the source transcript."
            lang_instruction = ""
        else:
            # Use any language specified by user
            system_prompt += f"\n\nPlease provide the summary in {summary_lang}."
            lang_instruction = f"in {summary_lang} "

        user_prompt = f"""Please provide {lang_instruction}a comprehensive summary of the following video transcript:

{transcript[:2000000]}  # Limit to ~2M chars to stay within token limits

요약 형식:

개요
- 영상의 주요 내용을 2-3문장으로 요약

주요 주제/섹션
- 각 주요 섹션 제목 [MM:SS] 또는 [HH:MM:SS] 형식으로 시작 시간 표시
  - 하위 항목들은 들여쓰기로 구조화
  - 세부 설명은 타임코드 없이 내용만 기술
  - 중요한 전환점이나 새로운 주제 시작 시점의 타임코드를 전사 텍스트에서 찾아 삽입

타임코드 추출 규칙:
1. 전사 텍스트에 [00:00], [1:23:45] 등의 타임스탬프가 있으면 해당 섹션의 시작 시간으로 사용
2. 주제가 전환되는 첫 번째 타임스탬프를 해당 섹션의 시작 시간으로 설정
3. 타임코드가 없는 전사의 경우 섹션 제목만 표시 (타임코드 생략)

예시 형식:
주요 주제/섹션
- 도입부 및 주제 소개 [00:00]
  - 오늘 다룰 내용 개요
  - 사용할 도구 소개
- 실습 데모 시작 [05:23]
  - 환경 설정
  - 첫 번째 예제 실행
  - 결과 분석

핵심 포인트 및 세부 내용
- 주요 인사이트와 중요한 정보들
- 구체적인 팁, 통계, 사실 등

결론 및 권장사항
- 핵심 메시지 요약"""

        if verbose:
            print(f"Generating summary with {model}...")
        
        # Make API call
        # Use max_completion_tokens for newer models like gpt-5-mini
        completion_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        }
        
        # Use appropriate parameter based on model
        if model.startswith('gpt-5'):
            # gpt-5 models only support default temperature
            pass
        else:
            completion_params["max_tokens"] = 1000
            completion_params["temperature"] = 0.3  # Lower temperature for more focused summaries
            
        response = client.chat.completions.create(**completion_params)
        
        summary = response.choices[0].message.content
        
        if verbose:
            print("Summary generated successfully")
        
        return summary
        
    except Exception as e:
        if verbose:
            print(f"Error generating summary: {e}")
        return None


def format_summary_output(summary: str, video_title: str) -> str:
    """
    Format summary with title and structure
    
    Args:
        summary: The summary text
        video_title: Title of the video
        
    Returns:
        str: Formatted summary
    """
    formatted = f"""
================================================================================
VIDEO SUMMARY
================================================================================

Title: {video_title}

{summary}

================================================================================
"""
    return formatted