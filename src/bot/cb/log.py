from __future__ import annotations

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes


async def log(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Message Update: {}", update)
