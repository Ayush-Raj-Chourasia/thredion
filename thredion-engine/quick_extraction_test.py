#!/usr/bin/env python3
"""
Quick test of content extraction with transcription support
No transcription actually run (takes long time)
Just shows the metadata extraction and what transcription WOULD do
"""

import sys
import os
from pathlib import Path

# Load .env
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from services.extractor import extract_from_url

# Test URLs
TEST_URLS = [
    ("YouTube Shorts", "https://www.youtube.com/shorts/6uDFX9mruLM"),
    ("Instagram Post", "https://www.instagram.com/p/DTfJe3CiVfN/"),
]

print("\n" + "="*80)
print("THREDION ENGINE - CONTENT EXTRACTION TEST")
print("="*80 + "\n")

for name, url in TEST_URLS:
    print(f"\n{'─'*80}")
    print(f"📍 {name}: {url}")
    print(f"{'─'*80}\n")
    
    try:
        result = extract_from_url(url)
        
        print(f"✅ Platform:     {result.platform}")
        print(f"📝 Title:        {result.title[:80]}" + ("..." if len(result.title) > 80 else ""))
        print(f"⏱️  Duration:     {result.duration_seconds} seconds")
        print(f"🎬 Is Video:     {result.is_video}")
        
        print(f"\n📄 EXTRACTED CONTENT ({len(result.content)} chars):")
        print(f"{'─'*80}")
        
        # Show content preview
        content_preview = result.content[:500]
        if len(result.content) > 500:
            content_preview += "..."
        
        print(content_preview)
        
        if result.video_metadata:
            print(f"\n🎥 VIDEO METADATA:")
            for key, value in result.video_metadata.items():
                if value:
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    print(f"   • {key}: {value_str}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}\n")

print("""
🎯 KEY IMPROVEMENTS:
   ✅ API keys are now loaded from .env (not hardcoded)
   ✅ Extraction includes video transcription support
   ✅ Short videos (<5 min) will be transcribed to FULL text
   ✅ Content returned includes actual transcript, not just title
   ✅ Secure: .env is in .gitignore and won't be pushed to GitHub

📋 TO USE WITH YOUR URLs:
   1. Update .env with actual Groq API key (already done)
   2. Run: python real_time_ai_test.py
   3. System will:
      • Extract metadata from URL
      • Download and transcribe audio (if short video)
      • Classify with Groq AI
      • Save full transcript + analysis to database
""")
