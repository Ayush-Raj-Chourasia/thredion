"""
Error Classifier — Categorize Failures for Retry Strategy

Failures are not all equal. Some will work if retried (transient),
some need authentication (auth), some won't ever work (permanent).

This classifier ensures we:
- Don't waste retries on permanent failures
- Don't retry auth errors without intervention
- Handle transient errors intelligently
- Track failure patterns for debugging
"""

import logging
from enum import Enum
from typing import Tuple

logger = logging.getLogger(__name__)


class FailureClass(Enum):
    """Categories of failures."""
    TRANSIENT = "transient"  # Retry likely to succeed
    AUTH = "auth"  # Need re-authentication
    PERMANENT = "permanent"  # Will never succeed
    UNSUPPORTED = "unsupported"  # Platform/content not supported
    UNKNOWN = "unknown"  # Can't classify


def classify_failure(error: Exception) -> Tuple[FailureClass, str]:
    """
    Analyze an exception and classify the failure type.
    
    Returns:
        (failure_class, human_readable_explanation)
    """
    
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # ── TRANSIENT ERRORS ─────────────────────────────────────────
    # Will likely succeed if retried
    
    transient_keywords = [
        "timeout",
        "connection reset",
        "connection refused",
        "temporarily unavailable",
        "please try again",
        "try again",
        "throttled",
        "rate limit",  # 429 is transient initially
        "enetunreach",
        "econnrefused",
        "etimedout",
        "broken pipe",
        "temporary failure",
    ]
    
    if any(keyword in error_msg for keyword in transient_keywords):
        return (
            FailureClass.TRANSIENT,
            f"Transient network error, safe to retry: {error_msg[:100]}"
        )
    
    if error_type in ["timeout", "connectionerror", "timeout error"]:
        return (FailureClass.TRANSIENT, "Network timeout")
    
    # ── PERMANENT ERRORS ────────────────────────────────────────
    # Will never succeed, don't retry
    
    permanent_keywords = [
        "404",
        "not found",
        "video not found",
        "post not found",
        "deleted",
        "removed",
        "no longer available",
        "private",
        "only available to followers",
        "only available to the owner",
        "channel terminated",
        "disabled",
        "unsupported format",
        "unsupported video",
        "unsupported audio",
    ]
    
    if any(keyword in error_msg for keyword in permanent_keywords):
        return (
            FailureClass.PERMANENT,
            f"Permanent failure (content not available): {error_msg[:100]}"
        )
    
    # ── AUTHENTICATION ERRORS ─────────────────────────────────────
    # Need auth refresh or cookies
    
    auth_keywords = [
        "401",
        "403",
        "unauthorized",
        "forbidden",
        "login required",
        "sign in to confirm",
        "bot check",
        "suspect you're a bot",
        "please log in",
        "authentication required",
        "access denied",
    ]
    
    if any(keyword in error_msg for keyword in auth_keywords):
        return (
            FailureClass.AUTH,
            f"Authentication required: {error_msg[:100]}"
        )
    
    if error_type in ["unauthorized", "forbidden"]:
        return (FailureClass.AUTH, "Unauthorized access")
    
    # ── UNSUPPORTED ERRORS ──────────────────────────────────────
    # Platform/feature not supported
    
    unsupported_keywords = [
        "unsupported",
        "not supported",
        "cannot",
        "not available for",
        "not available in your region",
        "geoblocked",
        "not implemented",
    ]
    
    if any(keyword in error_msg for keyword in unsupported_keywords):
        return (
            FailureClass.UNSUPPORTED,
            f"Feature not supported: {error_msg[:100]}"
        )
    
    # ── DEFAULT: TRANSIENT (SAFER TO RETRY) ──────────────────────
    # When in doubt, classify as transient (can retry)
    
    return (
        FailureClass.TRANSIENT,
        f"Unknown error (classified as transient, safe to retry): {error_msg[:100]}"
    )


def should_retry(failure_class: FailureClass, attempt_count: int) -> bool:
    """
    Decide whether to retry based on failure class.
    
    Args:
        failure_class: Category of failure
        attempt_count: Number of attempts so far (1-indexed)
    
    Returns:
        True if should retry, False if should give up
    """
    
    # Never retry permanent failures
    if failure_class == FailureClass.PERMANENT:
        logger.info(f"❌ Not retrying: permanent failure")
        return False
    
    # Never retry unsupported
    if failure_class == FailureClass.UNSUPPORTED:
        logger.info(f"❌ Not retrying: unsupported feature")
        return False
    
    # Transient errors: retry up to 3 times
    if failure_class == FailureClass.TRANSIENT:
        if attempt_count < 3:
            logger.info(f"🔄 Retrying transient error (attempt {attempt_count}/3)")
            return True
        else:
            logger.warning(f"❌ Transient error failed 3 times, giving up")
            return False
    
    # Auth errors: retry up to 2 times (need manual intervention)
    if failure_class == FailureClass.AUTH:
        if attempt_count < 2:
            logger.info(f"🔑 Retrying auth error (attempt {attempt_count}/2)")
            return True
        else:
            logger.warning(f"❌ Auth error needs manual intervention")
            return False
    
    # Unknown: conservative - don't retry
    logger.warning(f"❌ Unknown failure class, not retrying")
    return False


def get_retry_delay_seconds(failure_class: FailureClass, attempt_count: int) -> int:
    """
    Calculate retry delay using exponential backoff.
    
    Lower delays for transient errors (fast recovery needed),
    longer delays for auth errors (may need time for rate limit reset).
    """
    
    if failure_class == FailureClass.TRANSIENT:
        # Backoff: 2s, 4s, 8s
        return 2 ** attempt_count
    
    elif failure_class == FailureClass.AUTH:
        # Longer backoff for auth: 5s, 10s
        return 5 * attempt_count
    
    else:
        # Default: don't retry anyway, but if forced, longer delay
        return 30


def explain_failure(failure_class: FailureClass) -> str:
    """
    Generate user-friendly explanation of failure.
    """
    
    explanations = {
        FailureClass.TRANSIENT: (
            "Temporary error (network issue). "
            "This will be retried automatically. "
            "If it persists, the platform may be down."
        ),
        FailureClass.AUTH: (
            "Authentication required. "
            "The platform is requesting login/verification. "
            "This may require manual intervention."
        ),
        FailureClass.PERMANENT: (
            "Content not available. "
            "The post/video is deleted, private, or otherwise inaccessible. "
            "This won't be retried."
        ),
        FailureClass.UNSUPPORTED: (
            "Feature not supported. "
            "This platform or content type is not supported yet. "
            "Try a different link."
        ),
        FailureClass.UNKNOWN: (
            "Unknown error. "
            "Please try again or contact support."
        ),
    }
    
    return explanations.get(failure_class, "Unknown error")
