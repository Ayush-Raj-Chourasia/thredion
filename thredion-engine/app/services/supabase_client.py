
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import User, CognitiveEntry, Bucket
from app.models.schemas import CognitiveEntryCreate

logger = logging.getLogger(__name__)

def get_or_create_user(phone_number: str) -> User:
    """Finds or creates a user by phone number using SQLAlchemy."""
    phone = ''.join(filter(str.isdigit, phone_number))
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone_number == phone).first()
        if user:
            return user
        
        # Create new user
        user = User(phone_number=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()

def create_entry(user_id: UUID, entry_data: dict) -> CognitiveEntry:
    """Creates a new cognitive entry using SQLAlchemy."""
    db = SessionLocal()
    try:
        entry = CognitiveEntry(user_id=user_id, **entry_data)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        db.close()

def update_entry(entry_id: UUID, updates: dict) -> CognitiveEntry:
    """Updates an existing entry using SQLAlchemy."""
    db = SessionLocal()
    try:
        entry = db.query(CognitiveEntry).filter(CognitiveEntry.id == entry_id).first()
        if not entry:
            raise Exception("Entry not found")
            
        for key, value in updates.items():
            setattr(entry, key, value)
            
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        db.close()

def get_entries_by_user(user_id: UUID, mode: str = None, bucket: str = None, limit: int = 20, offset: int = 0):
    """Retrieves entries with filters and pagination."""
    db = SessionLocal()
    try:
        query = db.query(CognitiveEntry).filter(CognitiveEntry.user_id == user_id)
        if mode:
            query = query.filter(CognitiveEntry.cognitive_mode == mode)
        if bucket:
            query = query.filter(CognitiveEntry.bucket == bucket)
            
        return query.order_by(CognitiveEntry.created_at.desc()).offset(offset).limit(limit).all()
    finally:
        db.close()

def get_weekly_entries(user_id: UUID) -> List[CognitiveEntry]:
    """Get entries from the last 7 days."""
    db = SessionLocal()
    try:
        last_week = datetime.now() - timedelta(days=7)
        return db.query(CognitiveEntry).filter(
            CognitiveEntry.user_id == user_id,
            CognitiveEntry.created_at >= last_week
        ).all()
    finally:
        db.close()

def create_or_get_bucket(user_id: UUID, name: str):
    """Ensures a bucket exists for a user."""
    db = SessionLocal()
    try:
        bucket = db.query(Bucket).filter(Bucket.user_id == user_id, Bucket.name == name).first()
        if bucket:
            bucket.entry_count += 1
            db.commit()
            db.refresh(bucket)
            return bucket
            
        # Create new
        bucket = Bucket(user_id=user_id, name=name, entry_count=1)
        db.add(bucket)
        db.commit()
        db.refresh(bucket)
        return bucket
    finally:
        db.close()

def get_user_buckets(user_id: UUID) -> List[str]:
    """Gets list of bucket names for a user."""
    db = SessionLocal()
    try:
        buckets = db.query(Bucket.name).filter(Bucket.user_id == user_id).all()
        return [b.name for b in buckets]
    finally:
        db.close()

def get_all_users() -> List[User]:
    """Retrieves all registered users."""
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()
