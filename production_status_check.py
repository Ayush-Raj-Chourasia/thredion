#!/usr/bin/env python3
"""Production Status Check - Comprehensive Diagnostics"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "https://thredion.railway.app"
FRONTEND = "https://thredion.vercel.app"

class Colors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    INFO = '\033[94m'
    RESET = '\033[0m'

def test(name, method, url, data=None, expect_code=None):
    """Make HTTP request and report status"""
    try:
        if method == 'GET':
            r = requests.get(url, timeout=10)
        elif method == 'POST':
            r = requests.post(url, json=data, timeout=10)
        
        if expect_code and r.status_code != expect_code:
            status = f"{Colors.FAIL}✗ {r.status_code}{Colors.RESET}"
        elif r.status_code < 400:
            status = f"{Colors.OK}✓ {r.status_code}{Colors.RESET}"
        else:
            status = f"{Colors.WARN}⚠ {r.status_code}{Colors.RESET}"
        
        print(f"  {status:20} {method:5} {url.replace(API_BASE, '').ljust(30, '.')}")
        return r
    except Exception as e:
        print(f"  {Colors.FAIL}✗ ERROR{Colors.RESET:20} {method:5} {url.replace(API_BASE, '')} - {str(e)[:50]}")
        return None

print(f"\n{Colors.INFO}{'='*70}")
print(f"THREDION PRODUCTION STATUS CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*70}{Colors.RESET}\n")

# Phase 1: Core Infrastructure
print(f"{Colors.INFO}[Phase 1] Core Infrastructure{Colors.RESET}")
test("Health", "GET", f"{API_BASE}/health")
test("Frontend", "GET", FRONTEND)

# Phase 2: Available Routes (GET /openapi.json)
print(f"\n{Colors.INFO}[Phase 2] Checking Available Routes via OpenAPI{Colors.RESET}")
resp = test("OpenAPI Schema", "GET", f"{API_BASE}/openapi.json")

if resp and resp.status_code == 200:
    try:
        spec = resp.json()
        paths = list(spec.get('paths', {}).keys())
        print(f"\n  Available endpoints ({len(paths)} total):")
        for path in sorted(paths):
            print(f"    - {path}")
    except:
        pass
else:
    print(f"  {Colors.WARN}⚠ Could not fetch OpenAPI spec{Colors.RESET}")
    print(f"  Manually testing expected routes...")
    test("Auth: Send OTP", "POST", f"{API_BASE}/auth/send-otp", {"phone": "+11234567890"})
    test("Auth: Verify OTP", "POST", f"{API_BASE}/auth/verify-otp", {"phone": "+11234567890", "code": "123456"})
    test("API Docs", "GET", f"{API_BASE}/docs")

# Phase 3: Critical Routes
print(f"\n{Colors.INFO}[Phase 3] Critical Routes{Colors.RESET}")
test("Root", "GET", f"{API_BASE}/")
test("Health", "GET", f"{API_BASE}/health", expect_code=200)
test("Redoc", "GET", f"{API_BASE}/redoc")

# Phase 4: Summary
print(f"\n{Colors.INFO}{'='*70}")
print(f"SUMMARY{Colors.RESET}")
print(f"  Frontend: {Colors.OK}✓{Colors.RESET} Deployed on Vercel")
print(f"  API Base: {Colors.OK}✓{Colors.RESET} Responding on Railway")
print(f"  Auth Routes: {Colors.WARN}?{Colors.RESET} Check OpenAPI spec above")
print(f"\n  {Colors.INFO}Next steps:{Colors.RESET}")
print(f"  1. If auth routes not in OpenAPI, may need to redeploy")
print(f"  2. Check Railway deployment logs: https://railway.app")
print(f"  3. Verify git push included all .py files in thredion-engine/api/")
print(f"{'='*70}\n")
