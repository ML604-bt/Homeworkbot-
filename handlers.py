import logging
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
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
        # ✅ Handle plain text messages
        if message.text:
            text = message.text

        # Handle images/photos (OCR)
        elif message.photo:
            photo = await message.photo[-1].get_file()
            file_bytes = await photo.download_as_bytearray()
            text = extract_text_from_image(file_bytes)

        # Handle voice/audio/video (Transcription)
        elif message.voice or message.audio or message.video:
            file = await (message.voice or message.audio or message.video).get_file()
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                await file.download_to_drive(custom_path=tf.name)
                text = await transcribe_audio(tf.name)
                os.unlink(tf.name)  # Clean up

        # Check and forward if it's homework
        if text and is_homework_text(text):
            await message.copy(chat_id=target_chat_id)
            logger.info(f"✅ Forwarded homework from {source_chat_id} to {target_chat_id}")
        else:
            logger.info(f"❌ Ignored — No homework detected from {source_chat_id}")

    except Exception as e:
        logger.warning(f"⚠️ Error processing message: {e}")

# Export handler for main.py
handle_homework = MessageHandler(
    filters.TEXT | filters.PHOTO | filters.VOICE | filters.AUDIO | filters.VIDEO, handle_homework
          )
