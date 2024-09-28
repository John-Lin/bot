from __future__ import annotations

import os

from loguru import logger
from telegram import Update
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import filters

from .summary import summarize
from .translate import translate
from .utils import load_document
from .utils import parse_url


def get_full_message_text(update: Update) -> str:
    """
    Extract the full text of the message and the text of the reply-to message, if any.

    Args:
        update (Update): The update object containing the message.

    Returns:
        str: The combined message text and reply text, if available.
    """
    message = update.message
    if not message:
        return ""

    message_text = message.text or ""
    reply_text = message.reply_to_message.text if message.reply_to_message and message.reply_to_message.text else ""

    return f"{message_text}\n{reply_text}" if reply_text else message_text


class Bot:
    def __init__(self, token: str, whitelist: list[int]) -> None:
        """
        Initialize the bot with a token and a whitelist of chat IDs.
        """
        self.whitelist = whitelist
        logger.info("whitelist: {}", self.whitelist)

        # Create the application and add the command handler
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CommandHandler("sum", self.summarize_url, filters=filters.Chat(self.whitelist)))
        self.app.add_handler(CommandHandler("jp", self.translate_jp, filters=filters.Chat(self.whitelist)))
        self.app.add_handler(CommandHandler("chat_id", self.show_chat_id))
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    @classmethod
    def from_env(cls) -> Bot:
        """
        Create a Bot instance using environment variables for the token and whitelist.
        """
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN is not set")

        whitelist = os.getenv("BOT_WHITELIST")
        if not whitelist:
            raise ValueError("BOT_WHITELIST is not set")

        return cls(token=token, whitelist=[int(chat_id) for chat_id in whitelist.replace(" ", "").split(",")])

    # show chat_id
    async def show_chat_id(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show the chat ID of the current chat.
        """
        if not update.message:
            return

        await update.message.reply_text(f"Chat ID: {update.message.chat_id}")

    async def summarize_url(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Summarize the URL found in the message text and reply with the summary.
        """

        logger.info(update)

        if not update.message or not update.message.text:
            return

        raw_text = get_full_message_text(update)

        url = parse_url(raw_text)
        if not url:
            logger.info("No URL found in message")
            return

        logger.info("Found URL: {}", url)

        # TODO: Handle the type of URL here, reply with a message if it cannot be processed
        text = load_document(url)
        if not text:
            logger.info("Failed to load URL")
            await update.message.reply_text("Failed to load URL")
            return

        summarized = summarize(text)
        logger.info("Replying to chat ID: {} with: {}", update.message.chat_id, summarized)

        await update.message.reply_text(summarized)

    async def translate_jp(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(update)

        if not update.message or not update.message.text:
            return

        raw_text = get_full_message_text(update)

        translated = translate(raw_text, lang="日文")
        logger.info("Replying to chat ID: {} with: {}", update.message.chat_id, translated)

        await update.message.reply_text(translated)
