"""
Thredion Background Worker - Azure Functions Entry Point
Deploy this as a Timer-Triggered Azure Function that runs every 5 seconds.

To deploy:
1. Create Azure Function App (Python runtime)
2. Create Timer-Triggered Function with schedule: "*/5 * * * * *"
3. Copy this file as function_app.py
4. Run: func azure functionapp publish <app-name>
"""

import azure.functions as func
import asyncio
import logging

from worker.transcription_worker import run_worker_async

app = func.FunctionApp()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger("ThredionWorker")


@app.timer_trigger(arg_name="myTimer", schedule="*/5 * * * * *")
async def transcription_worker(myTimer: func.TimerRequest) -> None:
    """
    Background worker: Poll Azure Queue for transcription jobs every 5 seconds.
    
    This Azure Function runs on a schedule and processes queued video transcription jobs.
    """
    if myTimer.past_due:
        logger.info('Timer is past due!')
    
    try:
        # Run one iteration of the worker
        await run_worker_async()
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise


# ── Alternative: HTTP Trigger (for manual testing) ───────

@app.function_name("worker_manual_trigger")
@app.route_with_auth(route="worker/trigger", methods=["POST"], auth_level=func.AuthLevel.ADMIN)
async def manual_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Manually trigger worker processing via HTTP.
    Useful for testing or manual job processing.
    """
    try:
        await run_worker_async()
        return func.HttpResponse("Worker executed successfully", status_code=200)
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
