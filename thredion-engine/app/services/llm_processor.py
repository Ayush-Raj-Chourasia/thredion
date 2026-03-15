
import json
import logging
import httpx
import re
from typing import List, Optional, Dict
from openai import OpenAI
try:
    from groq import Groq
except ImportError:
    Groq = None

from core.config import settings
from app.models.schemas import LLMStructuredOutput

logger = logging.getLogger(__name__)

def process_entry(text: str, input_type: str, existing_buckets: List[str]) -> Optional[LLMStructuredOutput]:
    """
    Core LLM structuring engine. 
    Transforms raw text into a structured cognitive entry.
    Supports OpenAI with Groq fallback.
    """
    # 1. Prepare Prompts
    buckets_str = ", ".join(existing_buckets) if existing_buckets else "None yet"

    system_prompt = f"""You are a cognitive structuring engine. You receive raw input and MUST respond with a valid JSON object.

REQUIRED FIELDS:
1. "cognitive_mode": String. Values: "learn" (for content consumed), "think" (for original ideas), "reflect" (for personal feelings/diary).
2. "title": String. Max 10 words. Concise name for the entry.
3. "summary": String. 2-3 sentences.
4. "key_points": List of strings.
5. "bucket": String. Choose from existing buckets if possible: [{buckets_str}]. Otherwise create a new broad category.
6. "tags": List of strings.
7. "actionability_score": Float (0.0 to 1.0).
8. "emotional_tone": String. One word (neutral/curious/anxious/excited/reflective/motivated/frustrated/hopeful).
9. "confidence_score": Float (0.0 to 1.0).

BUCKET RULES:
- ALWAYS prefer an existing bucket from the list above.
- Suggest a new one ONLY if the content is fundamentally different.

IMPORTANT: Respond ONLY with the JSON object. Do not include markdown or explanations.
"""

    user_prompt = f"""
Input Type: {input_type}
Raw Content:
---
{text[:4000]}
---
Return ONLY the structured JSON.
"""

    # 2. Try OpenAI first
    if settings.OPENAI_API_KEY:
        try:
            logger.info("Attempting LLM processing via OpenAI...")
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            raw_json = response.choices[0].message.content
            return _parse_json_result(raw_json)
        except Exception as e:
            logger.warning(f"OpenAI processing failed (quota or error): {e}")

    # 3. Fallback to Groq
    if settings.GROQ_API_KEY and Groq:
        try:
            logger.info("Attempting LLM processing via Groq Fallback...")
            groq_client = Groq(api_key=settings.GROQ_API_KEY)
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1, # Even lower for stricter format
            )
            raw_json = response.choices[0].message.content
            return _parse_json_result(raw_json)
        except Exception as e:
            logger.error(f"Groq processing failed: {e}")

    logger.error("All LLM providers failed or are unconfigured.")
    return None

def _parse_json_result(raw_json: str) -> Optional[LLMStructuredOutput]:
    """Parses and validates LLM JSON response with cleaning."""
    try:
        # Strip markdown code blocks if present
        clean_json = re.sub(r'```json\s*|\s*```', '', raw_json).strip()
        data = json.loads(clean_json)
        
        # Mapping common misnamed fields or empty values
        if "classification" in data and "cognitive_mode" not in data:
            data["cognitive_mode"] = data.pop("classification")
            
        if not data.get("bucket") or data.get("bucket").lower() == "none":
            data["bucket"] = "General"
            
        return LLMStructuredOutput(**data)
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON: {e} | Raw: {raw_json}")
        return None
