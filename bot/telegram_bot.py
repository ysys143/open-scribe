"""
Telegram Bot handler for Open-Scribe Cloud
Provides mobile interface for transcription via Telegram
"""

import os
import re
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.transcribe_worker import process_url, WorkerOptions, WorkerResult
from bot.notion_client import NotionClient, TranscriptionResult
from bot.ytdlp_updater import check_and_update_ytdlp

logger = logging.getLogger(__name__)

# Per-user engine preference stored in memory (resets on container restart)
_user_engines: dict[int, str] = {}

# Simple URL pattern
URL_PATTERN = re.compile(r"https?://\S+")

# Max Telegram message length
MAX_MESSAGE_LENGTH = 4000

# Status icons (Unicode sent to Telegram users, defined via escapes)
_ICON_OK = "\u2705"  # check mark
_ICON_FAIL = "\u274c"  # cross mark
_ICON_WAIT = "\u23f3"  # hourglass
_ICON_TIME = "\u23f1"  # stopwatch
_ICON_PKG = "\U0001f4e6"  # package
_ICON_TOOL = "\U0001f527"  # wrench
_ICON_TEXT = "\U0001f4dd"  # memo
_ICON_CLIP = "\U0001f4cb"  # clipboard
_ICON_LINK = "\U0001f4ce"  # paperclip
_ICON_UNKNOWN = "\u2753"  # question mark


def _get_notion_client() -> Optional[NotionClient]:
    """Create Notion client if configured"""
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_DATABASE_ID")
    if api_key and db_id:
        return NotionClient(api_key, db_id)
    return None


def _extract_url(text: str) -> Optional[str]:
    """Extract first URL from text"""
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


def _truncate(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 100] + "\n\n... (truncated, see full text in Notion)"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Open-Scribe Cloud\n\n"
        "YouTube URL\uc744 \ubcf4\ub0b4\uba74 \uc790\ub3d9\uc73c\ub85c transcription\uc744 "
        "\uc2dc\uc791\ud569\ub2c8\ub2e4.\n\n"
        "\uba85\ub839\uc5b4:\n"
        "/summary <URL> - transcribe + \uc694\uc57d\n"
        "/translate <URL> - transcribe + \ubc88\uc5ed\n"
        "/srt <URL> - transcribe + SRT \uc790\ub9c9\n"
        "/engine <name> - \uc5d4\uc9c4 \ubcc0\uacbd (high, medium, youtube)\n"
        "/status - \ud604\uc7ac \uc0c1\ud0dc\n"
        "/list - \ucd5c\uadfc transcription \ubaa9\ub85d\n"
        "/help - \ub3c4\uc6c0\ub9d0"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "\uc0ac\uc6a9\ubc95\n\n"
        "1. YouTube URL\uc744 \ubcf4\ub0b4\uba74 \uc790\ub3d9\uc73c\ub85c transcription "
        "\uc2dc\uc791\n"
        "2. /summary URL - \uc694\uc57d \ud3ec\ud568\n"
        "3. /translate URL - \ubc88\uc5ed \ud3ec\ud568\n"
        "4. /srt URL - SRT \uc790\ub9c9 \uc0dd\uc131\n\n"
        "\uc5d4\uc9c4 \uc635\uc158:\n"
        "- high (gpt-4o-transcribe): \ucd5c\uace0 \ud488\uc9c8\n"
        "- medium (gpt-4o-mini-transcribe): \uae30\ubcf8, \ube60\ub984\n"
        "- youtube: YouTube \uc790\ub9c9 \ucd94\ucd9c (\ubb34\ub8cc)\n\n"
        "/engine medium \uc73c\ub85c \ubcc0\uacbd \uac00\ub2a5"
    )


async def cmd_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /engine command to change transcription engine"""
    if not context.args:
        user_id = update.effective_user.id
        current = _user_engines.get(
            user_id, os.getenv("OPEN_SCRIBE_ENGINE", "gpt-4o-mini-transcribe")
        )
        await update.message.reply_text(
            f"\ud604\uc7ac \uc5d4\uc9c4: {current}\n\n"
            "\uc0ac\uc6a9 \uac00\ub2a5\ud55c \uc5d4\uc9c4:\n"
            "- high (gpt-4o-transcribe)\n"
            "- medium (gpt-4o-mini-transcribe)\n"
            "- youtube (youtube-transcript-api)\n\n"
            "\ubcc0\uacbd: /engine <name>"
        )
        return

    engine_name = context.args[0].lower()
    valid_engines = {
        "high": "gpt-4o-transcribe",
        "medium": "gpt-4o-mini-transcribe",
        "youtube": "youtube-transcript-api",
        "whisper": "whisper-api",
        "gpt-4o-transcribe": "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe": "gpt-4o-mini-transcribe",
        "whisper-api": "whisper-api",
        "youtube-transcript-api": "youtube-transcript-api",
    }

    if engine_name not in valid_engines:
        await update.message.reply_text(
            f"\uc54c \uc218 \uc5c6\ub294 \uc5d4\uc9c4: {engine_name}\n"
            "\uc0ac\uc6a9 \uac00\ub2a5: high, medium, youtube, whisper"
        )
        return

    resolved = valid_engines[engine_name]
    _user_engines[update.effective_user.id] = resolved
    await update.message.reply_text(f"\uc5d4\uc9c4 \ubcc0\uacbd\ub428: {resolved}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    ytdlp_status = await check_and_update_ytdlp()
    await update.message.reply_text(
        f"Open-Scribe Cloud \uc0c1\ud0dc: \uc815\uc0c1\nyt-dlp: {ytdlp_status}"
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command - show recent transcriptions from Notion"""
    notion = _get_notion_client()
    if not notion:
        await update.message.reply_text(
            "Notion\uc774 \uc124\uc815\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4."
        )
        return

    try:
        pages = await notion.get_recent_pages(limit=10)
        if not pages:
            await update.message.reply_text(
                "\ucd5c\uadfc transcription\uc774 \uc5c6\uc2b5\ub2c8\ub2e4."
            )
            return

        lines = ["\ucd5c\uadfc Transcriptions:\n"]
        for i, page in enumerate(pages, 1):
            status_icon = {
                "completed": _ICON_OK,
                "processing": _ICON_WAIT,
                "failed": _ICON_FAIL,
            }.get(page["status"], _ICON_UNKNOWN)
            title = page["title"][:40]
            lines.append(f"{i}. {status_icon} {title}")
            if page.get("notion_url"):
                lines.append(f"   {page['notion_url']}")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error("Failed to list pages: %s", e)
        await update.message.reply_text(f"\ubaa9\ub85d \uc870\ud68c \uc2e4\ud328: {e}")
    finally:
        await notion.close()


async def _process_and_respond(
    update: Update,
    url: str,
    options: WorkerOptions,
    status_msg,
):
    """Run transcription and send results back to Telegram"""
    notion = _get_notion_client()
    notion_page_id = None

    try:
        # Create Notion page with "processing" status first
        if notion:
            try:
                initial_result = TranscriptionResult(
                    title="Processing...",
                    url=url,
                    engine=options.engine,
                    transcript="",
                    status="processing",
                )
                notion_page_id = await notion.create_page(initial_result)
            except Exception as e:
                logger.warning("Failed to create initial Notion page: %s", e)

        # Check yt-dlp version
        await check_and_update_ytdlp()

        # Run transcription
        result: WorkerResult = await process_url(url, options)

        if not result.success:
            error_text = f"\ucc98\ub9ac \uc2e4\ud328: {result.error}"
            await status_msg.edit_text(error_text)
            if notion and notion_page_id:
                await notion.update_status(notion_page_id, "failed")
            return

        # Update Notion with full results
        notion_url = None
        if notion:
            try:
                if notion_page_id:
                    await notion.update_status(notion_page_id, "completed")

                # Create the full page (replace the placeholder)
                full_result = TranscriptionResult(
                    title=result.title,
                    url=url,
                    engine=result.engine,
                    transcript=result.transcript,
                    summary=result.summary,
                    srt=result.srt_content,
                    duration=result.duration,
                    status="completed",
                )
                new_page_id = await notion.create_page(full_result)
                if new_page_id:
                    notion_url = f"https://notion.so/{new_page_id.replace('-', '')}"

                    # Delete the old placeholder page
                    if notion_page_id and notion_page_id != new_page_id:
                        try:
                            await notion._client.patch(
                                f"/pages/{notion_page_id}",
                                json={"archived": True},
                            )
                        except Exception:
                            pass
            except Exception as e:
                logger.warning("Failed to update Notion: %s", e)

        # Build response message
        parts = []
        parts.append(f"{_ICON_OK} {result.title}\n")

        if result.duration:
            mins = result.duration // 60
            secs = result.duration % 60
            parts.append(f"{_ICON_TIME} {mins}\ubd84 {secs}\ucd08")

        if result.audio_size_mb:
            parts.append(f"{_ICON_PKG} {result.audio_size_mb} MB")

        parts.append(f"{_ICON_TOOL} \uc5d4\uc9c4: {result.engine}\n")

        # Transcript preview
        parts.append(f"{_ICON_TEXT} Transcript:")
        parts.append(_truncate(result.transcript, 2000))

        # Summary
        if result.summary:
            parts.append(f"\n{_ICON_CLIP} Summary:")
            parts.append(_truncate(result.summary, 1000))

        # Notion link
        if notion_url:
            parts.append(f"\n{_ICON_LINK} Notion: {notion_url}")

        response_text = "\n".join(parts)

        # Telegram has a 4096 char limit
        if len(response_text) > 4096:
            response_text = (
                response_text[:4000]
                + "\n\n... (Notion\uc5d0\uc11c \uc804\uccb4 \ub0b4\uc6a9 \ud655\uc778)"
            )

        await status_msg.edit_text(response_text)

    except Exception as e:
        logger.exception("Processing error")
        try:
            await status_msg.edit_text(
                f"\ucc98\ub9ac \uc911 \uc624\ub958 \ubc1c\uc0dd: {e}"
            )
        except Exception:
            pass
        if notion and notion_page_id:
            try:
                await notion.update_status(notion_page_id, "failed")
            except Exception:
                pass
    finally:
        if notion:
            await notion.close()


async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain URL messages - start transcription"""
    text = update.message.text.strip()
    url = _extract_url(text)

    if not url:
        return  # Not a URL, ignore

    user_id = update.effective_user.id
    engine = _user_engines.get(
        user_id, os.getenv("OPEN_SCRIBE_ENGINE", "gpt-4o-mini-transcribe")
    )

    status_msg = await update.message.reply_text(
        f"{_ICON_WAIT} \ucc98\ub9ac\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4..."
    )

    options = WorkerOptions(engine=engine)

    # Process in background
    context.application.create_task(
        _process_and_respond(update, url, options, status_msg)
    )


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /summary command"""
    if not context.args:
        await update.message.reply_text("\uc0ac\uc6a9\ubc95: /summary <YouTube URL>")
        return

    url = _extract_url(" ".join(context.args))
    if not url:
        await update.message.reply_text(
            "\uc62c\ubc14\ub978 URL\uc744 \uc785\ub825\ud574\uc8fc\uc138\uc694."
        )
        return

    user_id = update.effective_user.id
    engine = _user_engines.get(
        user_id, os.getenv("OPEN_SCRIBE_ENGINE", "gpt-4o-mini-transcribe")
    )

    status_msg = await update.message.reply_text(
        f"{_ICON_WAIT} \ucc98\ub9ac\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4... "
        "(transcribe + \uc694\uc57d)"
    )
    options = WorkerOptions(engine=engine, summary=True)

    context.application.create_task(
        _process_and_respond(update, url, options, status_msg)
    )


async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /translate command"""
    if not context.args:
        await update.message.reply_text("\uc0ac\uc6a9\ubc95: /translate <YouTube URL>")
        return

    url = _extract_url(" ".join(context.args))
    if not url:
        await update.message.reply_text(
            "\uc62c\ubc14\ub978 URL\uc744 \uc785\ub825\ud574\uc8fc\uc138\uc694."
        )
        return

    user_id = update.effective_user.id
    engine = _user_engines.get(
        user_id, os.getenv("OPEN_SCRIBE_ENGINE", "gpt-4o-mini-transcribe")
    )

    status_msg = await update.message.reply_text(
        f"{_ICON_WAIT} \ucc98\ub9ac\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4... "
        "(transcribe + \ubc88\uc5ed)"
    )
    options = WorkerOptions(engine=engine, translate=True)

    context.application.create_task(
        _process_and_respond(update, url, options, status_msg)
    )


async def cmd_srt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /srt command"""
    if not context.args:
        await update.message.reply_text("\uc0ac\uc6a9\ubc95: /srt <YouTube URL>")
        return

    url = _extract_url(" ".join(context.args))
    if not url:
        await update.message.reply_text(
            "\uc62c\ubc14\ub978 URL\uc744 \uc785\ub825\ud574\uc8fc\uc138\uc694."
        )
        return

    user_id = update.effective_user.id
    engine = _user_engines.get(
        user_id, os.getenv("OPEN_SCRIBE_ENGINE", "gpt-4o-mini-transcribe")
    )

    status_msg = await update.message.reply_text(
        f"{_ICON_WAIT} \ucc98\ub9ac\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4... "
        "(transcribe + SRT)"
    )
    options = WorkerOptions(engine=engine, srt=True, timestamp=True)

    context.application.create_task(
        _process_and_respond(update, url, options, status_msg)
    )


def create_bot_application(token: str) -> Application:
    """
    Create and configure the Telegram bot application.

    Args:
        token: Telegram Bot API token

    Returns:
        Configured Application instance
    """
    app = Application.builder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("engine", cmd_engine))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("translate", cmd_translate))
    app.add_handler(CommandHandler("srt", cmd_srt))

    # URL message handler (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))

    return app
