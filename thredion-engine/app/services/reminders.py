
import logging
from datetime import datetime, timedelta
from typing import List

from twilio.rest import Client as TwilioClient
from core.config import settings
from app.services import supabase_client
from app.models.schemas import WeeklySummary

logger = logging.getLogger(__name__)

def generate_weekly_report(phone_number: str) -> str:
    """Generates a WhatsApp-formatted weekly cognitive summary."""
    user = supabase_client.get_or_create_user(phone_number)
    entries = supabase_client.get_weekly_entries(user.id)
    
    if not entries:
        return "🧠 *Thredion Weekly Recap*\n\nQuiet week! Send me some links, thoughts, or reflections to start building your cognitive layer."

    # Stats
    stats = {"learn": 0, "think": 0, "reflect": 0}
    for e in entries:
        stats[e.cognitive_mode] += 1
        
    # Find top actionable item
    actionable_items = sorted(
        [e for e in entries if e.actionability_score > 0.6], 
        key=lambda x: x.actionability_score, 
        reverse=True
    )
    
    top_piece = actionable_items[0] if actionable_items else entries[0]

    report = [
        "🧠 *Thredion Weekly Recap*",
        f"_{datetime.now().strftime('%b %d')} recap for your digital mind_",
        "",
        "📊 *Your Activity:*",
        f"• 📚 *Learn:* {stats['learn']} items consumed",
        f"• 💡 *Think:* {stats['think']} ideas born",
        f"• 🪞 *Reflect:* {stats['reflect']} inner thoughts",
        "",
        "🌟 *Top Actionable Insight:*",
        f"*{top_piece.title}*",
        f"_{top_piece.summary[:150]}..._",
        "",
        "🔗 View your full dashboard:",
        f"{settings.FRONTEND_URL}/cognitive"
    ]
    
    return "\n".join(report)

async def send_weekly_reminder(phone_number: str):
    """Sends the weekly report via Twilio WhatsApp."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.error("Twilio credentials missing for reminder.")
        return
        
    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message_body = generate_weekly_report(phone_number)
        
        # Twilio phone numbers are often formatted with 'whatsapp:' prefix
        to_number = f"whatsapp:+{phone_number.strip('+')}"
        from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
        
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        logger.info(f"Weekly reminder sent to {phone_number}: {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Failed to send weekly reminder: {e}")
        return None
