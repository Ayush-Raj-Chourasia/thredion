#!/usr/bin/env python3
"""Generate JWT token for API testing"""

import sys
import os
from datetime import datetime, timedelta, timezone

import jwt

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings

def create_test_token(phone: str) -> str:
    """Create a JWT token for testing."""
    payload = {
        "sub": phone,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

if __name__ == "__main__":
    phone = "9876543210"
    token = create_test_token(phone)
    print(f"✅ Test token created for phone: {phone}")
    print(f"\n📝 Token: {token}")
    print(f"\n💡 Usage:")
    print(f"   curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/...")
    print(f"\n   Or set in Python:")
    print(f"   headers = {{'Authorization': f'Bearer {{token}}'}}")
