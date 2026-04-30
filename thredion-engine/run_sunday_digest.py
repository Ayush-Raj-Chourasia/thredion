import asyncio
import logging
from app.services import reminders, supabase_client
from core.config import settings
from twilio.rest import Client as TwilioClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_digest_for_all_users():
    """Runs the Sunday Digest for all active users (V1)."""
    users = supabase_client.get_all_users()
    
    for user in users:
        phone = user.phone_number
        logger.info(f"Processing Sunday Digest for {phone}...")
        
        # 1. Generate Spec-Compliant Weekly Report
        full_message = reminders.generate_weekly_report(phone)
        
        # 2. Send via Twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                to_number = f"whatsapp:+{phone.replace('+', '')}"
                client.messages.create(
                    body=full_message,
                    from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    to=to_number
                )
                logger.info(f"Sent Sunday Digest to {phone}")
            except Exception as e:
                logger.error(f"Failed to send digest to {phone}: {e}")

if __name__ == "__main__":
    asyncio.run(run_digest_for_all_users())
