"""
Thredion Engine — WhatsApp OTP Authentication
Phone-based login: send OTP via Twilio WhatsApp → verify → issue JWT.
"""

import logging
import random
import re
from datetime import datetime, timedelta, timezone

try:
    from jose import jwt, JWTError
    from jose.exceptions import ExpiredSignatureError
except ImportError:
    import jwt
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError as JWTError
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from core.config import settings
from db.database import get_db
from db.models import User, OTPCode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# ── Phone normalisation ──────────────────────────────────────

_PHONE_RE = re.compile(r"^\+\d{7,15}$")


def _normalise_phone(raw: str) -> str:
    """Strip spaces/dashes, ensure it starts with '+' and contains 7-15 digits."""
    phone = re.sub(r"[\s\-\(\)]", "", raw.strip())
    if not phone.startswith("+"):
        phone = "+" + phone
    if not _PHONE_RE.match(phone):
        raise ValueError(f"Invalid phone number: {raw}")
    return phone


# ── JWT helpers ───────────────────────────────────────────────


def _create_token(phone: str) -> str:
    """Issue a JWT token for the given phone number."""
    payload = {
        "sub": phone,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises on invalid/expired."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# ── Dependency: current authenticated user ────────────────────


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency – extracts and validates the Bearer token,
    returns the authenticated User row."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    claims = _decode_token(token)
    phone_number = claims.get("sub", "")

    # Support both SQLAlchemy and Supabase REST sessions
    from db.database import SupabaseSession
    if isinstance(db, SupabaseSession):
        user = db.get_user_by_phone(phone_number)
    else:
        user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    # Check is_active (may be attribute or dict value)
    is_active = getattr(user, 'is_active', True)
    if not is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ── OTP sending (via Twilio WhatsApp) ─────────────────────────


def _send_otp_whatsapp(phone: str, code: str) -> bool:
    """Send the OTP code to the user's WhatsApp number via Twilio."""
    try:
        from twilio.rest import Client

        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.error("Twilio credentials not configured — cannot send OTP")
            return False

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        whatsapp_from = settings.TWILIO_WHATSAPP_NUMBER
        if not whatsapp_from.startswith("whatsapp:"):
            whatsapp_from = f"whatsapp:{whatsapp_from}"

        message = client.messages.create(
            body=f"🔐 Your Thredion login code is: *{code}*\n\nThis code expires in {settings.OTP_EXPIRY_MINUTES} minutes. Do not share it with anyone.",
            from_=whatsapp_from,
            to=f"whatsapp:{phone}",
        )
        logger.info(f"OTP sent to {phone} — Twilio SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP to {phone}: {e}")
        return False


# ── Endpoints ─────────────────────────────────────────────────


@router.post("/send-otp")
def send_otp(phone: str, db: Session = Depends(get_db)):
    """
    Send a 6-digit OTP to the given phone number via WhatsApp.
    Creates the user record if it doesn't exist yet.
    """
    try:
        phone = _normalise_phone(phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate 6-digit OTP
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    from db.database import SupabaseSession
    if isinstance(db, SupabaseSession):
        # Invalidate previous unused OTPs
        db.sb.table("otp_codes").update({"is_used": True}).eq("phone", phone).eq("is_used", False).execute()
        
        # Store new OTP
        data = {
            "phone": phone,
            "code": code,
            "is_used": False,
            "expires_at": expires_at.isoformat(),
        }
        db.sb.table("otp_codes").insert(data).execute()
        
        # Send via WhatsApp
        sent = _send_otp_whatsapp(phone, code)
        if not sent:
            raise HTTPException(status_code=502, detail="Failed to send OTP. Check Twilio config.")
    
        return {"detail": "OTP sent via WhatsApp", "expires_in_seconds": settings.OTP_EXPIRY_MINUTES * 60}

    # Invalidate any previous unused OTPs for this phone
    db.query(OTPCode).filter(
        OTPCode.phone == phone,
        OTPCode.is_used == False,  # noqa: E712
    ).update({"is_used": True})

    # Store new OTP
    otp = OTPCode(phone=phone, code=code, expires_at=expires_at)
    db.add(otp)
    db.commit()

    # Send via WhatsApp
    sent = _send_otp_whatsapp(phone, code)
    if not sent:
        raise HTTPException(status_code=502, detail="Failed to send OTP. Check Twilio config.")

    return {"detail": "OTP sent via WhatsApp", "expires_in_seconds": settings.OTP_EXPIRY_MINUTES * 60}


@router.post("/verify-otp")
def verify_otp(phone: str, code: str, db: Session = Depends(get_db)):
    """
    Verify the OTP code and return a JWT token on success.
    Auto-creates the user if first login.
    """
    try:
        phone = _normalise_phone(phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.now(timezone.utc)
    
    from db.database import SupabaseSession
    if isinstance(db, SupabaseSession):
        # 1. Check OTP
        otp_res = db.sb.table("otp_codes").select("*").eq("phone", phone).eq("code", code).eq("is_used", False).gt("expires_at", now.isoformat()).order("created_at", desc=True).limit(1).execute()
        if not otp_res.data:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        otp_id = otp_res.data[0]['id']
        
        # 2. Get or create user
        user_res = db.sb.table("users").select("*").eq("phone_number", phone).limit(1).execute()
        if not user_res.data:
            logger.info(f"Creating new user for phone: {phone}")
            new_user_res = db.sb.table("users").insert({"phone_number": phone, "last_login": now.isoformat()}).execute()
            user_data = new_user_res.data[0]
        else:
            user_data = user_res.data[0]
            db.sb.table("users").update({"last_login": now.isoformat()}).eq("id", user_data['id']).execute()
            
        token = _create_token(phone)
        
        # 3. Mark OTP as used
        db.sb.table("otp_codes").update({"is_used": True}).eq("id", otp_id).execute()
        
        return {
            "token": token,
            "user": {
                "id": user_data['id'],
                "phone_number": user_data.get('phone_number'),
                "name": user_data.get('name'),
                "created_at": user_data.get('created_at') or now.isoformat(),
            },
        }

    otp = (
        db.query(OTPCode)
        .filter(
            OTPCode.phone == phone,
            OTPCode.code == code,
            OTPCode.is_used == False,  # noqa: E712
            OTPCode.expires_at > now,
        )
        .order_by(OTPCode.created_at.desc())
        .first()
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    try:
        # Upsert user
        user = db.query(User).filter(User.phone_number == phone).first()
        if not user:
            logger.info(f"Creating new user for phone: {phone}")
            user = User(phone_number=phone)
            db.add(user)
            db.flush() # Get ID without committing yet
        
        user.last_login = now
        
        # Generate token BEFORE marking OTP as used
        token = _create_token(phone)

        # Only if everything above worked, mark OTP as used
        otp.is_used = True
        db.commit()
        db.refresh(user)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": user.name,
                "created_at": user.created_at.isoformat() if user.created_at else now.isoformat(),
            },
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error in verify_otp for {phone}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {type(e).__name__}")



@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    created_at = getattr(user, 'created_at', None)
    if created_at and hasattr(created_at, 'isoformat'):
        created_at_str = created_at.isoformat()
    elif isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = None
        
    return {
        "id": getattr(user, 'id', None),
        "phone_number": getattr(user, 'phone_number', None),
        "name": getattr(user, 'name', None),
        "created_at": created_at_str,
    }
