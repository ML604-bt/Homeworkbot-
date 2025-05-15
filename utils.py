import os
import io
import logging
import pytesseract
from PIL import Image
from faster_whisper import WhisperModel
from datetime import datetime
import pytz
import tempfile
import moviepy.editor as mp
from telegram import File

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy-load the Whisper model
model = None
def load_model():
    global model
    if model is None:
        model = WhisperModel("tiny", compute_type="int8")

def get_bot_info():
    bot_version = "1.0.0"
    bhutan_time = datetime.now(pytz.timezone("Asia/Thimphu")).strftime("%Y-%m-%d %I:%M %p")
    return bot_version, bhutan_time

def load_config():
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    admin_chat_ids = os.getenv("ADMIN_CHAT_IDS", "").split(",")
    routes_map = os.getenv("ROUTES_MAP", "").split(",")
    return bot_token, chat_id, admin_chat_ids, routes_map

# Dynamic greeting for Bhutan timezone
def get_dynamic_greeting():
    bhutan_tz = pytz.timezone("Asia/Thimphu")
    hour = datetime.now(BT).hour
    formatted_time = hour.strftime("%I:%M %p")

    if 0 <= hour < 12:
        return f"Good Morning 🌅 - {formatted_time} (BTT)"
    elif 12 <= hour < 16:
        return f"Good Afternoon 🌞 - {formatted_time} (BTT)"
    elif 16 <= hour < 19:
        return f"Good Evening 🌇 - {formatted_time} (BTT)"
    else:
        return f"Good Night 🌙 - {formatted_time} (BTT)"

# OCR for image-based homework
def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

# Audio/voice transcription using Whisper
def transcribe_audio(audio_path: str) -> str:
    try:
        load_model()
        segments, _ = model.transcribe(audio_path, beam_size=5)
        return " ".join(segment.text for segment in segments)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""

# Download Telegram File
async def download_media_file(file: File, suffix=".mp3") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        await file.download_to_drive(tmp_file.name)
        return tmp_file.name

# Extract audio from video (MP4/AVI etc.)
def extract_audio_from_video(video_path: str) -> str:
    try:
        video = mp.VideoFileClip(video_path)
        audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
        video.audio.write_audiofile(audio_path)
        return audio_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        return ""

# Detect homework-like text
def is_homework_text(text: str) -> bool:
    keywords = [
        "homework",
        "hw",
        "assignment",
        "classwork",
        "project",
        "math",
        "science"
    ]
    return any(keyword in text.lower() for keyword in keywords)





   

