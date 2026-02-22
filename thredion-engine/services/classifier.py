"""
Thredion Engine — AI Classifier & Summarizer
Classifies content into categories, generates summaries, and extracts topic graphs.
Uses OpenAI if available, falls back to keyword-based classification.
"""

import json
import logging
import re
from dataclasses import dataclass

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of AI classification."""
    category: str
    summary: str
    tags: list[str]
    topic_graph: list[str]


# ── Keyword Mapping (Fallback) ────────────────────────────────

KEYWORD_MAP: dict[str, list[str]] = {
    "Fitness": ["workout", "exercise", "gym", "muscle", "fitness", "cardio", "abs",
                "bodyweight", "training", "squat", "deadlift", "yoga", "stretch", "core"],
    "Coding": ["python", "javascript", "code", "programming", "developer", "api",
               "react", "fastapi", "algorithm", "software", "debug", "github", "coding",
               "frontend", "backend", "database", "deploy", "typescript", "node"],
    "Design": ["design", "ui", "ux", "figma", "logo", "brand", "typography",
               "color", "layout", "graphic", "creative", "photoshop", "canva"],
    "Food": ["recipe", "cook", "food", "meal", "pasta", "chicken", "bake",
             "restaurant", "cuisine", "kitchen", "ingredient", "diet", "nutrition"],
    "Travel": ["travel", "trip", "destination", "flight", "hotel", "beach",
               "mountain", "explore", "vacation", "tourism", "adventure", "backpack"],
    "Business": ["business", "startup", "entrepreneur", "marketing", "sales",
                 "revenue", "growth", "strategy", "market", "invest", "profit"],
    "Science": ["science", "research", "experiment", "physics", "chemistry",
                "biology", "space", "quantum", "dna", "climate", "evolution"],
    "Music": ["music", "song", "beat", "musician", "guitar", "piano",
              "producer", "album", "concert", "melody", "rhythm", "rap"],
    "Art": ["art", "painting", "sculpture", "gallery", "artist", "canvas",
            "draw", "sketch", "portrait", "abstract", "illustration"],
    "Fashion": ["fashion", "style", "outfit", "clothing", "trend", "wear",
                "wardrobe", "accessory", "streetwear", "luxury"],
    "Education": ["learn", "study", "course", "tutorial", "lesson", "university",
                  "student", "education", "skill", "knowledge", "teach"],
    "Technology": ["tech", "ai", "machine learning", "robotics", "gadget",
                   "smartphone", "innovation", "cloud", "blockchain", "data"],
    "Health": ["health", "mental", "wellness", "meditation", "sleep",
               "anxiety", "therapy", "mindfulness", "self-care", "stress"],
    "Finance": ["finance", "money", "invest", "stock", "crypto", "budget",
                "saving", "income", "wealth", "trading", "portfolio"],
    "Motivation": ["motivation", "inspire", "success", "mindset", "hustle",
                   "discipline", "goal", "productive", "habit", "grind"],
}


def classify_content(text: str, url: str = "") -> ClassificationResult:
    """
    Classify and summarize content.
    Uses OpenAI API if key is available, otherwise keyword-based fallback.
    """
    combined_text = f"{text} {url}".strip()

    if settings.OPENAI_API_KEY:
        try:
            return _classify_with_openai(combined_text)
        except Exception as e:
            logger.warning(f"OpenAI classification failed: {e}. Falling back to keywords.")

    return _classify_with_keywords(combined_text)


def _classify_with_openai(text: str) -> ClassificationResult:
    """Classify content using OpenAI GPT."""
    import openai

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    categories_str = ", ".join(settings.CATEGORIES)

    prompt = f"""Analyze this social media content and return a JSON object with these fields:

1. "category": One of [{categories_str}]. Pick the BEST match.
2. "summary": A concise 1-2 sentence summary capturing the key insight.
3. "tags": A list of 3-5 relevant tags (lowercase, no #).
4. "topic_graph": A hierarchical list of topics from broad to specific (3-5 items).
   Example: ["Technology", "Programming", "Python", "Web Development", "FastAPI"]

Content to analyze:
---
{text[:1500]}
---

Return ONLY valid JSON. No markdown, no explanation."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    result_text = response.choices[0].message.content.strip()

    # Clean potential markdown wrapping
    if result_text.startswith("```"):
        result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
        result_text = re.sub(r"\s*```$", "", result_text)

    data = json.loads(result_text)

    return ClassificationResult(
        category=data.get("category", "Uncategorized"),
        summary=data.get("summary", text[:200]),
        tags=data.get("tags", []),
        topic_graph=data.get("topic_graph", [data.get("category", "General")]),
    )


def _classify_with_keywords(text: str) -> ClassificationResult:
    """Fallback: classify content using keyword matching."""
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        category = max(scores, key=scores.get)
    else:
        category = "Uncategorized"

    # Generate simple summary
    sentences = re.split(r'[.!?]+', text)
    summary = sentences[0].strip()[:200] if sentences else text[:200]
    if not summary:
        summary = "Saved content"

    # Extract tags from text
    words = re.findall(r'#(\w+)', text)
    if not words:
        words = [w for w in text_lower.split() if len(w) > 4][:5]
    tags = list(set(words[:5]))

    # Build topic graph
    topic_graph = [category]
    if category in KEYWORD_MAP:
        matched = [kw for kw in KEYWORD_MAP[category] if kw in text_lower]
        topic_graph.extend(matched[:3])

    return ClassificationResult(
        category=category,
        summary=summary,
        tags=tags,
        topic_graph=topic_graph,
    )
