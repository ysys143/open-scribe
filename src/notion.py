"""
Notion API client for local CLI mode.
Saves transcription results to a Notion database when configured.
"""

import os
from typing import Optional

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_RICH_TEXT_LENGTH = 2000


def _get_client():
    """Lazy import httpx to keep it optional"""
    try:
        import httpx
        return httpx
    except ImportError:
        return None


def is_configured() -> bool:
    """Check if Notion integration is enabled and configured"""
    if os.getenv("OPEN_SCRIBE_NOTION", "false").lower() != "true":
        return False
    return bool(os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"))


def save_to_notion(
    title: str,
    url: str,
    engine: str,
    transcript: str,
    summary: Optional[str] = None,
    srt: Optional[str] = None,
    duration: Optional[int] = None,
) -> Optional[str]:
    """
    Save transcription result to Notion. Returns page ID or None on failure.
    """
    httpx = _get_client()
    if not httpx:
        print("Warning: httpx not installed, skipping Notion save (pip install httpx)")
        return None

    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not api_key or not database_id:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    properties = {
        "Title": {"title": [{"text": {"content": title[:2000]}}]},
        "URL": {"url": url},
        "Engine": {"select": {"name": engine}},
        "Status": {"select": {"name": "completed"}},
    }

    if duration is not None:
        properties["Duration"] = {"number": duration}

    children = []

    if transcript:
        children.append(_heading_block("Transcript"))
        children.extend(_text_to_blocks(transcript))

    if summary:
        children.append(_heading_block("Summary"))
        children.extend(_text_to_blocks(summary))

    if srt:
        children.append(_heading_block("SRT"))
        children.extend(_text_to_blocks(srt))

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": children[:100],
    }

    try:
        client = httpx.Client(base_url=NOTION_API_BASE, headers=headers, timeout=30.0)
        resp = client.post("/pages", json=payload)
        resp.raise_for_status()
        page_data = resp.json()
        page_id = page_data["id"]

        remaining = children[100:]
        for i in range(0, len(remaining), 100):
            batch = remaining[i : i + 100]
            resp = client.patch(
                f"/blocks/{page_id}/children", json={"children": batch}
            )
            resp.raise_for_status()

        client.close()
        return page_id

    except Exception as e:
        print(f"Warning: Failed to save to Notion: {e}")
        return None


def _heading_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _text_to_blocks(text: str) -> list:
    blocks = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_RICH_TEXT_LENGTH:
            chunk = remaining
            remaining = ""
        else:
            split_pos = remaining.rfind("\n", 0, MAX_RICH_TEXT_LENGTH)
            if split_pos <= 0:
                split_pos = remaining.rfind(" ", 0, MAX_RICH_TEXT_LENGTH)
            if split_pos <= 0:
                split_pos = MAX_RICH_TEXT_LENGTH
            chunk = remaining[:split_pos]
            remaining = remaining[split_pos:].lstrip("\n")

        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            }
        )
    return blocks
