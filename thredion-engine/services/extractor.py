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

def _parse_instagram_url(url: str) -> dict:
    """Parse an Instagram URL to extract content type and shortcode."""
    info = {"type": "post", "shortcode": "", "username": ""}
    url_lower = url.lower()
    if "/reel/" in url_lower or "/reels/" in url_lower:
        info["type"] = "reel"
    elif "/stories/" in url_lower:
        info["type"] = "story"
    elif "/p/" in url_lower:
        info["type"] = "post"
    elif "/tv/" in url_lower:
        info["type"] = "igtv"

    # Extract shortcode
    match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', url)
    if match:
        info["shortcode"] = match.group(1)

    # Extract username from stories or profile URLs
    match = re.search(r'/stories/([^/]+)/', url)
    if match:
        info["username"] = match.group(1)
    elif not any(x in url for x in ["/p/", "/reel/", "/reels/", "/tv/"]):
        match = re.search(r'instagram\.com/([A-Za-z0-9_.]+)', url)
        if match and match.group(1) not in ("explore", "accounts", "about", "developer"):
            info["username"] = match.group(1)

    return info


def _extract_instagram(url: str) -> ExtractedContent:
    """Extract content from an Instagram post/reel URL."""
    url_info = _parse_instagram_url(url)
    content_type = url_info["type"]
    shortcode = url_info["shortcode"]

    # Strategy 1: Try noembed.com proxy (free, no auth required)
    try:
        noembed_url = f"https://noembed.com/embed?url={url}"
        resp = requests.get(noembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("title") and not data.get("error"):
                title = data.get("title", "")
                author = data.get("author_name", "")
                thumbnail = data.get("thumbnail_url", "")
                content = title
                if author:
                    content = f"Instagram {content_type} by @{author}: {title}"
                else:
                    content = f"Instagram {content_type}: {title}"
                return ExtractedContent(
                    platform="instagram",
                    title=title[:512],
                    content=content[:2000],
                    thumbnail_url=thumbnail,
                    url=url,
                )
    except Exception as e:
        logger.debug(f"noembed.com failed for Instagram: {e}")

    # Strategy 2: Try Instagram oEmbed (may require auth, often returns HTML)
    try:
        oembed_url = f"https://api.instagram.com/oembed?url={url}&omitscript=true"
        resp = requests.get(oembed_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
            data = resp.json()
            title = data.get("title", f"Instagram {content_type.title()}")
            author = data.get("author_name", "")
            content = title
            if author:
                content = f"Instagram {content_type} by @{author}: {title}"
            thumbnail = data.get("thumbnail_url", "")
            return ExtractedContent(
                platform="instagram",
                title=title[:512],
                content=content[:2000],
                thumbnail_url=thumbnail,
                url=url,
            )
    except Exception as e:
        logger.debug(f"Instagram oEmbed failed: {e}")

    # Strategy 3: Scrape meta tags with a fresh session
    try:
        session = requests.Session()
        # First visit the main page to get cookies
        session.get("https://www.instagram.com/", headers=HEADERS, timeout=5)
        resp = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        og_title = _get_meta(soup, "og:title") or ""
        og_desc = _get_meta(soup, "og:description") or ""
        og_image = _get_meta(soup, "og:image") or ""

        # Check if we got real data (not just "Instagram")
        if og_title and og_title.strip().lower() != "instagram":
            content = og_title
            if og_desc:
                content = f"{og_title} — {og_desc}"
            return ExtractedContent(
                platform="instagram",
                title=og_title[:512],
                content=content[:2000],
                thumbnail_url=og_image,
                url=url,
            )
    except Exception as e:
        logger.debug(f"Instagram meta tag scraping failed: {e}")

    # Strategy 4: Construct meaningful metadata from URL structure
    type_labels = {
        "reel": "Instagram Reel",
        "post": "Instagram Post",
        "story": "Instagram Story",
        "igtv": "Instagram IGTV Video",
    }
    title = type_labels.get(content_type, "Instagram Content")
    if shortcode:
        title = f"{title} ({shortcode})"

    content_desc = f"{title} — Shared via Instagram."
    if content_type == "reel":
        content_desc = f"{title} — Short-form video content shared via Instagram Reels. Entertainment and social media content."
    elif content_type == "story":
        content_desc = f"{title} — Ephemeral story content shared on Instagram."
    elif content_type == "igtv":
        content_desc = f"{title} — Long-form video content on Instagram IGTV."

    if url_info["username"]:
        content_desc += f" Creator: @{url_info['username']}."

    # Strategy 5: Try to get thumbnail via a direct meta-tag fetch with minimal headers
    thumbnail = ""
    try:
        clean_url = url.split("?")[0]  # strip query params for cleaner request
        if not clean_url.endswith("/"):
            clean_url += "/"
        meta_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "text/html",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(clean_url, headers=meta_headers, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        thumbnail = (
            _get_meta(soup, "og:image")
            or _get_meta(soup, "twitter:image")
            or ""
        )
        if thumbnail:
            logger.debug(f"Got Instagram thumbnail via Googlebot UA: {thumbnail[:80]}")
    except Exception as e:
        logger.debug(f"Instagram thumbnail fetch failed: {e}")

    return ExtractedContent(
        platform="instagram",
        title=title,
        content=content_desc,
        thumbnail_url=thumbnail,
        url=url,
    )


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
