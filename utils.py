import os
import io
import pytesseract
from PIL import Image
from datetime import datetime
from pytz import timezone

from telegram import Message
from faster_whisper import WhisperModel

# --- Global model cache ---
whisper_model = None

# --- Config ---
VERSION = "1.0.1"

# --- Bhutan time greeting ---
def get_dynamic_greeting():
    bt_time = datetime.now(timezone("Asia/Thimphu")).time()
    if bt_time.hour < 12:
        return "Good Morning ☀️"
    elif bt_time.hour < 18:
        return "Good Afternoon ⛅"
    else:
        return "Good Evening 🌇"

# --- Bot info ---
def get_bot_info():
    now = datetime.now(timezone("Asia/Thimphu"))
    return VERSION, now.strftime("%Y-%m-%d %I:%M %p")

# --- ENV config ---
def load_config():
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_ids = os.getenv("ADMIN_CHAT_IDS", "").split(",")
    routes_raw = os.getenv("ROUTES_MAP", "").split(",")
    return bot_token, routes_raw, admin_ids, routes_raw

# --- OCR Image to Text ---
async def extract_text_from_image(message: Message) -> str:
    photo = message.photo[-1]
    file = await photo.get_file()
    f = io.BytesIO()
    await file.download(out=f)
    img = Image.open(f)
    return pytesseract.image_to_string(img)

# --- Transcribe Audio/Voice/Video using faster-whisper ---
async def transcribe_audio(bot, message: Message) -> str:
    global whisper_model
    file = await message.effective_attachment.get_file()
    f = io.BytesIO()
    await file.download(out=f)

    # Save to temp .mp3 file
    input_path = "/tmp/audio_input.mp3"
    with open(input_path, "wb") as out_file:
        out_file.write(f.getbuffer())

    # Lazy load tiny model
    if whisper_model is None:
        whisper_model = WhisperModel("tiny", compute_type="int8", device="cpu")

    segments, _ = whisper_model.transcribe(input_path)
    return " ".join([seg.text for seg in segments])
