from telegram import Update
from telegram.ext import ContextTypes
import os
import tempfile
import logging
from utils import extract_text_from_image, transcribe_audio, is_homework_text

logger = logging.getLogger(__name__)

async def handle_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📩 New message received.")
    if update.effective_chat is None:
        return

    source_chat_id = update.effective_chat.id
    routes_map = context.bot_data.get("ROUTES_MAP", {})
    target_chat_id = routes_map.get(source_chat_id)

    if not target_chat_id:
        logger.warning(f"❌ No route set for {source_chat_id}")
        return

    message = update.effective_message
    text = ""

    try:
        # TEXT Message
        if message.text:
            text = message.text
            logger.info(f"📝 Text received: {text}")

        # PHOTO Message
        elif message.photo:
            photo = await message.photo[-1].get_file()
            file_bytes = await photo.download_as_bytearray()
            text = extract_text_from_image(file_bytes)

        # VOICE / AUDIO / VIDEO Message
        elif message.voice or message.audio or message.video:
            file = await (message.voice or message.audio or message.video).get_file()
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                await file.download_to_drive(custom_path=tf.name)
                text = await transcribe_audio(tf.name)
                os.unlink(tf.name)

        # Decision Point
        if text and is_homework_text(text):
            await message.copy(chat_id=target_chat_id)
            logger.info(f"✅ Forwarded to {target_chat_id}")
        else:
            logger.info(f"⚠️ Skipped — not homework: {text}")

    except Exception as e:
        logger.error(f"🔥 Error during message handling: {e}")

def is_homework_text(text: str) -> bool:
    if not text:
        return False
    keywords = ["homework", "hw", "assignment", "classwork", "project", "math", "science"]
    return any(keyword in text.lower() for keyword in keywords)
