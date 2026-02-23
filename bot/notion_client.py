"""
Notion API client for Open-Scribe Cloud
Stores transcription results in a Notion database
"""

import logging
from typing import Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_RICH_TEXT_LENGTH = 2000  # Notion's limit per rich_text block


@dataclass
class TranscriptionResult:
    """Structured result from transcription pipeline"""

    title: str
    url: str
    engine: str
    transcript: str
    summary: Optional[str] = None
    srt: Optional[str] = None
    duration: Optional[int] = None
    keywords: Optional[list[str]] = None
    status: str = "completed"


class NotionClient:
    """Async Notion API client for storing transcription results"""

    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id
        self._client = httpx.AsyncClient(
            base_url=NOTION_API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()

    async def create_page(self, result: TranscriptionResult) -> Optional[str]:
        """
        Create a new page in the Notion database with transcription results.

        Args:
            result: Transcription result data

        Returns:
            Page ID if successful, None otherwise
        """
        # Build properties
        properties = {
            "Title": {"title": [{"text": {"content": result.title[:2000]}}]},
            "URL": {"url": result.url},
            "Engine": {"select": {"name": result.engine}},
            "Status": {"select": {"name": result.status}},
        }

        if result.duration is not None:
            properties["Duration"] = {"number": result.duration}

        if result.keywords:
            properties["Keywords"] = {
                "multi_select": [{"name": kw[:100]} for kw in result.keywords[:10]]
            }

        # Build page content blocks
        children = []

        # Transcript section
        if result.transcript:
            children.append(_heading_block("Transcript"))
            children.extend(_text_to_blocks(result.transcript))

        # Summary section
        if result.summary:
            children.append(_heading_block("Summary"))
            children.extend(_text_to_blocks(result.summary))

        # SRT section
        if result.srt:
            children.append(_heading_block("SRT"))
            children.extend(_text_to_blocks(result.srt))

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
            "children": children[:100],  # Notion limit: 100 blocks per request
        }

        try:
            resp = await self._client.post("/pages", json=payload)
            resp.raise_for_status()
            page_data = resp.json()
            page_id = page_data["id"]
            logger.info("Created Notion page: %s", page_id)

            # If there are more than 100 blocks, append them in batches
            remaining_blocks = children[100:]
            if remaining_blocks:
                await self._append_blocks(page_id, remaining_blocks)

            return page_id

        except httpx.HTTPStatusError as e:
            logger.error(
                "Notion API error: %s %s", e.response.status_code, e.response.text
            )
            return None
        except Exception as e:
            logger.error("Failed to create Notion page: %s", e)
            return None

    async def update_status(self, page_id: str, status: str) -> bool:
        """
        Update the status of an existing page.

        Args:
            page_id: Notion page ID
            status: New status value

        Returns:
            True if successful
        """
        payload = {"properties": {"Status": {"select": {"name": status}}}}

        try:
            resp = await self._client.patch(f"/pages/{page_id}", json=payload)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error("Failed to update Notion page status: %s", e)
            return False

    async def _append_blocks(self, page_id: str, blocks: list[dict]) -> bool:
        """Append blocks to an existing page in batches of 100"""
        for i in range(0, len(blocks), 100):
            batch = blocks[i : i + 100]
            try:
                resp = await self._client.patch(
                    f"/blocks/{page_id}/children",
                    json={"children": batch},
                )
                resp.raise_for_status()
            except Exception as e:
                logger.error("Failed to append blocks to page %s: %s", page_id, e)
                return False
        return True

    async def get_recent_pages(self, limit: int = 10) -> list[dict]:
        """
        Query recent pages from the database.

        Args:
            limit: Maximum number of pages to return

        Returns:
            List of page data dictionaries
        """
        payload = {
            "page_size": min(limit, 100),
            "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        }

        try:
            resp = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = []
            for page in data.get("results", []):
                props = page.get("properties", {})
                title_prop = props.get("Title", {}).get("title", [])
                title = title_prop[0]["text"]["content"] if title_prop else "Untitled"

                url_prop = props.get("URL", {}).get("url", "")
                status_prop = props.get("Status", {}).get("select", {})
                status = (
                    status_prop.get("name", "unknown") if status_prop else "unknown"
                )
                engine_prop = props.get("Engine", {}).get("select", {})
                engine = engine_prop.get("name", "") if engine_prop else ""

                pages.append(
                    {
                        "id": page["id"],
                        "title": title,
                        "url": url_prop,
                        "status": status,
                        "engine": engine,
                        "created_time": page.get("created_time", ""),
                        "notion_url": page.get("url", ""),
                    }
                )

            return pages

        except Exception as e:
            logger.error("Failed to query Notion database: %s", e)
            return []


def _heading_block(text: str) -> dict:
    """Create a heading_2 block"""
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _text_to_blocks(text: str) -> list[dict]:
    """
    Convert long text to multiple paragraph blocks, respecting the 2000-char limit.
    Splits on paragraph boundaries when possible.
    """
    blocks = []

    # Split text into chunks of at most MAX_RICH_TEXT_LENGTH
    remaining = text
    while remaining:
        if len(remaining) <= MAX_RICH_TEXT_LENGTH:
            chunk = remaining
            remaining = ""
        else:
            # Try to split at a newline near the limit
            split_pos = remaining.rfind("\n", 0, MAX_RICH_TEXT_LENGTH)
            if split_pos <= 0:
                # No good newline break, split at word boundary
                split_pos = remaining.rfind(" ", 0, MAX_RICH_TEXT_LENGTH)
            if split_pos <= 0:
                # No good break at all, hard split
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
