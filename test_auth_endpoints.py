#!/usr/bin/env python3
"""Test auth endpoints on Railway"""

import requests
import json

API_BASE = "https://thredion.railway.app"

print("=" * 60)
print("TESTING AUTH ENDPOINTS ON RAILWAY")
print("=" * 60)

# Test 1: Health
print("\n[Test 1] GET /health")
response = requests.get(f"{API_BASE}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 2: Root
print("\n[Test 2] GET /")
response = requests.get(f"{API_BASE}/")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 3: OpenAPI /openapi.json
print("\n[Test 3] GET /openapi.json")
response = requests.get(f"{API_BASE}/openapi.json")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Paths available: {list(data.get('paths', {}).keys())[:10]}")

# Test 4: /docs (OpenAPI UI)
print("\n[Test 4] GET /docs")
response = requests.get(f"{API_BASE}/docs")
print(f"Status: {response.status_code}")

# Test 5: Send OTP
print("\n[Test 5] POST /auth/send-otp")
payload = {"phone": "+918707701003"}
response = requests.post(f"{API_BASE}/auth/send-otp", json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:300]}")

# Test 6: Verify OTP
print("\n[Test 6] POST /auth/verify-otp")
payload = {"phone": "+918707701003", "code": "000000"}
response = requests.post(f"{API_BASE}/auth/verify-otp", json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:300]}")

# Test 7: Get me
print("\n[Test 7] GET /auth/me")
response = requests.get(f"{API_BASE}/auth/me")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:300]}")

print("\n" + "=" * 60)
print("Auth endpoint testing complete")
print("=" * 60)
