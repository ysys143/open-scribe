"""
Keyword extraction from transcripts using OpenAI
"""

from src.core.providers.models import TextClient,model,text_available
from src.core.config.settings import Config


def extract_keywords(text: str, max_keywords: int = 8) -> list[str]:
    """
    Extract keywords from transcript or summary text.
    Uses summary if short enough, otherwise truncates transcript.

    Returns:
        list of keyword strings (empty list on failure)
    """
    if not text_available('keywords') or not text.strip():
        return []

    # Use at most 3000 chars to keep cost low
    input_text = text[:3000]

    try:
        client = TextClient('keywords')
        response = client.chat.completions.create(
            model=model('keywords'),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Extract up to {max_keywords} topic keywords or key phrases "
                        "from the given text. Return ONLY a comma-separated list, "
                        "no numbering, no explanation. Each keyword should be 1-3 words. "
                        "Use the original language of the text for keywords."
                    ),
                },
                {"role": "user", "content": input_text},
            ],
            max_tokens=200,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        keywords = [kw.strip() for kw in raw.split(",") if kw.strip()]
        return keywords[:max_keywords]

    except Exception:
        return []
