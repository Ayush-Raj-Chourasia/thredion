"""Quick integration test for the cognitive pipeline."""
import asyncio
from services.cognitive_pipeline import process_cognitive_entry

async def test():
    print("Testing cognitive pipeline with YouTube short...")
    result = await process_cognitive_entry(
        "https://www.youtube.com/shorts/rJhJ9xlRyTA",
        "test_user",
        None,
        None
    )
    print(f"SUCCESS: {result.success}")
    print(f"Quality: {result.content_quality}")
    print(f"Content: {len(result.content)} chars")
    print(f"Transcript: {len(result.transcript) if result.transcript else 0} chars")
    print(f"Mode: {result.cognitive_mode}")
    print(f"Bucket: {result.bucket}")
    print(f"Summary: {(result.summary or '')[: 150]}")
    print(f"Tags: {result.tags}")
    print(f"Time: {result.extraction_time_ms}ms")
    if result.error:
        print(f"Error: {result.error}")

asyncio.run(test())
