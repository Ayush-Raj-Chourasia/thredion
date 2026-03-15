#!/usr/bin/env python3
"""
Thredion Engine — Keep-Warm Script for Render Free
Pings the health endpoint regularly to prevent cold starts.

Usage:
1. Local: `python keep-warm.py` (runs in background, pings every 10 mins)
2. Cron job: `0 */2 * * * curl -f http://your-render-url/health || exit 1` (every 2 hours)
3. GitHub Actions: Set up workflow to run this periodically (see .github/workflows/keep-warm.yml)

Why needed:
- Render Free tier spins down after 15 mins of inactivity
- This keeps the app "warm" so cold starts are avoided
- Twilio webhooks won't timeout if app is already running
"""

import os
import sys
import logging
import time
import asyncio
from datetime import datetime
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("keep-warm")


def get_app_url():
    """Get the app URL from environment or command line."""
    # Priority: env var > command line > default
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    url = os.getenv("APP_URL", "").strip()
    if url:
        return url
    
    # Check for common environment variables set by deployment platforms
    if os.getenv("RENDER_EXTERNAL_URL"):
        return os.getenv("RENDER_EXTERNAL_URL")
    
    print("Usage: python keep-warm.py <APP_URL>")
    print("  or set APP_URL environment variable")
    print("  or rely on RENDER_EXTERNAL_URL (auto-set by Render)")
    sys.exit(1)


async def ping_health(url: str, timeout: int = 10) -> bool:
    """Ping the /health endpoint."""
    health_url = url.rstrip("/") + "/health"
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(health_url, follow_redirects=True)
            success = response.status_code == 200
            
            if success:
                logger.info(f"✓ Health check passed ({response.status_code}) | {health_url}")
                return True
            else:
                logger.warning(f"⚠ Unexpected status {response.status_code} | {health_url}")
                return False
    
    except httpx.TimeoutException:
        logger.error(f"✗ Timeout (>{timeout}s) | {health_url}")
        return False
    except httpx.RequestError as e:
        logger.error(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


async def keep_warm_loop(url: str, interval_minutes: int = 10):
    """
    Continuously ping the health endpoint every `interval_minutes`.
    
    Args:
        url: The app URL to ping
        interval_minutes: How often to ping (default 10 = every 10 minutes)
    """
    interval_seconds = interval_minutes * 60
    
    logger.info(f"Starting keep-warm loop")
    logger.info(f"  App URL: {url}")
    logger.info(f"  Interval: every {interval_minutes} minutes ({interval_seconds}s)")
    logger.info(f"  Starting at: {datetime.now().isoformat()}")
    
    failure_count = 0
    max_failures = 3  # Stop after 3 consecutive failures
    
    while True:
        try:
            # Ping the health endpoint
            success = await ping_health(url)
            
            if success:
                failure_count = 0  # Reset failure counter
            else:
                failure_count += 1
                if failure_count >= max_failures:
                    logger.critical(f"⚠ {max_failures} consecutive failures. Stopping.")
                    break
            
            # Wait before next ping
            logger.debug(f"Next ping in {interval_minutes} minutes...")
            await asyncio.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("Keep-warm stopped by user (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Unexpected error in loop: {e}")
            await asyncio.sleep(5)  # Retry after 5 seconds


def main():
    """Main entry point."""
    app_url = get_app_url()
    
    # Optional: get interval from env or use default
    interval = int(os.getenv("KEEP_WARM_INTERVAL_MINUTES", "10"))
    
    try:
        asyncio.run(keep_warm_loop(app_url, interval))
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
