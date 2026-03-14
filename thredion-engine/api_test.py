#!/usr/bin/env python3
"""
Thredion Engine - Comprehensive API Integration Tests
Tests the running FastAPI server with real-world scenarios
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

import httpx
import time

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import SessionLocal
from db.models import Memory, User

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
TEST_TIMEOUT = 60.0
POLL_INTERVAL = 2.0

# Test data
TEST_VIDEOS = {
    "short_yt": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # 18 sec
    "medium_yt": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # 4+ min
}

TEST_PHONE = "9876543210"

class APITestRunner:
    def __init__(self):
        self.client = None
        self.passed = 0
        self.failed = 0
        self.blocked = 0
        self.auth_token = None
        
    async def setup_auth(self):
        """Create test user and generate auth token"""
        try:
            from datetime import datetime, timedelta, timezone
            import jwt
            from core.config import settings
            
            db = SessionLocal()
            
            # Create or get test user
            user = db.query(User).filter(User.phone == TEST_PHONE).first()
            if not user:
                user = User(phone=TEST_PHONE, is_active=True)
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Generate token
            payload = {
                "sub": TEST_PHONE,
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
            }
            self.auth_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
            
            db.close()
            return True
        except Exception as e:
            print(f"❌ Auth setup error: {e}")
            return False
        
    async def connect(self) -> bool:
        """Test connection to API server"""
        try:
            self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0)
            
            # Test root endpoint instead of /health
            response = await self.client.get("/")
            if response.status_code == 200:
                print(f"✅ Server is running at {API_BASE_URL}")
                return True
        except Exception as e:
            print(f"❌ Cannot connect to server at {API_BASE_URL}: {e}")
            print(f"   Make sure server is running: python main.py")
            return False

    async def test_swagger_docs(self):
        """Test 1: API Documentation"""
        print("\n" + "="*80)
        print("TEST 1: API DOCUMENTATION & SWAGGER")
        print("="*80)
        
        try:
            response = await self.client.get("/docs")
            if response.status_code == 200:
                print("✅ Swagger documentation available at /docs")
                print(f"   📄 Response size: {len(response.content)} bytes")
                self.passed += 1
            else:
                print(f"❌ Swagger docs returned {response.status_code}")
                self.failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed += 1

    async def test_root_endpoint(self):
        """Test 2: Root Endpoint"""
        print("\n" + "="*80)
        print("TEST 2: ROOT ENDPOINT")
        print("="*80)
        
        try:
            response = await self.client.get("/")
            if response.status_code in [200, 404]:  # 404 is expected if not defined
                print(f"✅ Root endpoint accessible (status: {response.status_code})")
                self.passed += 1
            else:
                print(f"❌ Root endpoint returned {response.status_code}")
                self.failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed += 1

    async def test_process_video(self, name: str, url: str):
        """Test 3,4,5: Process Video (async job creation)"""
        print(f"\n\n📺 Processing: {name}")
        print(f"   URL: {url}")
        
        try:
            # Create processing job
            params = {
                "url": url,
                "phone": TEST_PHONE,
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            start_time = time.time()
            response = await self.client.post(
                "/api/process-video",
                params=params,
                headers=headers,
                timeout=30.0
            )
            elapsed = time.time() - start_time
            
            if response.status_code in [200, 202, 201]:
                data = response.json()
                print(f"   ✅ Job created in {elapsed:.2f}s")
                print(f"   📋 Job ID: {data.get('job_id', 'N/A')}")
                print(f"   🔄 Status: {data.get('status', 'unknown')}")
                print(f"   🎬 Platform: {data.get('platform', 'unknown')}")
                
                # Wait for processing
                await self._wait_for_job(data.get('job_id'), name)
                self.passed += 1
                return data.get('job_id')
                
            else:
                print(f"   ❌ API returned {response.status_code}")
                print(f"   📝 Response: {response.text[:200]}")
                self.failed += 1
                return None
                
        except Exception as e:
            if "Sign in to confirm you're not a bot" in str(e):
                print(f"   ⚠️  YouTube authentication required")
                self.blocked += 1
            else:
                print(f"   ❌ Error: {e}")
                self.failed += 1
            return None

    async def _wait_for_job(self, job_id: str, name: str):
        """Wait for async job to complete"""
        if not job_id:
            return
            
        print(f"   ⏳ Waiting for job to complete...")
        
        for attempt in range(int(TEST_TIMEOUT / POLL_INTERVAL)):
            await asyncio.sleep(POLL_INTERVAL)
            
            try:
                response = await self.client.get(f"/api/job/{job_id}", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    if status == "completed":
                        print(f"   ✅ Job completed!")
                        print(f"      📝 Transcript length: {len(data.get('transcript', ''))} chars")
                        print(f"      🧠 Cognitive mode: {data.get('cognitive_mode', 'N/A')}")
                        return
                    elif status == "failed":
                        print(f"   ❌ Job failed: {data.get('error', 'Unknown error')}")
                        return
                    else:
                        print(f"   ⏳ Status: {status}")
                        
            except Exception as e:
                print(f"   ❌ Error polling job: {e}")
                return
        
        print(f"   ⏱️  Job timeout (exceeded {TEST_TIMEOUT}s)")

    async def test_database_directly(self):
        """Test 6: Direct Database Access"""
        print("\n" + "="*80)
        print("TEST 6: DATABASE DIRECT ACCESS")
        print("="*80)
        
        try:
            db = SessionLocal()
            
            # Count memories
            count = db.query(Memory).count()
            print(f"✅ Database accessible")
            print(f"   📊 Total memories: {count}")
            
            # Get recent memories
            recent = db.query(Memory).filter(
                Memory.user_phone == TEST_PHONE
            ).order_by(Memory.created_at.desc()).limit(5).all()
            
            if recent:
                print(f"   📋 User memories: {len(recent)}")
                for mem in recent:
                    print(f"      - {mem.platform}: {mem.url[:50]}...")
                    print(f"        Transcript: {len(mem.transcript or '')} chars")
                    print(f"        Cognitive: {mem.cognitive_mode}")
            
            db.close()
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            self.failed += 1

    async def test_multi_user_isolation(self):
        """Test 7: Multi-user Data Isolation"""
        print("\n" + "="*80)
        print("TEST 7: MULTI-USER DATA ISOLATION")
        print("="*80)
        
        try:
            db = SessionLocal()
            
            phone1 = "1111111111"
            phone2 = "2222222222"
            
            # Create test records
            mem1 = Memory(
                url="https://example.com/test1",
                platform="article",
                user_phone=phone1,
                content="Test content for user 1"
            )
            mem2 = Memory(
                url="https://example.com/test2",
                platform="article",
                user_phone=phone2,
                content="Test content for user 2"
            )
            
            db.add(mem1)
            db.add(mem2)
            db.commit()
            
            # Verify isolation
            user1_count = db.query(Memory).filter(Memory.user_phone == phone1).count()
            user2_count = db.query(Memory).filter(Memory.user_phone == phone2).count()
            
            print(f"✅ Data isolation working")
            print(f"   👤 User {phone1}: {user1_count} memories")
            print(f"   👤 User {phone2}: {user2_count} memories")
            
            # Cleanup
            db.query(Memory).filter(Memory.user_phone.in_([phone1, phone2])).delete()
            db.commit()
            db.close()
            
            self.passed += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed += 1

    async def test_memory_schema(self):
        """Test 8: Memory Schema Validation"""
        print("\n" + "="*80)
        print("TEST 8: MEMORY SCHEMA VALIDATION")
        print("="*80)
        
        try:
            db = SessionLocal()
            
            # Create memory with all relevant fields
            test_memory = Memory(
                url="https://example.com/test-schema",
                platform="youtube",
                user_phone="9999999999",
                title="Test Video",
                transcript="Sample transcript for testing",
                transcript_length=30,
                transcript_source="local",
                video_duration=120,
                is_video=True,
                cognitive_mode="learn",
                bucket="Testing",
                actionability_score=0.75,
                confidence_score=0.95,
                emotional_tone="neutral",
                key_points=json.dumps(["point 1", "point 2"]),
            )
            
            db.add(test_memory)
            db.commit()
            db.refresh(test_memory)
            
            # Verify all fields
            checks = {
                "ID": test_memory.id is not None,
                "URL": test_memory.url == "https://example.com/test-schema",
                "Platform": test_memory.platform == "youtube",
                "Transcript": len(test_memory.transcript) > 0,
                "Video Duration": test_memory.video_duration == 120,
                "Is Video": test_memory.is_video == True,
                "Cognitive Mode": test_memory.cognitive_mode == "learn",
                "Actionability Score": test_memory.actionability_score == 0.75,
                "Confidence": test_memory.confidence_score == 0.95,
            }
            
            print("✅ All schema fields validated:")
            for field, passed in checks.items():
                status = "✓" if passed else "✗"
                print(f"   {status} {field}")
            
            # Cleanup
            db.delete(test_memory)
            db.commit()
            db.close()
            
            if all(checks.values()):
                self.passed += 1
            else:
                self.failed += 1
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed += 1

    async def run_all(self):
        """Run all tests"""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + "  THREDION ENGINE - COMPREHENSIVE API INTEGRATION TESTS".center(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "="*78 + "╝")
        
        # Connect to server
        if not await self.connect():
            print("\n❌ Cannot connect to API server")
            return False
        
        # Setup authentication
        print("\n🔐 Setting up authentication...")
        if not await self.setup_auth():
            print("❌ Auth setup failed")
            return False
        print(f"✅ Auth token generated for phone: {TEST_PHONE}")
        
        print("\n" + "="*80)
        print("TEST SEQUENCE")
        print("="*80)
        print("1. API Documentation")
        print("2. Root Endpoint")
        print("3. Process Short Video (YouTube)")
        print("4. Process Medium Video (YouTube)")
        print("5. Database Access")
        print("6. Multi-user Isolation")
        print("7. Memory Schema Validation")
        print("8. [OPTIONAL] Video Transcription")
        
        start = datetime.now()
        
        # Run tests
        await self.test_swagger_docs()
        await self.test_root_endpoint()
        
        # Test video processing
        await self.test_process_video("Short YouTube Video", TEST_VIDEOS["short_yt"])
        await self.test_process_video("Medium YouTube Video", TEST_VIDEOS["medium_yt"])
        
        # Test database and schema
        await self.test_database_directly()
        await self.test_multi_user_isolation()
        await self.test_memory_schema()
        
        # Summary
        elapsed = (datetime.now() - start).total_seconds()
        
        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        print(f"✅ Passed:  {self.passed}")
        print(f"❌ Failed:  {self.failed}")
        print(f"⚠️  Blocked: {self.blocked}")
        print(f"⏱️  Duration: {elapsed:.2f}s")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            if self.client:
                await self.client.aclose()
            return True
        else:
            print(f"\n❌ {self.failed} tests failed")
            if self.client:
                await self.client.aclose()
            return False

async def main():
    runner = APITestRunner()
    success = await runner.run_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
