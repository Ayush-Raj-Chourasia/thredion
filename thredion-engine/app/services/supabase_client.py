
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from supabase import Client, create_client
from core.config import settings
from app.models.schemas import User, CognitiveEntry, CognitiveEntryCreate

logger = logging.getLogger(__name__)

# Initialize client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_or_create_user(phone_number: str) -> User:
    """Finds or creates a user by phone number."""
    # Clean phone number (ensure only digits)
    phone = ''.join(filter(str.isdigit, phone_number))
    
    response = supabase.table("users").select("*").eq("phone_number", phone).execute()
    
    if response.data:
        return User(**response.data[0])
    
    # Create new user
    new_user = {
        "phone_number": phone
    }
    insert_response = supabase.table("users").insert(new_user).execute()
    return User(**insert_response.data[0])

def create_entry(user_id: UUID, entry_data: dict) -> CognitiveEntry:
    """Creates a new cognitive entry."""
    data = {**entry_data, "user_id": str(user_id)}
    response = supabase.table("cognitive_entries").insert(data).execute()
    return CognitiveEntry(**response.data[0])

def update_entry(entry_id: UUID, updates: dict) -> CognitiveEntry:
    """Updates an existing entry."""
    response = supabase.table("cognitive_entries").update(updates).eq("id", str(entry_id)).execute()
    return CognitiveEntry(**response.data[0])

def get_entries_by_user(user_id: UUID, mode: str = None, bucket: str = None, limit: int = 20, offset: int = 0):
    """Retrieves entries with filters and pagination."""
    query = supabase.table("cognitive_entries").select("*").eq("user_id", str(user_id))
    
    if mode:
        query = query.eq("cognitive_mode", mode)
    if bucket:
        query = query.eq("bucket", bucket)
        
    response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return [CognitiveEntry(**item) for item in response.data]

def get_weekly_entries(user_id: UUID) -> List[CognitiveEntry]:
    """Get entries from the last 7 days."""
    last_week = (datetime.now() - timedelta(days=7)).isoformat()
    response = supabase.table("cognitive_entries").select("*") \
        .eq("user_id", str(user_id)) \
        .gte("created_at", last_week) \
        .execute()
    return [CognitiveEntry(**item) for item in response.data]

def create_or_get_bucket(user_id: UUID, name: str):
    """Ensures a bucket exists for a user."""
    # First check if exists
    res = supabase.table("buckets").select("*").eq("user_id", str(user_id)).eq("name", name).execute()
    if res.data:
        # Increment count
        supabase.table("buckets").update({"entry_count": res.data[0]["entry_count"] + 1}).eq("id", res.data[0]["id"]).execute()
        return res.data[0]
    
    # Create new
    bucket_data = {"user_id": str(user_id), "name": name, "entry_count": 1}
    insert_res = supabase.table("buckets").insert(bucket_data).execute()
    return insert_res.data[0]

def get_user_buckets(user_id: UUID) -> List[str]:
    """Gets list of bucket names for a user."""
    res = supabase.table("buckets").select("name").eq("user_id", str(user_id)).execute()
    return [item["name"] for item in res.data]
