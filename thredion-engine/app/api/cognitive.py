
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.services import supabase_client, pipeline
from app.models.schemas import CognitiveEntry, WeeklySummary, ProcessRequest

router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])

@router.post("/process")
async def process_content(request: ProcessRequest):
    """Manual trigger for processing content."""
    try:
        result = await pipeline.process_incoming(
            phone_number=request.phone_number,
            message_text=request.message_text,
            voice_file_url=request.voice_file_url,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard", response_model=WeeklySummary)
async def get_dashboard_data(phone_number: str):
    """Get weekly summary and statistics for the dashboard."""
    user = supabase_client.get_or_create_user(phone_number)
    entries = supabase_client.get_weekly_entries(user.id)
    
    # Simple aggregation
    stats = {"learn": 0, "think": 0, "reflect": 0}
    buckets = {}
    
    for e in entries:
        stats[e.cognitive_mode] += 1
        buckets[e.bucket] = buckets.get(e.bucket, 0) + 1
        
    bucket_list = [{"name": k, "count": v} for k, v in buckets.items()]
    bucket_list.sort(key=lambda x: x["count"], reverse=True)
    
    # Sort entries by actionability or date
    top_entries = sorted(entries, key=lambda x: x.created_at, reverse=True)[:5]
    
    return WeeklySummary(
        entries_by_mode=stats,
        entries_by_bucket=bucket_list,
        top_entries=top_entries,
        most_active_bucket=bucket_list[0]["name"] if bucket_list else None,
        total_count=len(entries)
    )

@router.get("/entries", response_model=List[CognitiveEntry])
async def list_entries(
    phone_number: str,
    mode: Optional[str] = None,
    bucket: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List cognitive entries with filtering and pagination."""
    user = supabase_client.get_or_create_user(phone_number)
    return supabase_client.get_entries_by_user(
        user_id=user.id,
        mode=mode,
        bucket=bucket,
        limit=limit,
        offset=offset
    )
