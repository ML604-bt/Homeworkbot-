from telegram import Update
from telegram.ext import ContextTypes
import os
import tempfile
import logging
from utils import extract_text_from_image, transcribe_audio, is_homework_text

logger = logging.getLogger(__name__)

async def handle_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    source_chat_id = update.effective_chat.id
    routes_map = context.bot_data.get("ROUTES_MAP", {})
    target_chat_id = routes_map.get(source_chat_id)

    if not target_chat_id:
        logger.info(f"No route defined for chat {source_chat_id}")
        return

    message = update.effective_message
    text = ""

    try:
        # TEXT
        if message.text:
            text = message.text

        # PHOTOS
        elif message.photo:
            photo = await message.photo[-1].get_file()
            file_bytes = await photo.download_as_bytearray()
            text = extract_text_from_image(file_bytes)

        # VOICE, AUDIO, VIDEO
        elif message.voice or message.audio or message.video:
            file = await (message.voice or message.audio or message.video).get_file()
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                await file.download_to_drive(custom_path=tf.name)
                text = await transcribe_audio(tf.name)
                os.unlink(tf.name)

        # DECISION
        if text and is_homework_text(text):
            await message.copy(chat_id=target_chat_id)
            logger.info(f"✅ Forwarded homework from {source_chat_id} to {target_chat_id}")
        else:
            logger.info(f"⚠️ Ignored — not homework: {text}")

    except Exception as e:
        logger.warning(f"Error in handle_homework: {e}")
