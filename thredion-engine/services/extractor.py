"""
Thredion Engine — Content Extractor
Extracts meaningful content from Instagram, Twitter/X, and article URLs.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ExtractedContent:
    """Result of content extraction from a URL."""
    platform: str
    title: str
    content: str
    thumbnail_url: str
    url: str


def detect_platform(url: str) -> str:
    """Detect which platform a URL belongs to."""
    url_lower = url.lower()
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "reddit.com" in url_lower:
        return "reddit"
    elif "tiktok.com" in url_lower:
        return "tiktok"
    else:
        return "article"


def extract_from_url(url: str) -> ExtractedContent:
    """Main extraction dispatcher — routes to platform-specific extractor."""
    platform = detect_platform(url)

    extractors = {
        "instagram": _extract_instagram,
        "twitter": _extract_twitter,
        "youtube": _extract_youtube,
        "reddit": _extract_reddit,
        "tiktok": _extract_tiktok,
        "article": _extract_article,
    }

    extractor = extractors.get(platform, _extract_article)

    try:
        return extractor(url)
    except Exception as e:
        logger.warning(f"Extraction failed for {url}: {e}. Falling back to meta tags.")
        return _extract_meta_tags(url, platform)


def _extract_meta_tags(url: str, platform: str = "unknown") -> ExtractedContent:
    """Fallback: extract Open Graph / meta tags from any page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        title = _get_meta(soup, "og:title") or _get_meta(soup, "twitter:title") or ""
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

        content = _get_meta(soup, "og:description") or _get_meta(soup, "twitter:description") or ""
        if not content:
            desc = soup.find("meta", attrs={"name": "description"})
            content = desc["content"] if desc and desc.get("content") else ""

        thumbnail = _get_meta(soup, "og:image") or _get_meta(soup, "twitter:image") or ""

        return ExtractedContent(
            platform=platform,
            title=title[:512],
            content=content[:2000],
            thumbnail_url=thumbnail,
            url=url,
        )
    except Exception as e:
        logger.error(f"Meta tag extraction failed: {e}")
        return ExtractedContent(
            platform=platform, title="", content="", thumbnail_url="", url=url,
        )


def _get_meta(soup: BeautifulSoup, property_name: str) -> Optional[str]:
    """Helper to extract a meta tag value by property or name."""
    tag = soup.find("meta", attrs={"property": property_name})
    if not tag:
        tag = soup.find("meta", attrs={"name": property_name})
    return tag["content"] if tag and tag.get("content") else None


# ── Instagram ─────────────────────────────────────────────────

def _extract_instagram(url: str) -> ExtractedContent:
    """Extract content from an Instagram post/reel URL."""
    # Try oEmbed API first (works for public posts)
    try:
        oembed_url = f"https://api.instagram.com/oembed?url={url}&omitscript=true"
        resp = requests.get(oembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", "Instagram Post")
            author = data.get("author_name", "")
            content = title
            if author:
                content = f"By @{author}: {title}"
            thumbnail = data.get("thumbnail_url", "")
            return ExtractedContent(
                platform="instagram",
                title=title[:512],
                content=content[:2000],
                thumbnail_url=thumbnail,
                url=url,
            )
    except Exception:
        pass

    # Fallback to meta tags
    return _extract_meta_tags(url, "instagram")


# ── Twitter / X ───────────────────────────────────────────────

def _extract_twitter(url: str) -> ExtractedContent:
    """Extract content from a Twitter/X post URL."""
    # Normalize x.com → twitter.com for oEmbed
    normalized = url.replace("x.com", "twitter.com")
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={normalized}&omit_script=true"
        resp = requests.get(oembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            author = data.get("author_name", "")
            # Extract text from the HTML
            html = data.get("html", "")
            soup = BeautifulSoup(html, "html.parser")
            tweet_text = soup.get_text(strip=True)
            # Clean up
            tweet_text = re.sub(r"— .+\(.*\).*$", "", tweet_text).strip()
            return ExtractedContent(
                platform="twitter",
                title=f"Tweet by {author}" if author else "Tweet",
                content=tweet_text[:2000],
                thumbnail_url="",
                url=url,
            )
    except Exception:
        pass

    return _extract_meta_tags(url, "twitter")


# ── YouTube ───────────────────────────────────────────────────

def _extract_youtube(url: str) -> ExtractedContent:
    """Extract content from a YouTube URL."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        resp = requests.get(oembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return ExtractedContent(
                platform="youtube",
                title=data.get("title", "YouTube Video")[:512],
                content=data.get("title", "")[:2000],
                thumbnail_url=data.get("thumbnail_url", ""),
                url=url,
            )
    except Exception:
        pass

    return _extract_meta_tags(url, "youtube")


# ── Article ───────────────────────────────────────────────────

def _extract_article(url: str) -> ExtractedContent:
    """Extract content from a generic article/blog URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        title = _get_meta(soup, "og:title") or ""
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

        # Main content — try article tag, then main, then body
        content_text = ""
        for selector in ["article", "main", '[role="main"]', ".post-content", ".entry-content"]:
            el = soup.select_one(selector)
            if el:
                # Remove script/style
                for s in el.find_all(["script", "style", "nav", "footer"]):
                    s.decompose()
                content_text = el.get_text(separator=" ", strip=True)
                break

        if not content_text:
            content_text = _get_meta(soup, "og:description") or ""

        thumbnail = _get_meta(soup, "og:image") or ""

        return ExtractedContent(
            platform="article",
            title=title[:512],
            content=content_text[:2000],
            thumbnail_url=thumbnail,
            url=url,
        )
    except Exception as e:
        logger.error(f"Article extraction failed: {e}")
        return _extract_meta_tags(url, "article")


# ── Reddit ────────────────────────────────────────────────────

def _extract_reddit(url: str) -> ExtractedContent:
    """Extract content from a Reddit post URL."""
    try:
        json_url = url.rstrip("/") + ".json"
        resp = requests.get(json_url, headers={**HEADERS, "Accept": "application/json"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                post = data[0]["data"]["children"][0]["data"]
                title = post.get("title", "Reddit Post")
                selftext = post.get("selftext", "")[:1500]
                subreddit = post.get("subreddit_name_prefixed", "")
                thumbnail = post.get("thumbnail", "")
                if thumbnail in ("self", "default", "nsfw", "spoiler", ""):
                    thumbnail = post.get("url_overridden_by_dest", "")
                    if not thumbnail.endswith((".jpg", ".png", ".gif", ".webp")):
                        thumbnail = ""
                content = f"{subreddit} — {title}"
                if selftext:
                    content += f"\n{selftext}"
                return ExtractedContent(
                    platform="reddit",
                    title=title[:512],
                    content=content[:2000],
                    thumbnail_url=thumbnail,
                    url=url,
                )
    except Exception:
        pass
    return _extract_meta_tags(url, "reddit")


# ── TikTok ────────────────────────────────────────────────────

def _extract_tiktok(url: str) -> ExtractedContent:
    """Extract content from a TikTok video URL using oEmbed."""
    try:
        oembed_url = f"https://www.tiktok.com/oembed?url={url}"
        resp = requests.get(oembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", "TikTok Video")
            author = data.get("author_name", "")
            thumbnail = data.get("thumbnail_url", "")
            content = title
            if author:
                content = f"By @{author}: {title}"
            return ExtractedContent(
                platform="tiktok",
                title=title[:512],
                content=content[:2000],
                thumbnail_url=thumbnail,
                url=url,
            )
    except Exception:
        pass
    return _extract_meta_tags(url, "tiktok")
