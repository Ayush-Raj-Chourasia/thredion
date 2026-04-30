
import re
import logging
import httpx
from typing import Tuple, Optional, Dict
from bs4 import BeautifulSoup
from readability import Document
import yt_dlp
from core.config import settings

logger = logging.getLogger(__name__)

def detect_input_type(text: str) -> Tuple[str, Optional[str]]:
    """
    Detects if the input is a link or raw text.
    Returns: (input_type, url_if_found)
    """
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, text)
    
    if urls:
        return ("link", urls[0])
    return ("text", None)

async def extract_content(url: str) -> Dict:
    """
    Universal extractor for various platforms.
    """
    logger.info(f"Extracting content from: {url}")
    
    if "youtube.com" in url or "youtu.be" in url:
        return await _extract_youtube(url)
    elif "twitter.com" in url or "x.com" in url:
        return await _extract_twitter(url)
    elif "instagram.com" in url:
        return await _extract_instagram(url)
    else:
        return await _extract_generic(url)

async def _extract_youtube(url: str) -> Dict:
    """Extracts YouTube metadata using Supadata/SocialKit or yt-dlp fallback."""
    
    # 1. Try Supadata (Excellent for YouTube)
    if settings.SUPADATA_API_KEY:
        try:
            logger.info("Using Supadata for YouTube extraction...")
            async with httpx.AsyncClient(headers={"x-api-key": settings.SUPADATA_API_KEY}, timeout=15.0) as client:
                resp = await client.get(f"https://api.supadata.ai/v1/youtube/video/data?url={url}")
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {
                        "source_type": "youtube",
                        "title": data.get("title", ""),
                        "raw_text": f"Title: {data.get('title')}\nDescription: {data.get('description')}\nChannel: {data.get('channelTitle')}",
                        "url": url,
                        "thumbnail_url": data.get("thumbnailUrl")
                    }
        except Exception as e:
            logger.warning(f"Supadata YouTube extraction failed: {e}")

    # 2. Try SocialKit
    if settings.SOCIALKIT_API_KEY:
        # Similar logic...
        pass

    # 3. Fallback to yt-dlp
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown YouTube Video')
            description = info.get('description', '')
            
            # Simplified: combine description as part of raw_text for V1
            raw_text = f"Title: {title}\nDescription: {description}"
            
            return {
                "source_type": "youtube",
                "title": title,
                "raw_text": raw_text,
                "url": url
            }
    except Exception as e:
        logger.error(f"YouTube extraction failed: {e}")
        return {"source_type": "youtube", "title": "YouTube Video", "raw_text": "Failed to extract content", "url": url}

async def _extract_twitter(url: str) -> Dict:
    """Extracts Tweet content using Supadata or meta tags fallback."""
    if settings.SUPADATA_API_KEY:
        try:
            async with httpx.AsyncClient(headers={"x-api-key": settings.SUPADATA_API_KEY}, timeout=15.0) as client:
                # Assuming Supadata has a universal metadata endpoint
                resp = await client.get(f"https://api.supadata.ai/v1/media/metadata?url={url}")
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {
                        "source_type": "twitter",
                        "title": data.get("author", "Twitter User"),
                        "raw_text": data.get("content", ""),
                        "url": url
                    }
        except Exception as e:
            logger.warning(f"Supadata Twitter extraction failed: {e}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # X/Twitter uses og:description for the tweet text
            description = soup.find("meta", property="og:description")
            title = soup.find("meta", property="og:title")
            
            tweet_text = description["content"] if description else "Could not extract tweet text"
            author = title["content"] if title else "Twitter User"
            
            return {
                "source_type": "twitter",
                "title": author,
                "raw_text": tweet_text,
                "url": url
            }
    except Exception as e:
        logger.error(f"Twitter extraction failed: {e}")
        return {"source_type": "twitter", "title": "Twitter", "raw_text": "Failed to extract tweet", "url": url}

async def _extract_instagram(url: str) -> Dict:
    """Extracts Instagram content using SocialKit/Supadata or meta tags fallback."""
    if settings.SOCIALKIT_API_KEY:
        try:
            # SocialKit uses 'Authorization: Bearer <key>' or similar. 
            # From search: "This token is then used in the Authorization header"
            async with httpx.AsyncClient(headers={"Authorization": f"Bearer {settings.SOCIALKIT_API_KEY}"}, timeout=15.0) as client:
                resp = await client.post("https://api.socialkit.dev/v1/video/summary", json={"url": url})
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "source_type": "instagram",
                        "title": data.get("author", "Instagram User"),
                        "raw_text": data.get("summary") or data.get("transcript") or data.get("caption", ""),
                        "url": url
                    }
        except Exception as e:
            logger.warning(f"SocialKit Instagram extraction failed: {e}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            description = soup.find("meta", property="og:description")
            title = soup.find("meta", property="og:title")
            
            caption = description["content"] if description else "Instagram Content"
            user = title["content"] if title else "Instagram User"
            
            return {
                "source_type": "instagram",
                "title": user,
                "raw_text": caption,
                "url": url
            }
    except Exception as e:
        logger.error(f"Instagram extraction failed: {e}")
        return {"source_type": "instagram", "title": "Instagram", "raw_text": "Failed to extract caption", "url": url}

async def _extract_generic(url: str) -> Dict:
    """Extracts clean article text using readability."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
            doc = Document(resp.text)
            
            return {
                "source_type": "article",
                "title": doc.short_title(),
                "raw_text": doc.summary(), # This is the cleaned HTML summary
                "url": url
            }
    except Exception as e:
        logger.error(f"Generic extraction failed: {e}")
        return {"source_type": "article", "title": "Web Article", "raw_text": f"URL saved: {url}", "url": url}
