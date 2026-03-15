
import asyncio
import logging
from app.services import reminders, synthesis, supabase_client
from core.config import settings
from twilio.rest import Client as TwilioClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_digest_for_all_users():
    """Runs the Sunday Digest for all active users."""
    # 1. Get all unique phone numbers from cognitive entries
    # For now, we'll just use the primary test user or fetch from DB
    users = supabase_client.get_all_users()
    
    for user in users:
        phone = user.phone_number
        logger.info(f"Processing Sunday Digest for {phone}...")
        
        # 2. Generate Synthesis
        syn = await synthesis.synthesize_week(phone)
        
        # 3. Generate Weekly Report
        basic_report = reminders.generate_weekly_report(phone)
        
        # 4. Combine into Sunday Digest
        digest = [
            basic_report,
            "",
            "✨ *Weekly Synthesis*",
        ]
        
        if syn.get("themes"):
            digest.append("*Major Themes:*")
            digest.extend([f" • {t}" for t in syn["themes"]])
            
        if syn.get("patterns"):
            digest.append("\n*Actionable Patterns:*")
            digest.extend([f" • {p}" for p in syn["patterns"]])
            
        if syn.get("gaps"):
            digest.append("\n*Curiosity Gaps:*")
            digest.extend([f" • {g}" for g in syn["gaps"]])
            
        full_message = "\n".join(digest)
        
        # 5. Send via Twilio
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
