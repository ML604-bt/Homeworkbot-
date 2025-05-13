import os
import io
import logging
import pytesseract
from PIL import Image
from faster_whisper import WhisperModel
import time
from datetime import datetime
from pytz import timezone
import pytz

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot info from environment variables
def get_bot_info():
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    admin_chat_ids = os.getenv("ADMIN_CHAT_IDS").split(",")
    routes_map = os.getenv("ROUTES_MAP").split(",")
    
    return bot_token, chat_id, admin_chat_ids, routes_map

# Function to get the dynamic greeting based on time
def get_dynamic_greeting():
    bhutan_tz = pytz.timezone("Asia/Thimphu")
    current_time = datetime.now(bhutan_tz)
    hour = current_time.hour
    formatted_time = current_time.strftime("%I:%M %p")  # 12-hour format with AM/PM

    if 0 <= hour < 12:
        return f"Good Morning 🌅 - {formatted_time} (BTT)"
    elif 12 <= hour < 18:
        return f"Good Afternoon 🌞 - {formatted_time} (BTT)"
    elif 18 <= hour < 22:
        return f"Good Evening 🌇 - {formatted_time} (BTT)"
    else:
        return f"Good Night 🌙 - {formatted_time} (BTT)"

# Function to create a log of messages
def log_message(message, message_type="text"):
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Message logged at {timestamp}: {message[:50]}... ({message_type})")  # Only show first 50 chars
    except Exception as e:
        logger.error(f"Error logging message: {e}")

# Lazy-loaded transcriber
transcriber_model = None

def warmup_transcriber():
    global transcriber_model
    if transcriber_model is None:
        logger.info("Loading Faster-Whisper model...")
        transcriber_model = WhisperModel("tiny", compute_type="int8")

def get_bot_info():
    """
    Returns bot version and time.
    """
    bot_version = "1.0.0"  # This should be your actual version or dynamic retrieval
    bt_time = datetime.now(pytz.timezone("Asia/Thimphu")).strftime("%Y-%m-%d %H:%M:%S")
    return bot_version, bt_time
    
async def transcribe_audio(file_path: str) -> str:
    warmup_transcriber()
    segments, _ = transcriber_model.transcribe(file_path)
    return " ".join([segment.text for segment in segments])

def extract_text_from_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)

def is_homework_text(text: str) -> bool:
    keywords = ["homework", "hw", "assignment", "classwork"]
    return any(keyword.lower() in text.lower() for keyword in keywords)
