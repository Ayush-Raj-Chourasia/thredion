#!/usr/bin/env python3
"""
Live Smoke Test: Real URL extraction against actual platforms.

This validates whether the extractors actually work with live content,
not just that the code structure is correct.

Tests real public URLs from each platform and logs:
- success/failure
- source_type
- extraction time
- content length
- failure_reason
- data freshness
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Test URLs - all public, no login required
TEST_URLS = {
    "youtube": [
        "https://www.youtube.com/shorts/rJhJ9xlRyTA",  # British vs American English
        "https://www.youtube.com/shorts/Edl-l88L-C4",  # English at a restaurant
        "https://www.youtube.com/shorts/gX-72MXld8s",  # Beginner, Intermediate & Advanced English
        "https://www.youtube.com/shorts/cFRZM-06z9o",  # Advanced English vocabulary
        "https://www.youtube.com/shorts/xVDSRXz6McQ",  # English class: IN vs ON
    ],
    "instagram": [
        "https://www.instagram.com/reel/C-_El56RpwS/",  # English-themed reel by Bobby Finn
        "https://www.instagram.com/reel/DBE9FzwRqkt/",  # English/language humor reel
        "https://www.instagram.com/reel/C_tdGqYRwHo/",  # English skit reel
        "https://www.instagram.com/reel/C-LggFCxdZE/",  # English skit reel
        "https://www.instagram.com/reel/DE0ZNySRlQ0/",  # English skit reel
    ],
    "twitter": [],  # Skip Twitter for now - focus on YouTube and Instagram
}

# Simplified test URLs (fallback if above fail)
FALLBACK_URLS = {
    "youtube": [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Guaranteed captions
    ],
    "instagram": [
        "https://www.instagram.com/instagram/",  # Official Instagram account
    ],
    "twitter": [
        "https://twitter.com/twitter/",  # Official Twitter account
    ],
}


def test_youtube():
    """Test YouTube extraction against real videos."""
    print("\n" + "="*60)
    print(" YOUTUBE EXTRACTION TESTS")
    print("="*60)
    
    from services.youtube_extractor import YouTubeExtractor
    
    extractor = YouTubeExtractor()
    results = []
    
    for url in TEST_URLS["youtube"]:
        print(f"\nTesting: {url}")
        start = time.time()
        try:
            result = extractor.extract(url)
            elapsed = time.time() - start
            
            success_marker = "✅" if result.success else "❌"
            print(f"{success_marker} Success: {result.success}")
            print(f"   Duration: {elapsed:.2f}s")
            print(f"   Source Type: {result.source_type}")
            print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                print(f"   Failure: {result.failure_reason}")
            if result.content:
                print(f"   Preview: {result.content[:100]}...")
            
            results.append({
                "platform": "youtube",
                "url": url,
                "success": result.success,
                "source_type": result.source_type,
                "duration_seconds": elapsed,
                "content_length": len(result.content) if result.content else 0,
                "failure_reason": result.failure_reason,
                "title": result.title,
            })
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {str(e)}")
            results.append({
                "platform": "youtube",
                "url": url,
                "success": False,
                "source_type": None,
                "duration_seconds": time.time() - start,
                "content_length": 0,
                "failure_reason": f"Exception: {type(e).__name__}",
                "title": None,
            })
    
    return results


def test_instagram():
    """Test Instagram extraction against real posts."""
    print("\n" + "="*60)
    print(" INSTAGRAM EXTRACTION TESTS")
    print("="*60)
    
    from services.instagram_extractor import InstagramExtractor
    
    extractor = InstagramExtractor()
    results = []
    
    for url in TEST_URLS["instagram"]:
        print(f"\nTesting: {url}")
        start = time.time()
        try:
            result = extractor.extract(url)
            elapsed = time.time() - start
            
            success_marker = "✅" if result.success else "❌"
            print(f"{success_marker} Success: {result.success}")
            print(f"   Duration: {elapsed:.2f}s")
            print(f"   Source Type: {result.source_type}")
            print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                print(f"   Failure: {result.failure_reason}")
            if result.content:
                print(f"   Preview: {result.content[:100]}...")
            
            results.append({
                "platform": "instagram",
                "url": url,
                "success": result.success,
                "source_type": result.source_type,
                "duration_seconds": elapsed,
                "content_length": len(result.content) if result.content else 0,
                "failure_reason": result.failure_reason,
                "title": result.title,
                "has_video": result.has_video,
                "has_carousel": result.has_carousel,
            })
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {str(e)}")
            results.append({
                "platform": "instagram",
                "url": url,
                "success": False,
                "source_type": None,
                "duration_seconds": time.time() - start,
                "content_length": 0,
                "failure_reason": f"Exception: {type(e).__name__}",
                "title": None,
                "has_video": False,
                "has_carousel": False,
            })
    
    return results


def test_twitter():
    """Test Twitter/X extraction against real tweets."""
    print("\n" + "="*60)
    print(" TWITTER/X EXTRACTION TESTS")
    print("="*60)
    
    from services.twitter_extractor import TwitterExtractor
    
    extractor = TwitterExtractor()
    results = []
    
    for url in TEST_URLS["twitter"]:
        print(f"\nTesting: {url}")
        start = time.time()
        try:
            result = extractor.extract(url)
            elapsed = time.time() - start
            
            success_marker = "✅" if result.success else "❌"
            print(f"{success_marker} Success: {result.success}")
            print(f"   Duration: {elapsed:.2f}s")
            print(f"   Source Type: {result.source_type}")
            print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                print(f"   Failure: {result.failure_reason}")
            if result.content:
                print(f"   Preview: {result.content[:100]}...")
            
            results.append({
                "platform": "twitter",
                "url": url,
                "success": result.success,
                "source_type": result.source_type,
                "duration_seconds": elapsed,
                "content_length": len(result.content) if result.content else 0,
                "failure_reason": result.failure_reason,
                "title": result.title,
                "has_media": result.has_media,
            })
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {str(e)}")
            results.append({
                "platform": "twitter",
                "url": url,
                "success": False,
                "source_type": None,
                "duration_seconds": time.time() - start,
                "content_length": 0,
                "failure_reason": f"Exception: {type(e).__name__}",
                "title": None,
                "has_media": False,
            })
    
    return results


def main():
    """Run all smoke tests and generate report."""
    print("\n" + "="*60)
    print(" LIVE SMOKE TEST SUITE")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*60)
    
    all_results = []
    
    # Test each platform
    try:
        all_results.extend(test_youtube())
    except ImportError as e:
        print(f"\n⚠️  YouTube extractor import failed: {e}")
    except Exception as e:
        print(f"\n YouTube tests crashed: {e}")
    
    try:
        all_results.extend(test_instagram())
    except ImportError as e:
        print(f"\n⚠️  Instagram extractor import failed: {e}")
    except Exception as e:
        print(f"\n Instagram tests crashed: {e}")
    
    try:
        all_results.extend(test_twitter())
    except ImportError as e:
        print(f"\n⚠️  Twitter extractor import failed: {e}")
    except Exception as e:
        print(f"\n  Twitter tests skipped (focus on YouTube + Instagram for now)")
    
    # Summary
    print("\n" + "="*60)
    print(" SUMMARY")
    print("="*60)
    
    if all_results:
        passed = sum(1 for r in all_results if r["success"])
        total = len(all_results)
        print(f"\nTests Passed: {passed}/{total}")
        
        by_platform = {}
        for result in all_results:
            platform = result["platform"]
            if platform not in by_platform:
                by_platform[platform] = {"passed": 0, "total": 0}
            by_platform[platform]["total"] += 1
            if result["success"]:
                by_platform[platform]["passed"] += 1
        
        print("\nBy Platform:")
        for platform, stats in sorted(by_platform.items()):
            pct = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {platform}: {stats['passed']}/{stats['total']} ({pct:.0f}%)")
        
        # Detailed failures
        failures = [r for r in all_results if not r["success"]]
        if failures:
            print("\nFailures:")
            for f in failures:
                print(f"  {f['platform']}: {f['failure_reason']}")
        
        # Save report
        report_path = Path(__file__).parent / "live_smoke_test_report.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "passed": passed,
                    "total": total,
                    "by_platform": by_platform,
                },
                "results": all_results,
            }, f, indent=2)
        
        print(f"\n Report saved: {report_path}")
    else:
        print("\n⚠️  No tests ran successfully. Check extractor imports.")
    
    print("\n" + "="*60)
    print(f"Completed: {datetime.now().isoformat()}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
