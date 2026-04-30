
import logging
from typing import List, Dict
from app.services import supabase_client
from app.models.schemas import CognitiveEntry
import openai
from core.config import settings

logger = logging.getLogger(__name__)

async def synthesize_week(phone_number: str) -> Dict:
    """Analyzes the week's entries to find patterns, themes, and gaps."""
    user = supabase_client.get_or_create_user(phone_number)
    entries = supabase_client.get_weekly_entries(user.id)
    
    if not entries:
        return {"patterns": [], "themes": [], "gaps": []}
        
    # Prepare text for LLM
    entry_texts = []
    for e in entries:
        entry_texts.append(f"[{e.cognitive_mode.upper()}] {e.title}: {e.summary} (Bucket: {e.bucket})")
        
    unified_text = "\n".join(entry_texts)
    
    prompt = f"""
    Analyze the following cognitive entries captured this week. 
    Identify:
    1. Converging Themes: 2-3 main topics the user focused on.
    2. Actionable Patterns: Suggestions based on repeating ideas.
    3. Curiosity Gaps: What's missing? (e.g., 'You learned a lot about AI theory but haven't captured any practical implementation steps').

    Entries:
    {unified_text}

    Respond in JSON format:
    {{
      "themes": ["theme 1", "theme 2"],
      "patterns": ["pattern 1", "pattern 2"],
      "gaps": ["gap 1"]
    }}
    """
    
    try:
        if not settings.OPENAI_API_KEY:
             return {"themes": ["No OpenAI Key"], "patterns": [], "gaps": []}
             
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a cognitive synthesis engine."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {"error": str(e)}
