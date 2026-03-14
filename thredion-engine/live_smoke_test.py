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

NOTE: Fully Windows-safe (no emoji characters that crash cp1252).
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Test URLs - all public, no login required
TEST_URLS = {
    "youtube": [
        "https://www.youtube.com/shorts/rJhJ9xlRyTA",  # British vs American English
        "https://www.youtube.com/shorts/gX-72MXld8s",  # Beginner, Intermediate & Advanced English
        "https://www.youtube.com/shorts/cFRZM-06z9o",  # Advanced English vocabulary
        "https://www.youtube.com/shorts/xVDSRXz6McQ",  # English class: IN vs ON
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
    ],
    "instagram": [
        "https://www.instagram.com/reel/C-_El56RpwS/",  # English-themed reel
        "https://www.instagram.com/reel/DBE9FzwRqkt/",  # English/language humor reel
        "https://www.instagram.com/reel/C_tdGqYRwHo/",  # English skit reel
        "https://www.instagram.com/reel/C-LggFCxdZE/",  # English skit reel
        "https://www.instagram.com/reel/DE0ZNySRlQ0/",  # English skit reel
    ],
    "twitter": [
        # Use well-known existing tweets
        "https://twitter.com/elonmusk/status/1519480761749016577",  # Elon buying twitter
        "https://x.com/NASA/status/1445764532",  # NASA tweet
    ],
}

# Rate limit delays (seconds) between requests per platform
RATE_LIMITS = {
    "youtube": 3.0,   # YouTube aggressively bans IPs
    "instagram": 1.0,
    "twitter": 0.5,
}


def safe_print(text):
    """Print text safely on Windows (replace unencodable chars)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def test_youtube():
    """Test YouTube extraction against real videos."""
    safe_print("\n" + "=" * 60)
    safe_print("[YT] YOUTUBE EXTRACTION TESTS")
    safe_print("=" * 60)

    from services.youtube_extractor import extract_youtube

    results = []

    for i, url in enumerate(TEST_URLS["youtube"]):
        safe_print(f"\nTesting [{i+1}/{len(TEST_URLS['youtube'])}]: {url}")

        # Rate limit: delay between requests to avoid IP ban
        if i > 0:
            delay = RATE_LIMITS["youtube"]
            safe_print(f"   (waiting {delay}s to avoid IP ban...)")
            time.sleep(delay)

        start = time.time()
        try:
            result = extract_youtube(url)
            elapsed = time.time() - start

            marker = "[OK]" if result.success else "[FAIL]"
            safe_print(f"   {marker} Success: {result.success}")
            safe_print(f"   Duration: {elapsed:.2f}s")
            safe_print(f"   Source Type: {result.source_type}")
            safe_print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                safe_print(f"   Failure: {result.failure_reason[:100]}")
            if result.content:
                preview = result.content[:100].replace("\n", " ")
                safe_print(f"   Preview: {preview}...")

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
            safe_print(f"   [EXCEPTION] {type(e).__name__}: {str(e)[:100]}")
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
    safe_print("\n" + "=" * 60)
    safe_print("[IG] INSTAGRAM EXTRACTION TESTS")
    safe_print("=" * 60)

    from services.instagram_extractor import extract_instagram

    results = []

    for i, url in enumerate(TEST_URLS["instagram"]):
        safe_print(f"\nTesting [{i+1}/{len(TEST_URLS['instagram'])}]: {url}")

        if i > 0:
            delay = RATE_LIMITS["instagram"]
            time.sleep(delay)

        start = time.time()
        try:
            result = extract_instagram(url)
            elapsed = time.time() - start

            marker = "[OK]" if result.success else "[FAIL]"
            safe_print(f"   {marker} Success: {result.success}")
            safe_print(f"   Duration: {elapsed:.2f}s")
            safe_print(f"   Source Type: {result.source_type}")
            safe_print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                safe_print(f"   Failure: {result.failure_reason[:100]}")
            if result.content:
                preview = result.content[:100].replace("\n", " ")
                safe_print(f"   Preview: {preview}...")

            results.append({
                "platform": "instagram",
                "url": url,
                "success": result.success,
                "source_type": result.source_type,
                "duration_seconds": elapsed,
                "content_length": len(result.content) if result.content else 0,
                "failure_reason": result.failure_reason,
                "title": result.title,
            })
        except Exception as e:
            safe_print(f"   [EXCEPTION] {type(e).__name__}: {str(e)[:100]}")
            results.append({
                "platform": "instagram",
                "url": url,
                "success": False,
                "source_type": None,
                "duration_seconds": time.time() - start,
                "content_length": 0,
                "failure_reason": f"Exception: {type(e).__name__}",
                "title": None,
            })

    return results


def test_twitter():
    """Test Twitter/X extraction against real tweets."""
    safe_print("\n" + "=" * 60)
    safe_print("[TW] TWITTER/X EXTRACTION TESTS")
    safe_print("=" * 60)

    from services.twitter_extractor import extract_twitter

    results = []

    for i, url in enumerate(TEST_URLS["twitter"]):
        safe_print(f"\nTesting [{i+1}/{len(TEST_URLS['twitter'])}]: {url}")

        if i > 0:
            delay = RATE_LIMITS["twitter"]
            time.sleep(delay)

        start = time.time()
        try:
            result = extract_twitter(url)
            elapsed = time.time() - start

            marker = "[OK]" if result.success else "[FAIL]"
            safe_print(f"   {marker} Success: {result.success}")
            safe_print(f"   Duration: {elapsed:.2f}s")
            safe_print(f"   Source Type: {result.source_type}")
            safe_print(f"   Content Length: {len(result.content) if result.content else 0} chars")
            if result.failure_reason:
                safe_print(f"   Failure: {result.failure_reason[:100]}")
            if result.content:
                preview = result.content[:100].replace("\n", " ")
                safe_print(f"   Preview: {preview}...")

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
            safe_print(f"   [EXCEPTION] {type(e).__name__}: {str(e)[:100]}")
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
    safe_print("\n" + "=" * 60)
    safe_print("THREDION LIVE SMOKE TEST SUITE")
    safe_print(f"Started: {datetime.now().isoformat()}")
    safe_print("=" * 60)

    all_results = []

    # Test each platform
    safe_print("\n>> Running YouTube tests...")
    try:
        all_results.extend(test_youtube())
    except ImportError as e:
        safe_print(f"\n[SKIP] YouTube extractor import failed: {e}")
    except Exception as e:
        safe_print(f"\n[CRASH] YouTube tests crashed: {e}")

    safe_print("\n>> Running Instagram tests...")
    try:
        all_results.extend(test_instagram())
    except ImportError as e:
        safe_print(f"\n[SKIP] Instagram extractor import failed: {e}")
    except Exception as e:
        safe_print(f"\n[CRASH] Instagram tests crashed: {e}")

    safe_print("\n>> Running Twitter tests...")
    try:
        all_results.extend(test_twitter())
    except ImportError as e:
        safe_print(f"\n[SKIP] Twitter extractor import failed: {e}")
    except Exception as e:
        safe_print(f"\n[CRASH] Twitter tests crashed: {e}")

    # Summary
    safe_print("\n" + "=" * 60)
    safe_print("RESULTS SUMMARY")
    safe_print("=" * 60)

    if all_results:
        passed = sum(1 for r in all_results if r["success"])
        total = len(all_results)
        safe_print(f"\nOverall: {passed}/{total} ({passed/total*100:.0f}%)")

        by_platform = {}
        for result in all_results:
            platform = result["platform"]
            if platform not in by_platform:
                by_platform[platform] = {"passed": 0, "total": 0}
            by_platform[platform]["total"] += 1
            if result["success"]:
                by_platform[platform]["passed"] += 1

        safe_print("\nPer Platform:")
        for platform, stats in sorted(by_platform.items()):
            pct = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            marker = "[PASS]" if pct >= 60 else "[WARN]" if pct >= 30 else "[FAIL]"
            safe_print(f"  {marker} {platform}: {stats['passed']}/{stats['total']} ({pct:.0f}%)")

        # Source types breakdown
        source_types = {}
        for r in all_results:
            st = r.get("source_type", "unknown") or "unknown"
            source_types[st] = source_types.get(st, 0) + 1
        safe_print("\nSource Types:")
        for st, count in sorted(source_types.items()):
            safe_print(f"  {st}: {count}")

        # Failures
        failures = [r for r in all_results if not r["success"]]
        if failures:
            safe_print(f"\nFailures ({len(failures)}):")
            for f in failures:
                reason = (f.get("failure_reason") or "Unknown")[:80]
                safe_print(f"  {f['platform']}: {reason}")

        # Save report
        report_path = Path(__file__).parent / "live_smoke_test_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "passed": passed,
                    "total": total,
                    "pass_rate": f"{passed/total*100:.0f}%",
                    "by_platform": by_platform,
                },
                "results": all_results,
            }, f, indent=2, default=str)

        safe_print(f"\nReport saved: {report_path}")
    else:
        safe_print("\n[WARN] No tests ran. Check extractor imports.")

    safe_print("\n" + "=" * 60)
    safe_print(f"Completed: {datetime.now().isoformat()}")
    safe_print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
