"""
yt-dlp version check and auto-update module
Ports the daily version check logic from scribe.zsh to Python for Cloud Run
"""

import logging
import subprocess
import asyncio
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

VERSION_CHECK_FILE = Path("/tmp/.ytdlp_version_check")


def _get_current_version() -> str:
    """Get currently installed yt-dlp version"""
    try:
        from importlib.metadata import version

        return version("yt-dlp")
    except Exception:
        return "unknown"


def _do_update() -> tuple[str, str, bool]:
    """Run the actual update check. Returns (old_version, new_version, was_updated)."""
    old_version = _get_current_version()

    try:
        result = subprocess.run(
            ["pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        new_version = _get_current_version()
        was_updated = old_version != new_version

        if result.returncode != 0:
            logger.warning("yt-dlp update command failed: %s", result.stderr)
            return old_version, old_version, False

        return old_version, new_version, was_updated

    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp update timed out")
        return old_version, old_version, False
    except Exception as e:
        logger.error("yt-dlp update error: %s", e)
        return old_version, old_version, False


async def check_and_update_ytdlp() -> str:
    """
    Check and update yt-dlp if needed (once per day).

    Returns:
        Status message string
    """
    today = date.today().strftime("%Y%m%d")

    # Check if already checked today
    if VERSION_CHECK_FILE.exists():
        last_check = VERSION_CHECK_FILE.read_text().strip()
        if last_check == today:
            version = _get_current_version()
            logger.debug("yt-dlp already checked today (version: %s)", version)
            return f"yt-dlp {version} (checked today)"

    logger.info("Checking yt-dlp version...")

    # Run update in thread to avoid blocking
    old_ver, new_ver, was_updated = await asyncio.to_thread(_do_update)

    # Record today's check
    try:
        VERSION_CHECK_FILE.write_text(today)
    except Exception as e:
        logger.warning("Could not write version check file: %s", e)

    if was_updated:
        msg = f"yt-dlp updated: {old_ver} → {new_ver}"
        logger.info(msg)
    else:
        msg = f"yt-dlp is up to date: {old_ver}"
        logger.info(msg)

    return msg
