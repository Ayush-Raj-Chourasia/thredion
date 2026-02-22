"""
Thredion Engine — WhatsApp Webhook (Twilio)
Handles incoming WhatsApp messages, processes URLs, and replies with AI insights.
"""

import re
import logging

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from db.database import get_db
from services.pipeline import process_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Regex to extract URLs from messages
URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
    r'[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
)


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Twilio WhatsApp webhook endpoint.
    Receives incoming messages, extracts URLs, processes them, and replies.
    """
    # Parse form data from Twilio
    try:
        form_data = await request.form()
    except Exception:
        return _twiml_response(_build_help_reply())
    body = form_data.get("Body", "") or ""
    from_number = form_data.get("From", "unknown") or "unknown"
    
    # Clean phone number
    user_phone = str(from_number).replace("whatsapp:", "").strip() or "unknown"
    
    logger.info(f"[WhatsApp] Message from {user_phone}: {body}")

    # Extract URLs from message
    urls = URL_PATTERN.findall(str(body))

    if not urls:
        # No URL found — send help message
        reply = _build_help_reply()
        return _twiml_response(reply)

    # Process each URL
    replies = []
    for url in urls[:3]:  # Max 3 URLs per message
        try:
            result = process_url(url, user_phone, db)
            if result.get("duplicate"):
                replies.append(_build_duplicate_reply(result))
            else:
                replies.append(_build_success_reply(result))
        except Exception as e:
            logger.error(f"[WhatsApp] Failed to process {url}: {e}")
            replies.append(f"⚠️ Couldn't process: {url}\nError: {str(e)[:100]}")

    full_reply = "\n\n---\n\n".join(replies)
    return _twiml_response(full_reply)


@router.get("/webhook")
async def whatsapp_verify():
    """Health check / verification endpoint for Twilio."""
    return PlainTextResponse("Thredion WhatsApp webhook is active ✓")


def _build_duplicate_reply(result: dict) -> str:
    """Build a reply when the URL was already saved."""
    summary = result.get("summary", "")
    category = result.get("category", "")
    score = result.get("importance_score", 0)
    return (
        "🔁 *Already in your memory vault!*\n\n"
        f"📝 *Summary:* {summary}\n"
        f"🏷️ *Category:* {category}\n"
        f"⭐ *Importance:* {score}/100\n\n"
        "This link was previously saved. No duplicate created."
    )


def _build_success_reply(result: dict) -> str:
    """Build a rich WhatsApp reply after processing a URL."""
    parts = []

    # Header
    parts.append("🧠 *Thredion — Memory Saved!*")
    parts.append("")

    # Summary
    summary = result.get("summary", "Content saved.")
    parts.append(f"📝 *Summary:* {summary}")

    # Category
    category = result.get("category", "Uncategorized")
    parts.append(f"🏷️ *Category:* {category}")

    # Importance
    score = result.get("importance_score", 0)
    bar = _importance_bar(score)
    parts.append(f"⭐ *Importance:* {score}/100 {bar}")

    # Tags
    tags = result.get("tags", [])
    if tags:
        parts.append(f"🔖 *Tags:* {', '.join(tags[:5])}")

    # Topic Graph
    topics = result.get("topic_graph", [])
    if topics:
        parts.append(f"🌐 *Topics:* {' → '.join(topics[:4])}")

    # Connections
    connections = result.get("connections", [])
    if connections:
        parts.append("")
        parts.append(f"🔗 *Connected to {len(connections)} related memory(s):*")
        for conn in connections[:3]:
            title = conn.get("connected_memory_title", "?")
            sim = int(conn.get("similarity_score", 0) * 100)
            parts.append(f"  • {title} ({sim}% similar)")

    # Resurfaced
    resurfaced = result.get("resurfaced", [])
    if resurfaced:
        parts.append("")
        parts.append("💡 *Resurfaced Insight:*")
        for r in resurfaced[:2]:
            title = r.get("memory_title", "?")
            reason = r.get("reason", "")
            parts.append(f"  ↳ _{title}_")
            parts.append(f"    {reason}")

    parts.append("")
    parts.append("📊 View dashboard: thredion.vercel.app")

    return "\n".join(parts)


def _build_help_reply() -> str:
    """Build a help message when no URL is found."""
    return (
        "🧠 *Thredion — AI Cognitive Memory Engine*\n\n"
        "Send me a link and I'll:\n"
        "• 📝 Summarize it with AI\n"
        "• 🏷️ Auto-categorize it\n"
        "• 🔗 Connect it to related memories\n"
        "• ⭐ Score its importance\n"
        "• 💡 Resurface forgotten insights\n\n"
        "Supported:\n"
        "• Instagram reels/posts\n"
        "• Twitter/X posts\n"
        "• YouTube videos\n"
        "• Blog articles\n\n"
        "Just paste a URL and I'll handle the rest! 🚀"
    )


def _importance_bar(score: float) -> str:
    """Create a visual bar for importance score."""
    filled = int(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _twiml_response(message: str) -> PlainTextResponse:
    """Wrap reply in TwiML format for Twilio."""
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{_escape_xml(message)}</Message>"
        "</Response>"
    )
    return PlainTextResponse(content=twiml, media_type="application/xml")


def _escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
