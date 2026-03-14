#!/usr/bin/env python3
"""Quick manual test of server connectivity"""
import requests
import time

print("Testing server connection...")
endpoints = ["/", "/health", "/docs", "/api/", "/api/process-video"]

for endpoint in endpoints:
    try:
        response = requests.get(f"http://127.0.0.1:8000{endpoint}", timeout=5)
        print(f"✅ {endpoint:<25} Status: {response.status_code}")
    except Exception as e:
        print(f"❌ {endpoint:<25} Error: {str(e)[:50]}")

