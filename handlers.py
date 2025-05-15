import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils import extract_text_from_image, transcribe_audio

logger = logging.getLogger(__name__)

async def handle_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    src_id = message.chat_id
    routes = context.bot_data.get("ROUTES_MAP", {})
    dst_id = routes.get(src_id)

    if not dst_id:
        logger.info(f"Ignoring message from untracked chat: {src_id}")
        return

    forwarded_logs = context.bot_data.setdefault("FORWARDED_LOGS", [])

    try:
        if message.text:
            await context.bot.forward_message(dst_id, src_id, message.message_id)
            forwarded_logs.append((src_id, dst_id, "text"))
        elif message.photo:
            await context.bot.forward_message(dst_id, src_id, message.message_id)
            extracted = await extract_text_from_image(message)
            if extracted.strip():
                await context.bot.send_message(dst_id, f"(OCR):\n{extracted.strip()}")
            forwarded_logs.append((src_id, dst_id, "photo"))
        elif message.audio or message.voice:
            transcript = await transcribe_audio(context.bot, message)
            await context.bot.forward_message(dst_id, src_id, message.message_id)
            if transcript.strip():
                await context.bot.send_message(dst_id, f"(Transcript):\n{transcript.strip()}")
            forwarded_logs.append((src_id, dst_id, "audio/voice"))
        elif message.video:
            await context.bot.forward_message(dst_id, src_id, message.message_id)
            forwarded_logs.append((src_id, dst_id, "video"))
        else:
            logger.info(f"Unsupported format from {src_id}")
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")

def is_homework_text(text: str) -> bool:
    if not text:
        return False
    keywords = ["homework", "hw", "assignment", "classwork", "project", "math", "science"]
    return any(keyword in text.lower() for keyword in keywords)
