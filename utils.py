import os
import io
import logging
import pytesseract
from PIL import Image
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

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
