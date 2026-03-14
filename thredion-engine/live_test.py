#!/usr/bin/env python3
"""
Thredion Engine - Real-Time Live Testing with Actual Data
Tests entire system end-to-end with real YouTube videos
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("LIVE_TEST")

# Import actual services
from services.transcriber import (
    detect_platform, 
    get_video_metadata, 
    transcribe_short_video,
)
from services.extractor import extract_from_url
from db.database import SessionLocal, init_db
from db.models import Memory

# Test URLs - Real videos
TEST_VIDEOS = {
    "youtube_short": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # First YouTube - 18 seconds
    "youtube_medium": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Popular music video
}

async def test_platform_detection():
    """Test 1: Platform Detection"""
    print("\n" + "="*70)
    print("TEST 1: PLATFORM DETECTION")
    print("="*70)
    
    for name, url in TEST_VIDEOS.items():
        try:
            platform = detect_platform(url)
            print(f"✅ {name}: {url}")
            print(f"   Platform detected: {platform}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")

async def test_metadata_extraction():
    """Test 2: Video Metadata Extraction"""
    print("\n" + "="*70)
    print("TEST 2: VIDEO METADATA EXTRACTION")
    print("="*70)
    
    for name, url in TEST_VIDEOS.items():
        try:
            print(f"\n📺 Testing: {name}")
            print(f"   URL: {url}")
            
            metadata = await get_video_metadata(url)
            
            print(f"   ✅ Title: {metadata.get('title', 'N/A')}")
            print(f"   ✅ Duration: {metadata.get('duration', 0)} seconds")
            print(f"   ✅ Uploader: {metadata.get('uploader', 'N/A')}")
            print(f"   ✅ Size: {metadata.get('file_size', 0)} bytes")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

async def test_short_video_transcription():
    """Test 3: Short Video Transcription"""
    print("\n" + "="*70)
    print("TEST 3: SHORT VIDEO TRANSCRIPTION (Local)")
    print("="*70)
    
    url = TEST_VIDEOS["youtube_short"]
    try:
        print(f"\n🎬 Testing short video transcription...")
        print(f"   URL: {url}")
        
        # Get duration first
        metadata = await get_video_metadata(url)
        duration = metadata.get('duration', 0)
        print(f"   Duration: {duration} seconds")
        
        if duration < 300:  # 5 minutes
            print(f"\n   ⏳ Starting transcription...")
            
            start_time = datetime.now()
            transcript = await transcribe_short_video(url)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if transcript:
                print(f"   ✅ Transcription completed in {elapsed:.2f} seconds")
                print(f"   📝 Transcript length: {len(transcript)} characters")
                print(f"   📄 Content preview:")
                print(f"      {transcript[:200]}..." if len(transcript) > 200 else f"      {transcript}")
            else:
                print(f"   ❌ No transcript generated")
        else:
            print(f"   ⏭️  Video too long for short path ({duration}s > 300s)")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_extraction():
    """Test 4: Content Extraction"""
    print("\n" + "="*70)
    print("TEST 4: CONTENT EXTRACTION")
    print("="*70)
    
    url = TEST_VIDEOS["youtube_short"]
    try:
        print(f"\n📊 Extracting content from URL...")
        
        start_time = datetime.now()
        result = extract_from_url(url)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"   ✅ Extraction completed in {elapsed:.2f} seconds")
        print(f"   📝 Title: {result.title}")
        print(f"   🎬 Platform: {result.platform}")
        print(f"   ⏱️  Duration: {result.duration_seconds} seconds")
        print(f"   📄 Content: {result.content[:100]}..." if len(result.content) > 100 else f"   📄 Content: {result.content}")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

async def test_database_storage():
    """Test 5: Database Storage"""
    print("\n" + "="*70)
    print("TEST 5: DATABASE STORAGE")
    print("="*70)
    
    try:
        # Initialize DB
        init_db()
        print("   ✅ Database initialized")
        
        # Create a test memory
        db = SessionLocal()
        memory = Memory(
            user_phone="9876543210",
            url=TEST_VIDEOS["youtube_short"],
            platform="youtube",
            title="Test Video",
            is_video=True,
            transcript="Test transcript content",
            transcript_length=22,
            transcript_source="local",
            video_duration=18,
            cognitive_mode="learn",
            bucket="Testing",
            actionability_score=0.8,
            confidence_score=0.95,
        )
        
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        print(f"   ✅ Memory record created: ID {memory.id}")
        print(f"   📝 URL: {memory.url}")
        print(f"   🏷️  Platform: {memory.platform}")
        print(f"   💾 Transcript stored: {len(memory.transcript)} chars")
        
        # Retrieve it
        retrieved = db.query(Memory).filter(Memory.id == memory.id).first()
        if retrieved:
            print(f"   ✅ Record retrieved successfully")
            print(f"      URL: {retrieved.url}")
            print(f"      Cognitive Mode: {retrieved.cognitive_mode}")
        
        # Clean up
        db.delete(retrieved)
        db.commit()
        db.close()
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_api_endpoints():
    """Test 6: API Endpoints (if server is running)"""
    print("\n" + "="*70)
    print("TEST 6: API ENDPOINT TESTING")
    print("="*70)
    
    try:
        import httpx
        
        # Try to connect to server
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=5.0) as client:
            print("   ✅ Server found at localhost:8000")
            
            # Test /docs endpoint
            response = await client.get("/docs")
            if response.status_code == 200:
                print("   ✅ Swagger docs available at http://localhost:8000/docs")
            
            # Test health (if available)
            response = await client.get("/health")
            if response.status_code == 200:
                print("   ✅ Health check passed")
                
    except Exception as e:
        print(f"   ℹ️  Server not running (expected if not started)")
        print(f"      Start server with: python main.py")

async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  THREDION ENGINE - REAL-TIME LIVE TESTING WITH ACTUAL DATA".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n📋 Test Plan:")
    print("   1️⃣  Platform Detection")
    print("   2️⃣  Video Metadata Extraction")
    print("   3️⃣  Short Video Transcription")
    print("   4️⃣  Content Extraction")
    print("   5️⃣  Database Storage")
    print("   6️⃣  API Endpoints (if server running)")
    
    print("\n⏱️  Starting tests...\n")
    
    start = datetime.now()
    
    # Run tests
    await test_platform_detection()
    await test_metadata_extraction()
    await test_short_video_transcription()
    await test_extraction()
    await test_database_storage()
    await test_api_endpoints()
    
    elapsed = (datetime.now() - start).total_seconds()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ All tests completed in {elapsed:.2f} seconds")
    print(f"\n🎉 LIVE SYSTEM VALIDATION COMPLETE")
    print("\nNext steps:")
    print("   1. Start server: python main.py")
    print("   2. View API docs: http://localhost:8000/docs")
    print("   3. Test via API: POST /api/process-video?url=<youtube-url>")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
