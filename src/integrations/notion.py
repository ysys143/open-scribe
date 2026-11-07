"""
Notion API client for local CLI mode.
Saves transcription results to a Notion database when configured.
"""

from src.core.config.document import load_settings
from src.core.providers.models import credential
from typing import Optional
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json

from src.core.speech.checkpoint import write_json

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
    if not load_settings()['integrations']['notion']['enabled']:
        return False
    return bool(credential('notion') and load_settings()['integrations']['notion']['database_id'])


def save_to_notion(
    title: str,
    url: Optional[str],
    engine: str,
    transcript: str,
    summary: Optional[str] = None,
    srt: Optional[str] = None,
    duration: Optional[int] = None,
    keywords: Optional[list] = None,
    created_at: Optional[str] = None,
    status: str = "completed",
    state_path: Optional[Path] = None,
) -> Optional[str]:
    """
    Save transcription result to Notion. Returns page ID only after all blocks save.

    state_path records intent before writes and the page ID before appending.
    An unknown outcome requires reconciliation; it is never automatically retried.
    Callers omitting state_path have no durable retry protection.
    """
    httpx = _get_client()
    if not httpx:
        print("Warning: httpx not installed, skipping Notion save (pip install httpx)")
        return None

    api_key = credential('notion')
    database_id = load_settings()['integrations']['notion']['database_id']
    if not api_key or not database_id:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    properties = {
        "Title": {"title": [{"text": {"content": title[:2000]}}]},
        "Engine": {"select": {"name": engine}},
        "Status": {"select": {"name": status}},
    }

    parsed_url = urlsplit(url or "")
    if parsed_url.scheme in ("http", "https") and parsed_url.netloc:
        properties["URL"] = {"url": url}

    if duration is not None:
        h, rem = divmod(int(duration), 3600)
        m, s = divmod(rem, 60)
        dur_str = f"{h}:{m:02d}:{s:02d}"
        properties["Duration"] = {
            "rich_text": [{"text": {"content": dur_str}}]
        }

    if keywords:
        properties["Keywords"] = {
            "multi_select": [{"name": kw[:100]} for kw in keywords[:10]]
        }

    if created_at:
        properties["Date"] = {"date": {"start": created_at[:10]}}

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

    # Bind receipts to content and destination so stale results cannot look successful.
    fingerprint = hashlib.sha256(json.dumps({**payload, "children": children}, sort_keys=True).encode()).hexdigest()
    state = {"status": "pending", "page_id": None, "payload_sha256": fingerprint}
    client = None
    try:
        if state_path and Path(state_path).exists():
            state = json.loads(Path(state_path).read_text(encoding="utf-8"))
            if state.get("payload_sha256") != fingerprint:
                print(f"Warning: Notion content changed; reconcile saved state: {state_path}")
                return None
            if state.get("status") == "completed" and state.get("page_id"):
                return state["page_id"]
            # Includes process termination during a request or receipt persistence.
            print(f"Warning: Notion outcome requires reconciliation: {state_path}")
            return None

        client = httpx.Client(base_url=NOTION_API_BASE, headers=headers, timeout=30.0)
        state["status"] = "unknown"
        if state_path:
            write_json(state_path, state)
        resp = client.post("/pages", json=payload)
        resp.raise_for_status()
        page_id = resp.json()["id"]
        state.update(page_id=page_id, status="partial", next_block=min(100, len(children)))
        if state_path:
            write_json(state_path, state)

        for i in range(100, len(children), 100):
            state["status"] = "unknown"
            if state_path:
                write_json(state_path, state)
            resp = client.patch(
                f"/blocks/{page_id}/children", json={"children": children[i:i + 100]}
            )
            resp.raise_for_status()
            state.update(status="partial", next_block=min(i + 100, len(children)))
            if state_path:
                write_json(state_path, state)

        state["status"] = "completed"
        if state_path:
            write_json(state_path, state)
        return page_id
    except Exception as e:
        print(f"Warning: Failed to save to Notion: {e}")
        return None
    finally:
        if client is not None:
            client.close()


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
