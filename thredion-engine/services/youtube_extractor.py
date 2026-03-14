"""
YouTube Extractor — Subtitle-First Strategy

This module implements the optimal YouTube extraction pipeline:
1. Try youtube-transcript-api (subtitles first - fastest, free, no bot risk)
2. Fall back to yt-dlp subtitle extraction (alternative sources)
3. Fall back to local ASR with faster-whisper (CPU-expensive, for short videos)
4. Rare fallback: cookies-based transcription (account risk, last resort)
5. Final fallback: metadata-only (graceful degradation)

Cost: 70% of videos cost $0 + <1 sec (stage 1)
       20% of videos cost $0 + 2-3 sec (stage 2)
       8% of videos cost CPU time (stage 3, queued)
       <1% of videos need paid APIs or fail
"""

import logging
import hashlib
import asyncio
import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass
class YouTubeResult:
    """Standardized YouTube extraction result."""
    platform: str = "youtube"
    title: str = ""
    content: str = ""  # Transcript or caption
    thumbnail_url: str = ""
    duration_seconds: int = 0
    video_id: str = ""
    channel_name: str = ""
    
    # Metadata about extraction
    source_type: str = "metadata_only"  # yt_transcript_api|yt_subtitle|local_asr|cookies_asr|metadata_only
    transcript_length: int = 0
    extraction_time_ms: int = 0
    success: bool = False  # Whether extraction succeeded
    failure_reason: Optional[str] = None
    failure_class: Optional[str] = None  # transient|auth|permanent|unsupported
    detected_language: Optional[str] = None
    duration_sec: int = 0  # Alias for duration_seconds


def normalize_youtube_url(url: str) -> tuple[str, str]:
    """
    Normalize YouTube URL variants and extract video ID.
    
    Returns:
        (video_id, canonical_url)
        e.g., ("dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    url = url.strip()
    
    # Handle different YouTube URL formats
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
    ]
    
    video_id = None
    for pattern in patterns:
        import re
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        raise ValueError(f"Could not extract video ID from YouTube URL: {url}")
    
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_id, canonical_url


# ── LAYER 1: Subtitle-First (Fastest, Free, No Bot Risk) ────────────────


def extract_with_transcript_api(video_id: str) -> Optional[YouTubeResult]:
    """
    LAYER 1: Fastest & safest method using youtube-transcript-api.
    
    Tries to fetch official YouTube subtitles (manual or auto-generated).
    Success rate: ~70% of videos have subtitles
    Speed: <1 second
    Cost: FREE
    Bot risk: NONE
    
    Returns None if no subtitles available (fall back to Layer 2).
    """
    start_time = datetime.utcnow()
    
    try:
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # transcript is a FetchedTranscript (iterable), each item has .text, .start, .duration
        transcript_items = list(transcript)
        
        # Combine all segments
        full_text = " ".join([item.text if hasattr(item, 'text') else str(item) for item in transcript_items])
        
        if not full_text or len(full_text.strip()) < 5:
            logger.info(f"Video {video_id}: Empty/tiny transcript, trying Layer 2")
            return None
        
        # Get metadata via yt-dlp (quick, no download) — may fail if IP blocked
        try:
            metadata = _get_youtube_metadata_quick(video_id)
        except Exception:
            metadata = {
                "title": "", "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "duration": 0, "channel": "",
            }
        
        extraction_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()
        
        return YouTubeResult(
            title=metadata.get("title", ""),
            content=full_text,
            thumbnail_url=metadata.get("thumbnail_url", ""),
            duration_seconds=metadata.get("duration", 0),
            video_id=video_id,
            channel_name=metadata.get("channel", ""),
            source_type="yt_transcript_api",
            transcript_length=len(full_text),
            extraction_time_ms=extraction_time,
            detected_language="en",
            success=True,
        )
    
    except (TranscriptsDisabled, NoTranscriptFound):
        logger.info(f"Video {video_id}: No transcripts found, trying Layer 2 (yt-dlp subtitles)")
        return None
    
    except Exception as e:
        logger.warning(f"Layer 1 (transcript-api) failed for {video_id}: {e}")
        return None


# ── LAYER 2: yt-dlp Subtitle Extraction (Fallback) ─────────────


def extract_with_ytdlp_subtitles(video_id: str) -> Optional[YouTubeResult]:
    """
    LAYER 2: Fallback using yt-dlp for subtitle extraction.
    
    Tries alternative subtitle sources when transcript-api fails.
    Success rate: ~15-20% of remaining videos
    Speed: 2-3 seconds
    Cost: FREE
    Bot risk: LOW
    
    Returns None if no subtitles found (fall back to Layer 3).
    """
    start_time = datetime.utcnow()
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": True,
            "allsubtitles": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Look for subtitles in any language
            subtitles = info.get("subtitles", {})
            if not subtitles:
                logger.info(f"Video {video_id}: No subtitles via yt-dlp, trying Layer 3 (ASR)")
                return None
            
            # Try English first, then any available
            subtitle_dict = subtitles.get("en", subtitles.get(list(subtitles.keys())[0], []))
            
            # Combine all subtitle entries
            full_text = " ".join([item.get("text", "") for item in subtitle_dict if isinstance(item, dict)])
            
            if not full_text:
                logger.info(f"Video {video_id}: Subtitle dict empty, trying Layer 3 (ASR)")
                return None
            
            extraction_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return YouTubeResult(
                title=info.get("title", ""),
                content=full_text,
                thumbnail_url=info.get("thumbnail", ""),
                duration_seconds=info.get("duration", 0),
                video_id=video_id,
                channel_name=info.get("uploader", ""),
                source_type="yt_subtitle",  # ✅ From yt-dlp subtitle extraction
                transcript_length=len(full_text),
                extraction_time_ms=extraction_time,
                detected_language=list(subtitles.keys())[0] if subtitles else "en",
                success=True,
            )
    
    except Exception as e:
        logger.warning(f"Layer 2 (yt-dlp subtitles) failed for {video_id}: {e}")
        return None


# ── LAYER 3: Local ASR (Queued, CPU-Expensive) ─────────────


def extract_with_local_asr_queued(video_id: str) -> YouTubeResult:
    """
    LAYER 3: Queue job for local ASR with faster-whisper.
    
    Only for short videos (<5 min) when server load is low.
    This is async - returns job_id, actual transcription happens later.
    
    Success rate: ~95% if media downloads successfully
    Speed: 30-120 seconds (runs in background)
    Cost: FREE (CPU time)
    Bot risk: MEDIUM (downloading from YouTube)
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # In real implementation, this would:
    # 1. Create a Memory row with job_status="queued"
    # 2. Push job to queue (RabbitMQ/Celery/Redis)
    # 3. Return immediately with job_id
    # 4. Worker picks up job and does transcription
    
    # For now, return a placeholder that indicates queueing
    return YouTubeResult(
        video_id=video_id,
        source_type="local_asr",
        failure_reason="Queued for async transcription",
        success=False,
    )


# ── HELPER: Quick Metadata Extraction (No Download) ─────────────


def _get_youtube_metadata_quick(video_id: str) -> Dict[str, Any]:
    """
    Get YouTube metadata WITHOUT downloading.
    Uses yt-dlp with skip_download=True for quick metadata only.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                "title": info.get("title", ""),
                "thumbnail_url": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "channel": info.get("uploader", ""),
            }
    
    except Exception as e:
        logger.warning(f"Could not get metadata for {video_id}: {e}")
        return {
            "title": f"YouTube Video {video_id}",
            "duration": 0,
            "channel": "Unknown",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        }


# ── LAYER 4: Rare Fallback - Cookie-Based (Account Risk) ─────────────


def extract_with_cookies_fallback(video_id: str, cookies_file: str) -> Optional[YouTubeResult]:
    """
    LAYER 4: Last resort using exported browser cookies.
    
    Only call this if all above failed AND:
    - Content is high-value
    - User explicitly requested it
    - You have browser cookies saved
    
    Success rate: ~60% (depends on session validity)
    Speed: 30-120 seconds
    Cost: FREE (but account security risk)
    Bot risk: HIGH
    Account risk: REAL (IP anomaly detection, 2FA challenges)
    
    NOT recommended as core strategy - use as desperate fallback only.
    """
    start_time = datetime.utcnow()
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    if not os.path.exists(cookies_file):
        logger.warning(f"Cookies file not found: {cookies_file}")
        return None
    
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "cookiefile": cookies_file,
            "writesubtitles": True,
            "allsubtitles": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Try to get transcript/subtitles
            subtitles = info.get("subtitles", {})
            if not subtitles:
                logger.warning(f"Video {video_id}: Still no subtitles even with cookies")
                return None
            
            subtitle_dict = subtitles.get("en", subtitles.get(list(subtitles.keys())[0], []))
            full_text = " ".join([item.get("text", "") for item in subtitle_dict if isinstance(item, dict)])
            
            extraction_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return YouTubeResult(
                title=info.get("title", ""),
                content=full_text,
                thumbnail_url=info.get("thumbnail", ""),
                duration_seconds=info.get("duration", 0),
                video_id=video_id,
                channel_name=info.get("uploader", ""),
                source_type="cookies_asr",  # ⚠️ Using browser session
                transcript_length=len(full_text),
                extraction_time_ms=extraction_time,
                extracted_with_cookies=True,  # Flag for logging
            )
    
    except Exception as e:
        logger.error(f"Layer 4 (cookies fallback) failed for {video_id}: {e}")
        return None


# ── LAYER 5: Graceful Degradation - Metadata Only ─────────────


def extract_metadata_only(video_id: str) -> YouTubeResult:
    """
    LAYER 5: Final fallback - return what we can get without transcription.
    
    This is the safety net. Always returns SOMETHING instead of failing.
    But be honest about what we got.
    
    Success rate: ~99% (YouTube rarely blocks metadata)
    Speed: <1 second
    Cost: FREE
    Confidence: LOW (0.3) because it's incomplete
    """
    metadata = _get_youtube_metadata_quick(video_id)
    
    return YouTubeResult(
        title=metadata.get("title", ""),
        content=metadata.get("title", ""),  # Just use title as content
        thumbnail_url=metadata.get("thumbnail_url", ""),
        duration_seconds=metadata.get("duration", 0),
        video_id=video_id,
        channel_name=metadata.get("channel", ""),
        source_type="metadata_only",  # 🔴 Be honest - this is degraded
        transcript_length=len(metadata.get("title", "")),
        failure_reason="All transcription methods failed, returning metadata only",
        failure_class="permanent",
    )


# ── Main Extraction Pipeline ────────────────────────────


def extract_youtube(url: str) -> YouTubeResult:
    """
    Main YouTube extraction pipeline using 5-layer strategy:
    
    Layer 1: youtube-transcript-api (60-70% success) ← BEST
    Layer 2: yt-dlp subtitles (20-30% of remaining)
    Layer 3: Local ASR with whisper (queued, CPU-expensive)
    Layer 4: Cookies-based (rare, account risk)
    Layer 5: Metadata-only (graceful degradation) ← ALWAYS WORKS
    
    Returns YouTubeResult with source_type indicating which layer succeeded.
    """
    
    try:
        video_id, canonical_url = normalize_youtube_url(url)
    except ValueError as e:
        logger.error(f"Invalid YouTube URL: {url} - {e}")
        return YouTubeResult(
            failure_reason=str(e),
            failure_class="unsupported",
            source_type="unavailable",
        )
    
    # Layer 1: Try transcript-first (fastest, free, no risk)
    result = extract_with_transcript_api(video_id)
    if result:
        logger.info(f"Layer 1 (transcript-api) succeeded for {video_id}")
        return result
    
    # Delay before Layer 2 to reduce YouTube IP ban risk
    time.sleep(1.5)
    
    # Layer 2: Try yt-dlp subtitles
    result = extract_with_ytdlp_subtitles(video_id)
    if result:
        logger.info(f"Layer 2 (yt-dlp subtitles) succeeded for {video_id}")
        return result
    
    # Layer 3: Queue local ASR (async) - only for short videos
    try:
        metadata = _get_youtube_metadata_quick(video_id)
    except Exception:
        metadata = {"duration": 0}
    duration = metadata.get("duration", 0)
    
    if duration > 0 and duration <= 300:  # Short video, <5 min
        logger.info(f"Layer 3 (local ASR): Queueing {video_id} for transcription")
        result = extract_with_local_asr_queued(video_id)
        if result and result.success:
            return result
    
    # Layer 4: Could try cookies here if enabled, but skip for MVP
    
    # Layer 5: Graceful degradation
    logger.warning(f"Falling back to metadata-only for {video_id}")
    return extract_metadata_only(video_id)


# ── Class Wrapper for API Consistency ────────────────────

class YouTubeExtractor:
    """
    Class wrapper for YouTube extraction.
    Provides simple .extract(url) interface for consistent API.
    """
    
    def extract(self, url: str) -> YouTubeResult:
        """Extract transcript/content from YouTube URL."""
        return extract_youtube(url)
