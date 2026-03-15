
import os
import logging
import tempfile
import httpx
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)

# Global model variable for lazy loading
_whisper_model = None

def load_model():
    """Lazily loads the faster-whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper model (base)...")
            # Using CPU, int8 for memory efficiency as requested
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("faster-whisper model loaded ✓")
        except Exception as e:
            logger.error(f"Failed to load faster-whisper: {e}")
    return _whisper_model

def transcribe_audio(file_path: str) -> str:
    """Transcribes a local audio file."""
    model = load_model()
    if not model:
        # Fallback to OpenAI if configured
        return _transcribe_openai_fallback(file_path)
        
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return _transcribe_openai_fallback(file_path)

async def transcribe_from_url(audio_url: str) -> str:
    """Downloads audio from a URL and transcribes it."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(audio_url)
            resp.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
                
            try:
                return transcribe_audio(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
    except Exception as e:
        logger.error(f"Failed to download/transcribe from URL: {e}")
        return "Audio transcription failed."

def transcribe_from_bytes(audio_bytes: bytes, file_extension: str = ".ogg") -> str:
    """Transcribes audio from raw bytes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
        
    try:
        return transcribe_audio(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def _transcribe_openai_fallback(file_path: str) -> str:
    """Uses OpenAI Whisper API as a fallback."""
    if not settings.OPENAI_API_KEY:
        logger.error("OpenAI Fallback requested but OPENAI_API_KEY is missing.")
        return "Transcription unavailable (no local model, no API key)."
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        logger.error(f"OpenAI fallback failed: {e}")
        return "Transcription service error."
