"""
Thredion Engine — Video Transcriber Service
Dual-mode transcription:
- SHORT videos (<5 min): Local faster-whisper (free, instant)
- LONG videos (>5 min): Queue for async Groq processing (free, background)
"""

import asyncio
import logging
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import yt_dlp
from faster_whisper import WhisperModel
from pydub import AudioSegment

from core.config import settings

logger = logging.getLogger(__name__)

# ── Global Whisper Model Cache ─────────────────────────────
_whisper_model: Optional[WhisperModel] = None
_model_lock = asyncio.Lock()


async def load_whisper_model() -> WhisperModel:
    """
    Lazy-load faster-whisper model (optimized for CPU).
    Uses locking to prevent multiple concurrent loads.
    Model: base (74M parameters, fast on CPU with int8 quantization)
    """
    global _whisper_model
    
    if _whisper_model is not None:
        return _whisper_model
    
    async with _model_lock:
        if _whisper_model is not None:
            return _whisper_model
        
        logger.info("Loading faster-whisper model (base)...")
        try:
            _whisper_model = WhisperModel(
                model_size_or_path=settings.WHISPER_MODEL_SIZE,
                device="cpu",
                compute_type="int8",  # 8-bit quantization for low RAM
                num_workers=1,
                cpu_threads=2
            )
            logger.info("✅ Whisper model loaded successfully")
            return _whisper_model
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise


def detect_platform(url: str) -> str:
    """Detect video platform from URL."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    elif "tiktok.com" in url_lower or "vm.tiktok.com" in url_lower:
        return "tiktok"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "reddit.com" in url_lower:
        return "reddit"
    else:
        return "unknown"


async def get_video_metadata(url: str) -> Dict[str, Any]:
    """
    Extract video metadata (duration, title, thumbnail, description).
    Non-blocking: uses thread executor to avoid blocking event loop.
    """
    logger.info(f"[METADATA] Extracting from {url}")
    
    def _extract():
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'duration_seconds': int(info.get('duration', 0)),
                    'title': info.get('title', 'Unknown')[:200],
                    'platform': detect_platform(url),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')[:500],
                    'uploader': info.get('uploader', '')[:100],
                    'view_count': info.get('view_count', 0),
                    'success': True,
                }
        except Exception as e:
            logger.warning(f"[METADATA] Extraction failed: {e}")
            # Return conservative estimate for unknown videos
            return {
                'duration_seconds': 600,  # Assume 10 min
                'title': 'Unknown',
                'platform': detect_platform(url),
                'description': '',
                'uploader': '',
                'view_count': 0,
                'success': False,
                'error': str(e),
            }
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract)


async def transcribe_short_video(url: str) -> str:
    """
    LOCAL TRANSCRIPTION: faster-whisper (synchronous, free, instant).
    For videos <5 minutes.
    """
    logger.info(f"[SHORT] Transcribing locally: {url}")
    
    def _transcribe():
        try:
            # Get ffmpeg path from environment or use default
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
            
            # Download audio only (no video)
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': ffmpeg_path,
                'quiet': True,
                'no_warnings': True,
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_file = ydl.prepare_filename(info)
            
            logger.info(f"[SHORT] Audio downloaded: {audio_file}")
            
            # Load model
            model = asyncio.run(load_whisper_model())
            
            # Transcribe
            logger.info(f"[SHORT] Starting transcription...")
            segments, _ = model.transcribe(
                audio_file,
                language="en",
                beam_size=5,
            )
            
            # Collect transcript
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())
            
            transcript = " ".join(transcript_parts)
            
            logger.info(f"[SHORT] ✅ Completed: {len(transcript)} chars")
            
            # Cleanup
            try:
                os.remove(audio_file)
            except:
                pass
            
            return transcript
        
        except Exception as e:
            logger.error(f"[SHORT] Local transcription failed: {e}")
            raise
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe)


async def queue_long_video_job(
    url: str,
    user_phone: str,
    db_session,
) -> str:
    """
    ASYNC TRANSCRIPTION: Queue job for background worker.
    For videos >5 minutes.
    Returns job_id for tracking.
    """
    from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy
    
    logger.info(f"[LONG] Queueing async job: {url}")
    
    job_id = str(uuid.uuid4())
    
    try:
        # Check if Azure Queue is configured
        if not settings.AZURE_QUEUE_CONNECTION_STRING:
            logger.warning("[LONG] Azure Queue not configured, cannot queue job")
            return job_id
        
        queue_client = QueueClient.from_connection_string(
            settings.AZURE_QUEUE_CONNECTION_STRING,
            settings.AZURE_QUEUE_NAME
        )
        
        # Create message
        message_data = {
            'job_id': job_id,
            'url': url,
            'user_phone': user_phone,
            'type': 'video_transcription',
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Send to queue
        queue_client.send_message(json.dumps(message_data))
        logger.info(f"[LONG] ✅ Job queued: {job_id}")
        
        return job_id
    
    except Exception as e:
        logger.error(f"[LONG] ❌ Queue failed: {e}")
        raise


async def process_video(
    url: str,
    user_phone: str,
    db_session,
) -> Dict[str, Any]:
    """
    MAIN ROUTER: Detect video length → route to local OR async.
    Returns metadata about processing decision.
    """
    logger.info(f"[ROUTER] Processing video: {url}")
    
    # Step 1: Get metadata (includes duration)
    metadata = await get_video_metadata(url)
    duration = metadata.get('duration_seconds', 600)
    
    logger.info(f"[ROUTER] Duration: {duration}s ({duration//60}m)")
    
    # Step 2: Route based on duration
    if duration <= settings.SHORT_VIDEO_MAX_DURATION:
        # SHORT: Use local faster-whisper
        logger.info(f"[ROUTER] SHORT video ({duration}s): using local transcription")
        
        try:
            transcript = await transcribe_short_video(url)
            
            return {
                'status': 'completed',
                'job_id': None,
                'transcript': transcript,
                'transcript_length': len(transcript),
                'transcript_source': 'local',
                'duration': duration,
                'metadata': metadata,
                'message': '✅ Transcription complete!',
            }
        except Exception as e:
            logger.error(f"[ROUTER] Local transcription failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'transcript_source': 'failed',
                'duration': duration,
                'metadata': metadata,
            }
    
    else:
        # LONG: Queue for async processing
        logger.info(f"[ROUTER] LONG video ({duration}s): queueing for async")
        
        try:
            job_id = await queue_long_video_job(url, user_phone, db_session)
            
            return {
                'status': 'processing',
                'job_id': job_id,
                'transcript_source': 'async_queued',
                'duration': duration,
                'metadata': metadata,
                'message': f'🔄 Long video detected! Transcription in progress (Job: {job_id[:8]}...). You\'ll get an update on your dashboard!',
            }
        except Exception as e:
            logger.error(f"[ROUTER] Queue failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'transcript_source': 'failed',
                'duration': duration,
                'metadata': metadata,
            }


# Utility: Clean up old audio files
async def cleanup_temp_audio():
    """Periodically clean up downloaded audio files from /tmp."""
    import glob
    try:
        for f in glob.glob('/tmp/*.wav'):
            try:
                os.remove(f)
                logger.info(f"Cleaned up: {f}")
            except:
                pass
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
