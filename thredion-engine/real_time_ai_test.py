#!/usr/bin/env python3
"""
Thredion Engine - Real-Time AI Processing Test
Test with actual YouTube Shorts and Instagram URLs using Groq API
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from services.extractor import extract_from_url, ExtractedContent
from services.transcriber import detect_platform, get_video_metadata
from services.llm_processor import process_with_groq, CognitiveStructure
from db.database import SessionLocal, init_db
from db.models import Memory

# Real user-provided URLs
TEST_URLS = {
    "youtube_shorts": "https://www.youtube.com/shorts/6uDFX9mruLM",
    "instagram": "https://www.instagram.com/p/DTfJe3CiVfN/",
}

TEST_PHONE = "9876543210"

async def test_extract_url(name: str, url: str):
    """Extract content from URL"""
    print(f"\n{'='*80}")
    print(f"EXTRACTING: {name}")
    print(f"{'='*80}")
    print(f"URL: {url}\n")
    
    try:
        print(f"⏳ Extracting content...")
        start_time = datetime.now()
        
        result = extract_from_url(url)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Extraction completed in {elapsed:.2f}s\n")
        
        print(f"📊 EXTRACTED DATA:")
        print(f"{'─'*80}")
        print(f"🎬 Platform:          {result.platform}")
        print(f"📝 Title:             {result.title}")
        print(f"⏱️  Duration:          {result.duration_seconds} seconds")
        print(f"🌐 URL:               {result.url}")
        print(f"🖼️  Thumbnail:         {result.thumbnail_url[:60]}..." if len(result.thumbnail_url) > 60 else f"🖼️  Thumbnail:         {result.thumbnail_url}")
        print(f"📄 Content Preview:   {result.content[:100]}..." if len(result.content) > 100 else f"📄 Content:           {result.content}")
        
        if result.video_metadata:
            print(f"\n🎥 VIDEO METADATA:")
            print(f"{'─'*80}")
            if 'uploader' in result.video_metadata:
                print(f"   Uploader:   {result.video_metadata['uploader']}")
            if 'description' in result.video_metadata:
                desc = result.video_metadata['description']
                print(f"   Description: {desc[:80]}..." if len(desc) > 80 else f"   Description: {desc}")
            if 'view_count' in result.video_metadata:
                print(f"   Views:      {result.video_metadata['view_count']:,}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_classify(name: str, content: ExtractedContent):
    """Classify content using Groq AI"""
    print(f"\n{'='*80}")
    print(f"AI CLASSIFICATION: {name}")
    print(f"{'='*80}\n")
    
    try:
        print(f"⏳ Classifying content with Groq AI...")
        start_time = datetime.now()
        
        result = await process_with_groq(
            text=f"{content.title}\n\n{content.content}",
            platform=content.platform,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if not result:
            print(f"❌ Groq returned None (API error)")
            return None
        
        print(f"✅ Classification completed in {elapsed:.2f}s\n")
        
        print(f"🧠 AI RESULTS:")
        print(f"{'─'*80}")
        print(f"🎯 Category:          {result.bucket}")
        print(f"📚 Cognitive Mode:    {result.cognitive_mode}")
        print(f"⚡ Actionability:     {result.actionability_score}/1.0")
        print(f"🎭 Emotional Tone:    {result.emotional_tone}")
        print(f"🔍 Confidence:        {result.confidence_score}/1.0")
        
        if result.key_points:
            print(f"\n📌 KEY POINTS:")
            for i, point in enumerate(result.key_points, 1):
                print(f"   {i}. {point}")
        
        if result.summary:
            print(f"\n📄 AI SUMMARY:")
            print(f"   {result.summary}")
        
        # Convert to dict for database storage
        return {
            'bucket': result.bucket,
            'cognitive_mode': result.cognitive_mode,
            'actionability_score': result.actionability_score,
            'emotional_tone': result.emotional_tone,
            'confidence_score': result.confidence_score,
            'key_points': result.key_points,
            'summary': result.summary,
            'title': result.title,
            'tags': result.tags,
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_save_to_db(name: str, content: ExtractedContent, classification: dict):
    """Save to database"""
    print(f"\n{'='*80}")
    print(f"SAVING TO DATABASE: {name}")
    print(f"{'='*80}\n")
    
    try:
        print(f"⏳ Creating database record...")
        
        init_db()
        db = SessionLocal()
        
        memory = Memory(
            url=content.url,
            platform=content.platform,
            user_phone=TEST_PHONE,
            title=classification.get('title', content.title),
            content=content.content,
            transcript=classification.get('summary', ''),
            transcript_length=len(classification.get('summary', '')),
            transcript_source="groq",
            video_duration=content.duration_seconds,
            is_video=True,
            cognitive_mode=classification.get('cognitive_mode', 'learn'),
            bucket=classification.get('bucket', 'Uncategorized'),
            actionability_score=float(classification.get('actionability_score', 0)),
            confidence_score=float(classification.get('confidence_score', 0)),
            emotional_tone=classification.get('emotional_tone', ''),
            key_points=json.dumps(classification.get('key_points', [])),
            title_generated=classification.get('title', content.title),
            thumbnail_url=content.thumbnail_url,
        )
        
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        print(f"✅ Record created: ID {memory.id}\n")
        
        print(f"💾 DATABASE RECORD:")
        print(f"{'─'*80}")
        print(f"ID:                   {memory.id}")
        print(f"URL:                  {memory.url}")
        print(f"Platform:             {memory.platform}")
        print(f"User:                 {memory.user_phone}")
        print(f"Title:                {memory.title}")
        print(f"Cognitive Mode:       {memory.cognitive_mode}")
        print(f"Bucket:               {memory.bucket}")
        print(f"Actionability Score:  {memory.actionability_score}")
        print(f"Confidence:           {memory.confidence_score}")
        print(f"Created:              {memory.created_at}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  THREDION ENGINE - REAL-TIME AI PROCESSING TEST".center(78) + "║")
    print("║" + "  YouTube Shorts + Instagram Content Processing".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Check if API key is set
    if not os.getenv('GROQ_API_KEY'):
        print("\n❌ ERROR: GROQ_API_KEY not set in environment")
        print("\n📋 To set it up:")
        print("   1. Create a .env file in this directory")
        print("   2. Add: GROQ_API_KEY=your_key_here")
        print("   3. Get your key from: https://console.groq.com/keys")
        return
    
    print(f"\n📌 CONFIGURATION")
    print(f"{'─'*80}")
    print(f"Groq API:             ✅ Configured")
    print(f"Test User Phone:      {TEST_PHONE}")
    print(f"URLs to Test:         {len(TEST_URLS)}")
    print(f"Test Timestamp:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Process each URL
    for test_name, url in TEST_URLS.items():
        print(f"\n\n{'#'*80}")
        print(f"# {test_name.upper()}")
        print(f"{'#'*80}")
        
        # Extract content
        content = await test_extract_url(test_name, url)
        
        if content:
            # Classify with AI
            classification = await test_classify(test_name, content)
            
            if classification:
                # Save to database
                saved = await test_save_to_db(test_name, content, classification)
                
                results[test_name] = {
                    "extracted": True,
                    "classified": True,
                    "saved": saved,
                    "url": url,
                    "platform": content.platform,
                    "title": content.title,
                }
            else:
                results[test_name] = {
                    "extracted": True,
                    "classified": False,
                    "saved": False,
                    "error": "Classification failed",
                }
        else:
            results[test_name] = {
                "extracted": False,
                "classified": False,
                "saved": False,
                "error": "Extraction failed",
            }
    
    # Summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}\n")
    
    for test_name, result in results.items():
        status = "✅" if result.get("saved") else "⚠️"
        print(f"{status} {test_name.upper()}")
        print(f"   Extracted:     {'✅' if result['extracted'] else '❌'}")
        print(f"   Classified:    {'✅' if result['classified'] else '❌'}")
        print(f"   Saved to DB:   {'✅' if result['saved'] else '❌'}")
        if 'platform' in result:
            print(f"   Platform:      {result['platform']}")
        if 'error' in result:
            print(f"   Error:         {result['error']}")
        print()
    
    all_success = all(r.get("saved") for r in results.values())
    
    print(f"{'='*80}")
    if all_success:
        print("🎉 ALL TESTS PASSED - SYSTEM OPERATIONAL")
    else:
        print("⚠️  SOME TESTS ENCOUNTERED ISSUES - CHECK ABOVE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
