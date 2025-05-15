from telegram import Update
from telegram.ext import ContextTypes
import os
import tempfile
import logging
from utils import extract_text_from_image, transcribe_audio, is_homework_text

logger = logging.getLogger(__name__)

async def handle_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        routes = context.bot_data.get("ROUTES_MAP", {})
        forward_to = routes.get(chat_id)

        if not forward_to:
            logger.warning(f"No route found for chat {chat_id}. Message ignored.")
            return

        logger.info(f"Forwarding message from {chat_id} to {forward_to}...")

        if update.message:
            await context.bot.forward_message(forward_to, chat_id, update.message.message_id)
        else:
            logger.warning("No message content detected in update.")

    except Exception as e:
        logger.error(f"Error in handle_homework: {e}")

def is_homework_text(text: str) -> bool:
    if not text:
        return False
    keywords = ["homework", "hw", "assignment", "classwork", "project", "math", "science"]
    return any(keyword in text.lower() for keyword in keywords)
