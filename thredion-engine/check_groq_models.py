#!/usr/bin/env python3
"""Test available Groq models"""

import os
from pathlib import Path
from groq import Groq

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    print("❌ ERROR: GROQ_API_KEY not set in environment")
    print("\n📋 To set it up:")
    print("   1. Create a .env file in this directory")
    print("   2. Add: GROQ_API_KEY=your_key_here")
    print("   3. Get your key from: https://console.groq.com/keys")
    exit(1)

client = Groq(api_key=api_key)

print("🔍 Checking available Groq models...\n")

try:
    models = client.models.list()
    print(f"✅ Found {len(models.data)} available models:\n")
    for model in models.data:
        print(f"   • {model.id}")
except Exception as e:
    print(f"❌ Error: {e}")
