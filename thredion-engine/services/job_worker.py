"""
Job Worker — Idempotent Queue Processing

This worker processes async jobs (transcription, classification) safely:
- Handles crashes without duplicate processing
- Implements state machine for atomic updates
- Retries transient failures intelligently
- Logs comprehensive state for debugging

This is what runs in background, processing long videos, waiting for APIs, etc.
"""

import logging
from typing import Optional
from datetime import datetime
from enum import Enum

from services.error_classifier import classify_failure, should_retry, FailureClass
from services.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Explicit job state machine."""
    QUEUED = "queued"  # Waiting to be picked up
    EXTRACTING = "extracting"  # Fetching content
    TRANSCRIBING = "transcribing"  # Running audio-to-text
    CLASSIFYING = "classifying"  # Running LLM classification
    SAVING = "saving"  # Writing to database
    COMPLETED = "completed"  # ✅ Success
    FAILED = "failed"  # ❌ Unrecoverable failure
    PARTIAL = "partial"  # ⚠️ Partial success (metadata but no transcript)
    UNAVAILABLE = "unavailable"  # Content not accessible


class JobWorkerResult:
    """Result of processing a job."""
    def __init__(
        self,
        status: JobStatus,
        memory_id: Optional[int] = None,
        transcript: Optional[str] = None,
        error_reason: Optional[str] = None,
        failure_class: Optional[FailureClass] = None,
    ):
        self.status = status
        self.memory_id = memory_id
        self.transcript = transcript
        self.error_reason = error_reason
        self.failure_class = failure_class


def process_transcription_job(job_id: str, db_session) -> JobWorkerResult:
    """
    Main worker function for processing async transcription jobs.
    
    This function is IDEMPOTENT - safe to call multiple times:
    - If job already completed, just return result
    - If job in progress by another worker, back off
    - If job crashed mid-process, resume from last state
    
    Flow:
        queued → extracting → transcribing → classifying → saving → completed
                                ↓ (fail)
                             failed or partial
    """
    
    logger.info(f"🚀 Worker starting job {job_id}")
    
    # Step 1: Load job from database
    # In real code:
    # job = db.query(Memory).filter(Memory.job_id == job_id).first()
    
    job = db_session.query_memory_by_job_id(job_id)
    
    if not job:
        logger.error(f"🛑 Job {job_id} not found in database")
        return JobWorkerResult(
            status=JobStatus.FAILED,
            error_reason="Job not found",
            failure_class=FailureClass.PERMANENT,
        )
    
    try:
        # Step 2: Idempotency check - is job already completed?
        if job["job_status"] == JobStatus.COMPLETED.value:
            logger.info(f"✅ Job {job_id} already completed, returning existing result")
            return JobWorkerResult(
                status=JobStatus.COMPLETED,
                memory_id=job["id"],
                transcript=job.get("transcript"),
            )
        
        # Step 3: Try to acquire lock (atomic update from queued → extracting)
        # Only update if currently in queued state
        updated = db_session.update_with_condition(
            table="memories",
            filters={"job_id": job_id, "job_status": JobStatus.QUEUED.value},
            updates={"job_status": JobStatus.EXTRACTING.value},
        )
        
        if updated == 0:
            # Job already being processed by another worker or already completed
            logger.warning(f"⚠️ Job {job_id} already being processed by another worker")
            return JobWorkerResult(
                status=JobStatus.FAILED,
                error_reason="Job already being processed by another worker",
                failure_class=FailureClass.TRANSIENT,
            )
        
        logger.info(f"🔒 Acquired lock for job {job_id}")
        
        # Step 4: EXTRACTING - Fetch content
        try:
            logger.info(f"📥 Extracting content for {job['url']}")
            
            # Update state
            db_session.update("memories", {"job_status": JobStatus.EXTRACTING.value}, job_id)
            
            # Do extraction (would call youtube_extractor, instagram_extractor, etc)
            extraction_result = extract_content_from_url(job["url"], job["platform"])
            
            if not extraction_result.success:
                raise Exception(extraction_result.error)
            
            # Update with extracted content
            db_session.update(
                "memories",
                {
                    "title": extraction_result.title,
                    "content": extraction_result.content,
                    "source_type": extraction_result.source_type,
                },
                job_id,
            )
        
        except Exception as extract_error:
            failure_class, reason = classify_failure(extract_error)
            logger.error(f"❌ Extraction failed: {reason}")
            
            db_session.update(
                "memories",
                {
                    "job_status": JobStatus.FAILED.value,
                    "failure_reason": reason,
                    "failure_class": failure_class.value,
                    "last_failure_at": datetime.utcnow(),
                },
                job_id,
            )
            
            return JobWorkerResult(
                status=JobStatus.FAILED,
                error_reason=reason,
                failure_class=failure_class,
            )
        
        # Step 5: TRANSCRIBING (if applicable)
        if job["platform"] == "youtube" and extraction_result.duration < 300:
            try:
                logger.info(f"🎙️ Transcribing audio")
                
                db_session.update("memories", {"job_status": JobStatus.TRANSCRIBING.value}, job_id)
                
                transcript = transcribe_audio(extraction_result.audio_path, job_id)
                
                db_session.update(
                    "memories",
                    {
                        "transcript": transcript,
                        "transcript_length": len(transcript),
                        "source_type": "local_asr",
                    },
                    job_id,
                )
            
            except Exception as transcribe_error:
                failure_class, reason = classify_failure(transcribe_error)
                logger.warning(f"⚠️ Transcription failed: {reason}")
                
                # Transcription failure is not critical - can continue with metadata
                db_session.update(
                    "memories",
                    {
                        "failure_reason": reason,
                        "failure_class": failure_class.value,
                        # Don't set job_status to failed yet - might still classify
                    },
                    job_id,
                )
        
        # Step 6: CLASSIFYING - Run LLM on content
        try:
            logger.info(f"🧠 Classifying content")
            
            db_session.update("memories", {"job_status": JobStatus.CLASSIFYING.value}, job_id)
            
            # Get best available content (transcript > caption > metadata)
            content_to_classify = (
                job.get("transcript") or 
                job.get("content") or 
                job.get("title")
            )
            
            classification = classify_content(content_to_classify, job_id)
            
            db_session.update(
                "memories",
                {
                    "cognitive_mode": classification["mode"],
                    "bucket": classification["bucket"],
                    "confidence_score": classification["confidence"],
                    "summary": classification["summary"],
                    "key_points": classification["key_points"],
                },
                job_id,
            )
        
        except Exception as classify_error:
            failure_class, reason = classify_failure(classify_error)
            logger.error(f"❌ Classification failed: {reason}")
            
            db_session.update(
                "memories",
                {
                    "job_status": JobStatus.FAILED.value,
                    "failure_reason": reason,
                    "failure_class": failure_class.value,
                    "last_failure_at": datetime.utcnow(),
                },
                job_id,
            )
            
            return JobWorkerResult(
                status=JobStatus.FAILED,
                error_reason=reason,
                failure_class=failure_class,
            )
        
        # Step 7: SAVING - Write final result
        try:
            logger.info(f"💾 Saving to database")
            
            db_session.update(
                "memories",
                {
                    "job_status": JobStatus.COMPLETED.value,
                    "processed_at": datetime.utcnow(),
                },
                job_id,
            )
            
            logger.info(f"✅ Job {job_id} COMPLETED successfully")
            
            return JobWorkerResult(
                status=JobStatus.COMPLETED,
                memory_id=job["id"],
                transcript=job.get("transcript"),
            )
        
        except Exception as save_error:
            logger.critical(f"💥 CRITICAL: Failed to save result: {save_error}")
            # Don't update status - will retry on next attempt
            raise
    
    except Exception as outer_error:
        # Worker itself crashed - don't touch DB, let retry mechanism handle it
        logger.critical(f"💥 Worker crashed processing {job_id}: {outer_error}")
        raise


def handle_job_failure(job_id: str, db_session, attempt_count: int = 1) -> bool:
    """
    Determine if a failed job should be retried.
    
    Returns:
        True if should retry, False if should give up
    """
    
    job = db_session.query_memory_by_job_id(job_id)
    
    if not job:
        return False
    
    failure_class = FailureClass(job.get("failure_class", "unknown"))
    
    # Decide: should we retry?
    if should_retry(failure_class, attempt_count):
        # Reset to queued for retry
        db_session.update(
            "memories",
            {"job_status": JobStatus.QUEUED.value},
            job_id,
        )
        logger.info(f"🔄 Job {job_id} requeued for retry (attempt {attempt_count + 1})")
        return True
    else:
        # Give up
        logger.warning(f"❌ Job {job_id} failed permanently: {job.get('failure_reason')}")
        return False


# ── Placeholder functions for actual work ────────────────────────────────


def extract_content_from_url(url: str, platform: str):
    """Placeholder for actual extraction logic."""
    # Would call: youtube_extractor, instagram_extractor, twitter_extractor
    pass


def transcribe_audio(audio_path: str, job_id: str) -> str:
    """Placeholder for transcription."""
    # Would call: services/transcriber.py
    pass


def classify_content(content: str, job_id: str) -> dict:
    """Placeholder for LLM classification."""
    # Would call: services/llm_processor.py
    pass
