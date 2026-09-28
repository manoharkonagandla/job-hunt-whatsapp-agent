import os
from twilio.rest import Client

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox default

_client = Client(TWILIO_SID, TWILIO_AUTH) if TWILIO_SID and TWILIO_AUTH else None


def send_whatsapp(to_phone: str, body: str):
    """to_phone should look like 'whatsapp:+91xxxxxxxxxx'"""
    if not _client:
        print(f"[DRY RUN — no Twilio creds set] would send to {to_phone}: {body}")
        return
    _client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=to_phone, body=body)
