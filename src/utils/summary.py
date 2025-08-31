"""
Summary generation utilities
"""

import os
from typing import Optional
from openai import OpenAI


def generate_summary(transcript: str, verbose: bool = False) -> Optional[str]:
    """
    Generate AI summary of transcript using OpenAI
    
    Args:
        transcript: The transcript text to summarize
        verbose: Whether to print verbose output
        
    Returns:
        str: Summary text or None if failed
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        if verbose:
            print("Error: OPENAI_API_KEY not set")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Get model from environment or use default
        model = os.getenv('OPENAI_SUMMARY_MODEL', 'gpt-4o-mini')
        
        # Prepare the prompt
        system_prompt = """You are a helpful assistant that creates concise, well-structured summaries of video transcripts.
Your summaries should:
1. Capture the main topics and key points
2. Be organized with clear sections if the content covers multiple topics
3. Include important details, facts, or insights mentioned
4. Be written in clear, professional language
5. Use bullet points for lists when appropriate"""

        user_prompt = f"""Please provide a comprehensive summary of the following video transcript:

{transcript[:15000]}  # Limit to ~15k chars to stay within token limits

Please structure the summary with:
- A brief overview (1-2 sentences)
- Main topics/sections covered
- Key points and takeaways
- Any important conclusions or recommendations"""

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
            completion_params["max_completion_tokens"] = 2000  # Increased for better summaries
            # gpt-5 models only support default temperature
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