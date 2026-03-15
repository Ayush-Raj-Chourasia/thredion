#!/usr/bin/env python3
"""
Test Thredion Extractors with Real Content
Tests Instagram Reels and YouTube Shorts extraction with actual links.
"""

import sys
import os
import logging
from datetime import datetime

# Add thredion-engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'thredion-engine'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("test_real_content")

# Test URLs
TEST_URLS = {
    "instagram": "https://www.instagram.com/p/DUxWU53Ep6P/",
    "youtube_shorts": "https://www.youtube.com/shorts/YNAOYWufq74",
}

def test_instagram_extraction():
    """Test Instagram post extraction"""
    logger.info("=" * 70)
    logger.info("TEST 1: Instagram Extraction")
    logger.info("=" * 70)
    
    url = TEST_URLS["instagram"]
    logger.info(f"Testing URL: {url}")
    
    try:
        from services.instagram_extractor import extract_instagram
        
        logger.info("→ Extracting Instagram content...")
        result = extract_instagram(url)
        
        logger.info("✓ Instagram extraction succeeded!")
        logger.info(f"  Platform: {result.platform}")
        logger.info(f"  Title: {result.title[:80]}..." if len(result.title) > 80 else f"  Title: {result.title}")
        logger.info(f"  Content length: {len(result.content)} characters")
        logger.info(f"  Content preview: {result.content[:200]}..." if len(result.content) > 200 else f"  Content: {result.content}")
        logger.info(f"  Username: {result.username}")
        logger.info(f"  Is Video: {result.is_video}")
        logger.info(f"  Thumbnail: {result.thumbnail_url[:60]}..." if result.thumbnail_url else "  Thumbnail: None")
        logger.info(f"  Source Type: {result.source_type}")
        logger.info(f"  Extraction Time: {result.extraction_time_ms}ms")
        
        return {
            "success": result.success,
            "platform": result.platform,
            "title": result.title,
            "content": result.content,
            "username": result.username,
            "extraction_time_ms": result.extraction_time_ms,
        }
    
    except Exception as e:
        logger.error(f"✗ Instagram extraction failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


def test_youtube_extraction():
    """Test YouTube Shorts extraction"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 2: YouTube Shorts Extraction")
    logger.info("=" * 70)
    
    url = TEST_URLS["youtube_shorts"]
    logger.info(f"Testing URL: {url}")
    
    try:
        from services.youtube_extractor import extract_youtube
        
        logger.info("→ Extracting YouTube content...")
        result = extract_youtube(url)
        
        logger.info("✓ YouTube extraction succeeded!")
        logger.info(f"  Platform: {result.platform}")
        logger.info(f"  Title: {result.title}")
        logger.info(f"  Content length: {len(result.content)} characters")
        logger.info(f"  Content preview: {result.content[:200]}..." if len(result.content) > 200 else f"  Content: {result.content}")
        logger.info(f"  Channel: {result.channel_name}")
        logger.info(f"  Duration: {result.duration_seconds}s")
        logger.info(f"  Thumbnail: {result.thumbnail_url[:60]}..." if result.thumbnail_url else "  Thumbnail: None")
        logger.info(f"  Source Type: {result.source_type}")
        logger.info(f"  Extraction Time: {result.extraction_time_ms}ms")
        
        return {
            "success": result.success,
            "platform": result.platform,
            "title": result.title,
            "content": result.content,
            "channel": result.channel_name,
            "duration": result.duration_seconds,
            "extraction_time_ms": result.extraction_time_ms,
        }
    
    except Exception as e:
        logger.error(f"✗ YouTube extraction failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


def test_api_integration():
    """Test the full pipeline"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 3: Full API Integration (Mock)")
    logger.info("=" * 70)
    
    try:
        # Mock the database and process both URLs
        logger.info("Testing Instagram + YouTube extraction in sequence...")
        
        results = []
        for platform, url in TEST_URLS.items():
            logger.info(f"\n  [{platform.upper()}] Processing {url}")
            try:
                if platform == "instagram":
                    result = test_instagram_extraction()
                else:
                    result = test_youtube_extraction()
                results.append(result)
            except Exception as e:
                logger.error(f"    Error: {e}")
                results.append({"success": False, "error": str(e)})
        
        return results
    
    except Exception as e:
        logger.error(f"✗ Integration test failed: {e}", exc_info=True)
        return []


def main():
    """Run all tests"""
    logger.info("")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "THREDION REAL CONTENT TEST SUITE" + " " * 21 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("")
    
    results = {}
    
    # Test extractors individually
    logger.info("Testing individual extractors...\n")
    
    instagram_result = test_instagram_extraction()
    results["instagram"] = instagram_result
    
    youtube_result = test_youtube_extraction()
    results["youtube"] = youtube_result
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    for platform, result in results.items():
        status = "✓ PASS" if result.get("success") else "✗ FAIL"
        error = f" — {result.get('error', 'Unknown error')}" if not result.get("success") else ""
        logger.info(f"{status} | {platform.upper()}{error}")
    
    logger.info("")
    logger.info(f"End Time: {datetime.now().isoformat()}")
    logger.info("")
    
    # Return exit code
    all_passed = all(r.get("success") for r in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
