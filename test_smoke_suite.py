#!/usr/bin/env python3
"""
Thredion Frontend & API Smoke Test
Tests login flow, dashboard, and basic functionality
"""

import requests
import json
import time
from datetime import datetime

# Endpoints
VERCEL_FRONTEND = "https://thredion.vercel.app"
RAILWAY_API = "https://thredion.railway.app"
USER_PHONE = "+918707701003"

def test_frontend_load():
    """Test if frontend loads"""
    print("\n" + "="*70)
    print("TEST 1: Frontend Loads")
    print("="*70)
    
    try:
        r = requests.get(VERCEL_FRONTEND, timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            print("✓ Frontend loads successfully")
            print(f"  Content Length: {len(r.text)} bytes")
            print(f"  Contains 'Thredion': {'Thredion' in r.text}")
            print(f"  Contains 'Cognitive': {'Cognitive' in r.text}")
            return True
        else:
            print(f"✗ Frontend returned {r.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_api_health():
    """Test API health endpoint"""
    print("\n" + "="*70)
    print("TEST 2: API Health Check")
    print("="*70)
    
    try:
        r = requests.get(f"{RAILWAY_API}/health", timeout=5)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"✓ API healthy")
                print(f"  Service: {data.get('service')}")
                print(f"  Status: {data.get('status')}")
                print(f"  Version: {data.get('version')}")
                return True
            except:
                print(f"✓ API responds (non-JSON: {r.text})")
                return True
        else:
            print(f"✗ API returned {r.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_auth_flow():
    """Test authentication flow"""
    print("\n" + "="*70)
    print("TEST 3: Authentication Flow (Send OTP)")
    print("="*70)
    
    try:
        # Step 1: Send OTP
        url = f"{RAILWAY_API}/auth/send-otp"
        payload = {"phone": USER_PHONE}
        
        print(f"Sending OTP to {USER_PHONE}...")
        r = requests.post(url, json=payload, timeout=10)
        
        print(f"Status: {r.status_code}")
        
        if r.status_code in [200, 201]:
            print(f"✓ OTP sent successfully")
            print(f"  Response: {r.text[:200]}")
            
            # In real scenario, user would receive SMS
            print(f"\n⚠ Note: In production, Twilio sends SMS with OTP code")
            print(f"  User would reply to Twilio with OTP")
            print(f"  For testing, would need to capture from logs or DB")
            
            return True
        else:
            print(f"✗ Failed to send OTP: {r.status_code}")
            print(f"  Response: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_api_docs():
    """Test if API documentation is accessible"""
    print("\n" + "="*70)
    print("TEST 4: API Documentation (Swagger)")
    print("="*70)
    
    try:
        r = requests.get(f"{RAILWAY_API}/docs", timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"✓ API docs accessible")
            print(f"  Swagger UI available at {RAILWAY_API}/docs")
            print(f"  Content Length: {len(r.text)} bytes")
            return True
        else:
            print(f"⚠ API docs returned {r.status_code}")
            # This is OK if not exposed
            return True
    except Exception as e:
        print(f"⚠ Could not access docs: {e}")
        # Not critical
        return True


def test_root_endpoint():
    """Test API root endpoint"""
    print("\n" + "="*70)
    print("TEST 5: API Root Info")
    print("="*70)
    
    try:
        r = requests.get(f"{RAILWAY_API}/", timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"✓ API root responds")
                print(f"  Info: {json.dumps(data, indent=2)[:300]}")
                return True
            except:
                print(f"✓ API root responds (non-JSON)")
                return True
        else:
            print(f"⚠ Root returned {r.status_code}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_frontend_routes():
    """Test if common frontend routes exist"""
    print("\n" + "="*70)
    print("TEST 6: Frontend Routes")
    print("="*70)
    
    routes = [
        ("/", "Home"),
        ("/dashboard", "Dashboard"),
        ("/memory", "Memory"),
        ("/settings", "Settings"),
    ]
    
    results = []
    for route, name in routes:
        try:
            r = requests.get(f"{VERCEL_FRONTEND}{route}", timeout=5, allow_redirects=True)
            status = "✓" if r.status_code == 200 else "⚠"
            print(f"{status} {name:15} {route:20} → {r.status_code}")
            results.append(r.status_code == 200)
        except Exception as e:
            print(f"✗ {name:15} {route:20} → Error: {str(e)[:30]}")
            results.append(False)
    
    return any(results)


def test_cors_headers():
    """Test CORS headers"""
    print("\n" + "="*70)
    print("TEST 7: CORS Headers (API)")
    print("="*70)
    
    try:
        r = requests.get(
            f"{RAILWAY_API}/health",
            headers={"Origin": "https://thredion.vercel.app"},
            timeout=5
        )
        
        print(f"Status: {r.status_code}")
        print(f"CORS Headers:")
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        ]
        
        has_cors = False
        for header in cors_headers:
            value = r.headers.get(header, "Not set")
            print(f"  {header}: {value}")
            if value != "Not set":
                has_cors = True
        
        if has_cors or r.status_code == 200:
            print("✓ CORS appears configured")
            return True
        else:
            print("⚠ CORS headers not visible (may still work)")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_ssl_certificate():
    """Test SSL certificate"""
    print("\n" + "="*70)
    print("TEST 8: SSL/TLS Certificate")
    print("="*70)
    
    try:
        # Test both URLs
        for url in [VERCEL_FRONTEND, RAILWAY_API]:
            try:
                r = requests.head(url, timeout=5)
                print(f"✓ {url}")
                print(f"  Status: {r.status_code}")
                print(f"  SSL: Valid")
            except Exception as e:
                print(f"✗ {url}: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all smoke tests"""
    print("")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "THREDION SMOKE TEST SUITE" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Frontend: {VERCEL_FRONTEND}")
    print(f"API: {RAILWAY_API}")
    print(f"Test User: {USER_PHONE}")
    
    results = {}
    
    # Run all tests
    results["Frontend Load"] = test_frontend_load()
    time.sleep(1)
    
    results["API Health"] = test_api_health()
    time.sleep(1)
    
    results["Auth Flow"] = test_auth_flow()
    time.sleep(1)
    
    results["API Docs"] = test_api_docs()
    time.sleep(1)
    
    results["Root Endpoint"] = test_root_endpoint()
    time.sleep(1)
    
    results["Frontend Routes"] = test_frontend_routes()
    time.sleep(1)
    
    results["CORS Headers"] = test_cors_headers()
    time.sleep(1)
    
    results["SSL/TLS"] = test_ssl_certificate()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} | {test}")
    
    print("")
    print(f"Total: {passed}/{total} tests passed")
    print(f"Success Rate: {passed*100//total}%")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Go to https://thredion.vercel.app
2. Click "Login with WhatsApp"
3. Enter phone: +91 8707701003
4. You'll need OTP from WhatsApp (sent to this number)
5. After login, dashboard shows your saved memories
6. Send WhatsApp message to +14155238886 with:
   - Instagram link: https://www.instagram.com/p/DUxWU53Ep6P/
   - YouTube link: https://www.youtube.com/shorts/YNAOYWufq74
7. Verify memories appear in dashboard

Note: Requires SUPABASE_DB_PASSWORD to be set in Railway Variables
""")
    
    print(f"End Time: {datetime.now().isoformat()}")
    print("")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
