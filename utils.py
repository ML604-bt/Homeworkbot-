import os
import io
import logging
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from faster_whisper import WhisperModel
from datetime import datetime
import pytz
import tempfile
import moviepy.editor as mp
from telegram import File

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Whisper model once
model = None
def load_model():
    global model
    if model is None:
        model = WhisperModel("tiny", compute_type="int8")

def get_bot_info():
    bot_version = "1.0.1"
    bhutan_time = datetime.now(pytz.timezone("Asia/Thimphu")).strftime("%Y-%m-%d %I:%M %p")
    return bot_version, bhutan_time

def load_config():
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    admin_chat_ids = os.getenv("ADMIN_CHAT_IDS", "").split(",")
    routes_map = os.getenv("ROUTES_MAP", "").split(",")
    return bot_token, chat_id, admin_chat_ids, routes_map

def get_dynamic_greeting():
    BT = pytz.timezone("Asia/Thimphu")
    now = datetime.now(BT)
    hour = now.hour
    formatted = now.strftime("%I:%M %p")
    if 0 <= hour < 12: return f"Good Morning 🌅 - {formatted} (BTT)"
    elif 12 <= hour < 16: return f"Good Afternoon 🌞 - {formatted} (BTT)"
    elif 16 <= hour < 19: return f"Good Evening 🌇 - {formatted} (BTT)"
    else: return f"Good Night 🌙 - {formatted} (BTT)"

# --- OCR ---
def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        image = ImageOps.autocontrast(image)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        image = image.point(lambda x: 0 if x < 140 else 255, mode='1')

        if image.width < 800:
            ratio = 800 / float(image.width)
            height = int((float(image.height) * float(ratio)))
            image = image.resize((800, height), Image.Resampling.LANCZOS)

        text = pytesseract.image_to_string(image)
        logger.info(f"OCR extracted: {text.strip()}")
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

# --- Audio Transcription ---
def transcribe_audio(audio_path: str) -> str:
    try:
        load_model()
        segments, _ = model.transcribe(audio_path, beam_size=5)
        full_text = " ".join(segment.text for segment in segments)
        logger.info(f"Whisper transcription: {full_text}")
        return full_text
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""

async def download_media_file(file: File, suffix=".mp3") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        await file.download_to_drive(tmp_file.name)
        return tmp_file.name

def extract_audio_from_video(video_path: str) -> str:
    try:
        video = mp.VideoFileClip(video_path)
        audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
        video.audio.write_audiofile(audio_path)
        return audio_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        return ""

def is_homework_text(text: str) -> bool:
    keywords = ["homework", "hw", "assignment", "classwork", "project", "math", "science"]
    return any(k in text.lower() for k in keywords)
