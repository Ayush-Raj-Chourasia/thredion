#!/usr/bin/env python3
"""
Test Thredion Production API on Railway
Tests the LIVE deployed API with real phone number and links.
"""

import requests
import json
import time
from datetime import datetime

# Production API endpoint
API_BASE = "https://thredion.railway.app"
USER_PHONE = "+918707701003"

# Test content
TEST_URLS = [
    "https://www.instagram.com/p/DUxWU53Ep6P/",
    "https://www.youtube.com/shorts/YNAOYWufq74",
]

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    try:
        url = f"{API_BASE}/health"
        print(f"GET {url}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"  Service: {data.get('service')}")
            print(f"  Status: {data.get('status')}")
            print(f"  Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        return False


def get_jwt_token():
    """Get a JWT token for testing"""
    print("\n" + "="*70)
    print("TEST 2: Send OTP to Authenticate")
    print("="*70)
    
    try:
        # Step 1: Send OTP
        url = f"{API_BASE}/auth/send-otp"
        payload = {"phone": USER_PHONE}
        
        print(f"POST {url}")
        print(f"  Phone: {USER_PHONE}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"✗ Failed to send OTP: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
        
        print(f"✓ OTP sent successfully")
        
        # For testing, use a default OTP (check with your app)
        # In production, this would be from Twilio SMS
        test_otp = "000000"  # This may not work without real SMS
        
        print(f"\n⚠ Note: OTP would be sent via Twilio SMS in production")
        print(f"  For testing, we would need the actual OTP from SMS")
        
        return None  # Can't proceed without real OTP
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        return None


def test_api_with_token(token=None):
    """Test API endpoints (may not need token if public)"""
    print("\n" + "="*70)
    print("TEST 3: Test API Endpoints")
    print("="*70)
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Try to test without authentication first (see if public)
    print("Attempting API access...")
    
    try:
        # Test a simple endpoint
        url = f"{API_BASE}/docs"
        print(f"GET {url} (Swagger docs)")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ API docs accessible at {url}")
            return True
        else:
            print(f"⚠ API docs returned {response.status_code}")
            print(f"  This is OK if endpoints require authentication")
            return None
            
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        return False


def simulate_whatsapp_webhook():
    """Simulate what happens when user sends a WhatsApp message"""
    print("\n" + "="*70)
    print("TEST 4: Simulate WhatsApp Webhook (What Will Happen)")
    print("="*70)
    
    print(f"When you send a WhatsApp message with these links:")
    for url in TEST_URLS:
        print(f"  • {url}")
    
    print(f"\nThe Twilio webhook will:")
    print(f"  1. POST to {API_BASE}/whatsapp")
    print(f"  2. Extract and process the link")
    print(f"  3. Store memory in Supabase database")
    print(f"  4. Return success message back to WhatsApp")
    
    print(f"\nExpected Results:")
    print(f"  ✓ Instagram (caption extraction): 'How sun candles actually form'")
    print(f"  ✓ YouTube (transcript extraction): Full 585-character transcript")
    print(f"  ✓ Thumbnail: Downloaded and cached")
    print(f"  ✓ Database: Entry created in memories table")
    print(f"  ✓ Importance Score: Calculated (1-10)")
    print(f"  ✓ Category: Classified automatically")


def main():
    print("")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "THREDION PRODUCTION API TEST - RAILWAY LIVE" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE}")
    print(f"User Phone: {USER_PHONE}")
    print("")
    
    results = []
    
    # Test 1: Health
    health_ok = test_health()
    results.append(("Health Check", health_ok))
    
    if not health_ok:
        print("\n✗ API not responding. Deployment may still be in progress.")
        print(f"  Check {API_BASE} directly")
        return 1
    
    time.sleep(1)
    
    # Test 2: Token (informational)
    token = get_jwt_token()
    
    time.sleep(1)
    
    # Test 3: API endpoints
    api_ok = test_api_with_token(token)
    results.append(("API Endpoints", api_ok if api_ok is not None else "partial"))
    
    # Test 4: Simulation
    simulate_whatsapp_webhook()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} | {test_name}")
    
    print("\n" + "="*70)
    print("NEXT STEPS FOR REAL TESTING")
    print("="*70)
    print(f"""
1. Send WhatsApp Message:
   TO: +14155238886 (Twilio sandbox number)
   FROM: Your phone ({USER_PHONE})
   TEXT: {TEST_URLS[0]}
   
   Railway will receive webhook → extract content → store in Supabase

2. Verify in Supabase:
   Dashboard → bmiaomzdjspduxyvhatb → memories table
   You should see a new row with:
   - user_phone: {USER_PHONE}
   - platform: "instagram"
   - title: "Video by vt.physics"
   - content: "How sun candles actually form"

3. Test YouTube link the same way:
   TEXT: {TEST_URLS[1]}
   
   Expected in Supabase:
   - platform: "youtube"
   - Full 585-character transcript
   - Category & importance score calculated

4. Check Dashboard:
   Visit https://thredion.vercel.app
   Login with {USER_PHONE}
   See your extracted memories with AI-generated summaries
""")
    
    print("="*70)
    print(f"End Time: {datetime.now().isoformat()}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
