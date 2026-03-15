#!/usr/bin/env python3
"""
Test Thredion API with Real Phone Number and Links
Simulates what happens when a user sends links via WhatsApp.
"""

import sys
import os
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add thredion-engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'thredion-engine'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("test_api_pipeline")

# Real test data
USER_PHONE = "+918707701003"  # Your phone number
TEST_LINKS = [
    "https://www.instagram.com/p/DUxWU53Ep6P/",
    "https://www.youtube.com/shorts/YNAOYWufq74",
]


def setup_database():
    """Setup in-memory SQLite database for testing"""
    logger.info("Setting up test database...")
    
    # Import models to register them with Base
    from db.models import User, OTPCode, Memory, Connection, ResurfacedMemory  # noqa: F401
    from db.database import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables from models
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")
    
    SessionLocal_test = sessionmaker(bind=engine)
    
    return engine, SessionLocal_test()


def test_process_url(db, url: str):
    """Test process_url function with a real URL"""
    logger.info(f"\n{'─' * 70}")
    logger.info(f"Processing: {url}")
    logger.info(f"{'─' * 70}")
    
    try:
        from services.pipeline import process_url
        
        logger.info("→ Starting pipeline...")
        start = datetime.now()
        
        result = process_url(url, USER_PHONE, db)
        
        elapsed = (datetime.now() - start).total_seconds()
        
        logger.info(f"✓ Pipeline complete in {elapsed:.2f}s")
        logger.info(f"  Memory ID: {result.get('memory_id')}")
        logger.info(f"  Platform: {result.get('platform')}")
        logger.info(f"  Title: {result.get('title')[:60]}..." if len(str(result.get('title', ''))) > 60 else f"  Title: {result.get('title')}")
        logger.info(f"  Summary: {result.get('summary')[:80]}..." if len(str(result.get('summary', ''))) > 80 else f"  Summary: {result.get('summary')}")
        logger.info(f"  Category: {result.get('category')}")
        logger.info(f"  Tags: {result.get('tags')}")
        logger.info(f"  Importance Score: {result.get('importance_score')}/10")
        logger.info(f"  Connections found: {len(result.get('connections', []))}")
        logger.info(f"  Resurfaced memories: {len(result.get('resurfaced', []))}")
        logger.info(f"  Thumbnail: {result.get('thumbnail_url')[:50]}..." if result.get('thumbnail_url') else "  Thumbnail: None")
        
        return {
            "success": True,
            "url": url,
            "memory_id": result.get("memory_id"),
            "platform": result.get("platform"),
            "title": result.get("title"),
            "category": result.get("category"),
            "importance_score": result.get("importance_score"),
            "elapsed_seconds": elapsed,
        }
    
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "error_type": type(e).__name__,
        }


def test_duplicate_detection(db, url: str):
    """Test duplicate detection (process the same URL twice)"""
    logger.info(f"\n{'─' * 70}")
    logger.info(f"Testing Duplicate Detection: {url}")
    logger.info(f"{'─' * 70}")
    
    try:
        from services.pipeline import process_url
        
        logger.info("→ First processing...")
        result1 = process_url(url, USER_PHONE, db)
        memory_id_1 = result1.get("memory_id")
        logger.info(f"✓ Created memory #{memory_id_1}")
        
        logger.info("→ Processing same URL again (should detect duplicate)...")
        result2 = process_url(url, USER_PHONE, db)
        memory_id_2 = result2.get("memory_id")
        
        if memory_id_1 == memory_id_2 and result2.get("duplicate"):
            logger.info(f"✓ Duplicate detected correctly (same memory ID: {memory_id_2})")
            return {"success": True, "duplicate_detected": True}
        else:
            logger.warning(f"⚠ Duplicate detection may not have worked (ID1: {memory_id_1}, ID2: {memory_id_2})")
            return {"success": False, "duplicate_detected": False}
    
    except Exception as e:
        logger.error(f"✗ Duplicate test failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def main():
    """Run all tests"""
    logger.info("")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 12 + "THREDION API PIPELINE TEST (REAL PHONE + LINKS)" + " " * 10 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info(f"User Phone: {USER_PHONE}")
    logger.info(f"Test Links: {len(TEST_LINKS)}")
    logger.info("")
    
    try:
        # Setup database
        engine, db = setup_database()
        
        # Test 1: Process URLs through pipeline
        logger.info("=" * 70)
        logger.info("TEST 1: Process URLs Through Full Pipeline")
        logger.info("=" * 70)
        
        results = []
        for url in TEST_LINKS:
            result = test_process_url(db, url)
            results.append(result)
        
        # Test 2: Duplicate detection
        logger.info("")
        logger.info("=" * 70)
        logger.info("TEST 2: Duplicate Detection")
        logger.info("=" * 70)
        
        if TEST_LINKS:
            dup_result = test_duplicate_detection(db, TEST_LINKS[0])
            logger.info(f"Duplicate detection: {'✓ PASS' if dup_result['success'] else '✗ FAIL'}")
        
        # Summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        
        passed = sum(1 for r in results if r.get("success"))
        total = len(results)
        
        for result in results:
            status = "✓ PASS" if result.get("success") else "✗ FAIL"
            error = f" — {result.get('error', '')}" if not result.get("success") else ""
            platform = result.get("platform", "unknown").upper()
            logger.info(f"{status} | {platform}{error}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        logger.info(f"End Time: {datetime.now().isoformat()}")
        logger.info("")
        
        db.close()
        return 0 if passed == total else 1
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
