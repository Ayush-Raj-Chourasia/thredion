
import logging
from datetime import datetime, timedelta
from typing import List

from twilio.rest import Client as TwilioClient
from core.config import settings
from app.services import supabase_client
from app.models.schemas import WeeklySummary

logger = logging.getLogger(__name__)

def generate_weekly_report(phone_number: str) -> str:
    """Generates a WhatsApp-formatted weekly cognitive summary as per spec."""
    user = supabase_client.get_or_create_user(phone_number)
    entries = supabase_client.get_weekly_entries(user.id)
    
    if not entries:
        return "🧠 *Thredion Weekly Recap*\n\nQuiet week! Send me some links, thoughts, or reflections to start building your cognitive layer."

    learn_entries = [e for e in entries if e.cognitive_mode == 'learn']
    think_entries = [e for e in entries if e.cognitive_mode == 'think']
    reflect_entries = [e for e in entries if e.cognitive_mode == 'reflect']

    report = ["🧠 *Thredion Weekly Recap*", f"_{datetime.now().strftime('%b %d')} - Your Digital Mind_", ""]

    # Section 1: What You Learned
    report.append("📚 *Section 1: What You Learned*")
    report.append(f"• Total: {len(learn_entries)} items")
    if learn_entries:
        buckets = {}
        for e in learn_entries:
            buckets[e.bucket] = buckets.get(e.bucket, 0) + 1
        bucket_stats = ", ".join([f"{b}({c})" for b, c in sorted(buckets.items(), key=lambda x: x[1], reverse=True)])
        report.append(f"• Buckets: {bucket_stats}")
        report.append("• Top Highlights:")
        for e in learn_entries[:3]:
            report.append(f"  ↳ _{e.title}_")
    report.append("")

    # Section 2: What You Thought
    report.append("💡 *Section 2: What You Thought*")
    report.append(f"• Total Ideas: {len(think_entries)}")
    high_action = [e for e in think_entries if e.actionability_score > 0.7]
    if high_action:
        report.append(f"• 🔥 *High Actionability:*")
        for e in high_action[:2]:
            report.append(f"  ↳ *{e.title}* (Score: {int(e.actionability_score*100)}%)")
    elif think_entries:
        report.append(f"• Top Idea: _{think_entries[0].title}_")
    report.append("")

    # Section 3: What You Reflected On
    report.append("🪞 *Section 3: What You Reflected On*")
    report.append(f"• Total Reflections: {len(reflect_entries)}")
    if reflect_entries:
        buckets = {}
        for e in reflect_entries:
            buckets[e.bucket] = buckets.get(e.bucket, 0) + 1
        top_bucket = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[0][0]
        report.append(f"• Most Recurring Theme: *{top_bucket}*")
        report.append(f"• Summary: _{reflect_entries[0].summary[:100]}..._")
    
    report.append("")
    report.append(f"📊 *Full Dashboard:* {settings.FRONTEND_URL}/cognitive")
    
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
