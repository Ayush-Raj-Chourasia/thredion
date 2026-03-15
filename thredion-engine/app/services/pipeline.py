
import re
import logging
import asyncio
from typing import Optional
from uuid import UUID

from app.services import supabase_client, extractor, transcriber, llm_processor
from app.models.schemas import CognitiveEntryCreate

logger = logging.getLogger(__name__)

async def process_incoming(phone_number: str, message_text: str = None, voice_file_url: str = None) -> dict:
    """
    Unified entry point for all cognitive captures.
    Orchestrates extraction, transcription, cleaning, and LLM structuring.
    """
    logger.info(f"Incoming capture from {phone_number}")
    
    # 1. Get or create user
    user = supabase_client.get_or_create_user(phone_number)
    
    # 2. Detect input type
    input_type = "text"
    source_url = None
    original_input = message_text or ""
    
    if voice_file_url:
        input_type = "voice"
        original_input = voice_file_url # Use URL as original input for voice
    elif message_text:
        detected_type, detected_url = extractor.detect_input_type(message_text)
        input_type = detected_type
        source_url = detected_url

    # 3. Create initial entry (Pending status)
    # We save cognitive_mode as 'learn' initially, it will be corrected by LLM
    initial_data = {
        "input_type": input_type,
        "cognitive_mode": "learn", 
        "original_input": original_input,
        "source_url": source_url,
        "processing_status": "processing"
    }
    entry = supabase_client.create_entry(user.id, initial_data)
    
    try:
        raw_text = ""
        
        # 4. Processing based on type
        if input_type == "voice":
            logger.info("Processing voice capture...")
            raw_text = await transcriber.transcribe_from_url(voice_file_url)
        elif input_type == "link":
            logger.info(f"Processing link capture: {source_url}")
            extracted = await extractor.extract_content(source_url)
            raw_text = extracted.get("raw_text", "")
            title_guess = extracted.get("title")
        else:
            logger.info("Processing text capture...")
            raw_text = message_text

        # 5. Clean text
        cleaned_text = clean_text(raw_text, is_voice=(input_type == "voice"))
        cleaned_text = cleaned_text[:4000] # Stay within context limits
        
        # 6. Structured Analysis
        existing_buckets = supabase_client.get_user_buckets(user.id)
        llm_output = llm_processor.process_entry(cleaned_text, input_type, existing_buckets)
        
        if not llm_output:
            raise Exception("LLM processing failed to return structured output")

        # 7. Handle Bucketing (Enforce max 20)
        bucket_name = llm_output.bucket
        current_buckets = existing_buckets
        
        if bucket_name not in current_buckets and len(current_buckets) >= 20:
            logger.warning(f"User {user.id} has reached bucket limit. Forcing into existing.")
            # Simple fallback: use the first existing bucket
            bucket_name = current_buckets[0]
        else:
            supabase_client.create_or_get_bucket(user.id, bucket_name)

        # 8. Final update
        updates = {
            "cognitive_mode": llm_output.cognitive_mode,
            "title": llm_output.title,
            "summary": llm_output.summary,
            "cleaned_text": cleaned_text,
            "key_points": llm_output.key_points,
            "bucket": bucket_name,
            "tags": llm_output.tags,
            "actionability_score": llm_output.actionability_score,
            "emotional_tone": llm_output.emotional_tone,
            "confidence_score": llm_output.confidence_score,
            "processing_status": "completed"
        }
        
        updated_entry = supabase_client.update_entry(entry.id, updates)
        return updated_entry.dict()

    except Exception as e:
        logger.error(f"Pipeline error for entry {entry.id}: {e}")
        supabase_client.update_entry(entry.id, {"processing_status": "failed"})
        return {
            "id": str(entry.id),
            "error": str(e),
            "original_input": original_input,
            "processing_status": "failed"
        }

def clean_text(text: str, is_voice: bool = False) -> str:
    """Basic text cleanup."""
    # Remove HTML if generic extraction was used
    text = re.sub(r'<[^>]*>', '', text)
    
    # Simple regex for voice filler words
    if is_voice:
        fillers = [r'\bum\b', r'\buh\b', r'\blike\b', r'\byou know\b', r'\bbasically\b', r'\bactually\b']
        for pattern in fillers:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
