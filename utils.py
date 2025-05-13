import os
import io
import logging
import pytesseract
from PIL import Image
from faster_whisper import WhisperModel
import time
from datetime import datetime
import pytz
from pytz import timezone
import tempfile
import logging
import moviepy.editor as mp
import numpy as np
import torch
from telegram import Message, File

# Lazy load the tiny model
model = None
def load_model():
    global model
    if model is None:
        model = WhisperModel("tiny", compute_type="int8")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# OCR logic
def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        logging.error(f"OCR failed: {e}")
        return ""

# Audio transcription logic
def transcribe_audio(audio_path: str) -> str:
    try:
        load_model()
        segments, _ = model.transcribe(audio_path, beam_size=5)
        return " ".join(segment.text for segment in segments)
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return ""

# Voice/audio/video download
async def download_media_file(file: File, suffix=".mp3") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        await file.download_to_drive(tmp_file.name)
        return tmp_file.name

# Extract audio from video
def extract_audio_from_video(video_path: str) -> str:
    try:
        video = mp.VideoFileClip(video_path)
        audio_path = video_path.rsplit(".", 1)[0] + ".mp3"
        video.audio.write_audiofile(audio_path)
        return audio_path
    except Exception as e:
        logging.error(f"Failed to extract audio: {e}")
        return ""

# Basic homework detection logic
def is_homework_text(text: str) -> bool:
    keywords = ["homework", "hw", "work", "assignment", "project", "math", "science", "english"]
    text = text.lower()
    return any(word in text for word in keywords)

# Get bot info from environment variables
def get_bot_info():
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    admin_chat_ids = os.getenv("ADMIN_CHAT_IDS").split(",")
    routes_map = os.getenv("ROUTES_MAP").split(",")
    
    return bot_token, chat_id, admin_chat_ids, routes_map

# Function to perform OCR (optional to update if Tesseract or another is used)
def ocr_image(image):
    try:
        # Here you would use Tesseract or any other OCR library you're using
        # For now, this is a placeholder.
        text = "Extracted text from image"
        return text
    except Exception as e:
        logger.error(f"Error in OCR: {e}")
        return None

# Function to transcribe audio/video to text using Faster Whisper
def transcribe_audio_or_video(audio_file_path):
    model = WhisperModel('tiny', device='cpu', compute_type='int8')  # Adjust based on your model
    result = model.transcribe(audio_file_path)
    
    # Return the transcribed text
    return result["text"]

# Function to handle homework based on type (image, audio, voice, video)
def handle_homework(file, file_type):
    # Check file type and perform relevant action
    if file_type == "image":
        text = ocr_image(file)
        return text
    elif file_type == "audio" or file_type == "video":
        transcribed_text = transcribe_audio_or_video(file)
        return transcribed_text
    else:
        return None

# Function to create a log of messages
def log_message(message, message_type="text"):
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Message logged at {timestamp}: {message[:50]}... ({message_type})")  # Only show first 50 chars
    except Exception as e:
        logger.error(f"Error logging message: {e}")

def is_homework_text(text: str) -> bool:
    keywords = ["homework", "hw", "assignment", "classwork"]
    return any(keyword.lower() in text.lower() for keyword in keywords)
