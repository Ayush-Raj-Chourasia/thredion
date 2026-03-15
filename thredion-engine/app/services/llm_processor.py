
import json
import logging
import httpx
from typing import List, Optional
from openai import OpenAI
from core.config import settings
from app.models.schemas import LLMStructuredOutput

logger = logging.getLogger(__name__)

def process_entry(text: str, input_type: str, existing_buckets: List[str]) -> Optional[LLMStructuredOutput]:
    """
    Core LLM structuring engine. 
    Transforms raw text into a structured cognitive entry.
    """
    if not settings.OPENAI_API_KEY:
        logger.error("Missing OPENAI_API_KEY for LLM processing.")
        return None

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Bucket names for prompt
    buckets_str = ", ".join(existing_buckets) if existing_buckets else "None yet"

    system_prompt = f"""You are a cognitive structuring engine. You receive raw input from a user — either content
from a URL they consumed, a voice note transcription of their thoughts, or a text message
with an idea/reflection.
Your job is to classify, structure, and summarize it.

CLASSIFICATION RULES:
- "learn": External content the user consumed — articles, videos, threads, podcasts, saved
links. The user is learning FROM this content.
- "think": Original ideas, observations, business thoughts, startup ideas, frameworks the user
GENERATED. These are the user's own thoughts.
- "reflect": Personal reflections, dreams, emotional entries, diary-style thoughts, life
observations. These are about the user's INNER state.

BUCKET RULES:
- Here are the user's existing buckets: {buckets_str}
- ALWAYS prefer an existing bucket if the content fits even loosely
- Only suggest a new bucket if nothing fits at all
- Keep bucket names broad and simple (1-2 words max): "Marketing", "AI Tools", "Startup
Ideas", "Health", etc.
- Never create overly specific buckets

OUTPUT FORMAT (JSON):
Respond with a raw JSON object matching the requested schema. Ensure all fields are present.
"""

    user_prompt = f"""
Input Type: {input_type}
Raw Content:
---
{text[:4000]}
---
Analyze and structure this content according to the schema.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3, # Low temperature for consistent structure
        )
        
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        
        # Enforce max 20 buckets if we create a new one (Logic added in pipeline)
        
        return LLMStructuredOutput(**data)

    except Exception as e:
        logger.error(f"LLM processing failed: {e}")
        return None
