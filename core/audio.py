#complete audio.py for Whisper transcription and gTTS

from transformers import pipeline
from gtts import gTTS
from .agent import detect_language
import os, tempfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB    = 25
MAX_DURATION_SEC    = 120
MIN_FILE_SIZE_BYTES = 500
SUPPORTED_FORMATS   = {".ogg", ".mp3", ".mp4", ".wav", ".m4a", ".mpeg", ".mpga", ".webm"}

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # module level

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """
    Transcribe audio using Groq's Whisper API.
    Returns (transcript_text, detected_language_code).
    """
    with open(audio_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",  # fast + accurate + multilingual
            file=audio_file,
            response_format="json"
        )
    
    transcript = transcription.text.strip()
    language = detect_language(transcript)
    return transcript, language



def text_to_audio(text: str, lang_code: str, output_path: str | None = None):

    """
    Convert text to an MP3 file using gTTS.
    Returns path to the generated audio file.
    lang_code: 'hi' for Hindi, 'en' for English
    """

    if lang_code not in ['hi', 'en']:
        lang_code = 'hi'  # Default to Hindi if unsupported language code

    tts = gTTS(text=text, lang=lang_code, slow=False)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    tmp.close()
    return tmp.name




#---------------------------------------------------------------------
def validate_audio(audio_path: str, max_duration_seconds: int = MAX_DURATION_SEC) -> tuple[bool, str]:
    """Validate audio file before sending to Groq. Returns (is_valid, error_message)."""

    # File exists?
    if not audio_path or not os.path.exists(audio_path):
        return False, "Audio file not found"

    # Supported format?
    ext = Path(audio_path).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        return False, f"Unsupported format '{ext}'"

    # Not empty or corrupt?
    size_bytes = os.path.getsize(audio_path)
    if size_bytes < MIN_FILE_SIZE_BYTES:
        return False, "Audio file is empty or corrupt"

    # Under 25MB?
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"Voice note too large ({size_mb:.1f}MB). Max is {MAX_FILE_SIZE_MB}MB"

    # Duration check
    duration, error = _get_duration(audio_path, ext)
    if not error:
        if duration < 0.5:
            return False, "Voice note too short. Please speak a bit longer."
        if duration > max_duration_seconds:
            return False, f"Voice note too long ({duration:.0f}s). Max is {max_duration_seconds}s."

    logger.info(f"Audio valid | {ext} | {size_mb:.2f}MB | {duration:.1f}s")
    return True, ""


def _get_duration(audio_path: str, ext: str) -> tuple[float, str]:
    """Get audio duration in seconds using pydub."""
    try:
        from pydub import AudioSegment
        fmt_map = {
            ".ogg": "ogg", ".mp3": "mp3", ".mp4": "mp4",
            ".wav": "wav", ".m4a": "mp4", ".mpeg": "mp3",
            ".mpga": "mp3", ".webm": "webm"
        }
        audio = AudioSegment.from_file(audio_path, format=fmt_map.get(ext, ext.lstrip(".")))
        return len(audio) / 1000.0, ""
    except Exception as e:
        return 0.0, str(e)


def cleanup_audio_files(*paths: str) -> None:
    """Delete one or more temp files silently. Never raises."""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception as e:
            logger.warning(f"Could not delete {path}: {e}")


def get_audio_error_message(error: str, lang_code: str = "hi") -> str:
    """Return farmer-friendly error message in Hindi or English."""
    e = error.lower()
    if lang_code == "hi":
        if "not found"  in e: return "Voice note नहीं मिला। दोबारा भेजें। 🙏"
        if "large"      in e: return "Voice note बहुत बड़ा है। छोटा भेजें।"
        if "long"       in e: return "Voice note बहुत लंबा है। 2 मिनट से कम भेजें।"
        if "short"      in e: return "Voice note बहुत छोटा है। थोड़ा लंबा बोलें।"
        if "corrupt"    in e: return "Voice note खराब है। दोबारा record करें।"
        if "unsupported" in e: return "यह format supported नहीं है।"
        return "Voice note process नहीं हो सका। दोबारा भेजें। 🙏"
    else:
        if "not found"  in e: return "Voice note not received. Please send again. 🙏"
        if "large"      in e: return "Voice note too large. Send a shorter one."
        if "long"       in e: return "Voice note too long. Keep it under 2 minutes."
        if "short"      in e: return "Voice note too short. Please speak longer."
        if "corrupt"    in e: return "Voice note corrupted. Please record again."
        if "unsupported" in e: return "This audio format is not supported."
        return "Could not process voice note. Please try again. 🙏"