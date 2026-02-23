"""
Cloud Run entrypoint for Open-Scribe Cloud
FastAPI server handling Telegram webhook
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

# Add project root to path for src/ imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, Request, Response
from telegram import Update

from bot.telegram_bot import create_bot_application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global bot application
_bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and cleanup bot"""
    global _bot_app

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        yield
        return

    logger.info("Initializing Telegram bot...")
    _bot_app = create_bot_application(token)

    # Initialize the application (but don't start polling)
    await _bot_app.initialize()
    await _bot_app.start()

    logger.info("Bot initialized successfully")
    yield

    # Cleanup
    logger.info("Shutting down bot...")
    if _bot_app:
        await _bot_app.stop()
        await _bot_app.shutdown()


app = FastAPI(title="Open-Scribe Cloud", lifespan=lifespan)


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "open-scribe-cloud"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram webhook updates"""
    if not _bot_app:
        return Response(status_code=503, content="Bot not initialized")

    try:
        data = await request.json()
        update = Update.de_json(data, _bot_app.bot)
        await _bot_app.process_update(update)
        return Response(status_code=200)
    except Exception:
        logger.exception("Error processing webhook update")
        return Response(
            status_code=200
        )  # Always return 200 to prevent Telegram retries


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "bot.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
