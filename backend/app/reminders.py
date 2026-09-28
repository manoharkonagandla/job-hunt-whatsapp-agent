from . import db
from .whatsapp import send_whatsapp

STALE_AFTER_DAYS = 7


def check_and_nudge():
    """Run once a day (see main.py scheduler). For every application still
    sitting at 'applied' with no update in STALE_AFTER_DAYS days, and that
    hasn't been nudged recently, send a follow-up reminder."""
    stale = db.stale_applications(stale_after_days=STALE_AFTER_DAYS)
    for app in stale:
        msg = (f"Hey — it's been {STALE_AFTER_DAYS}+ days since you applied to "
               f"{app['company']} ({app['role'] or 'role n/a'}) with no update. "
               f"Worth sending a follow-up email? Reply 'update {app['company']} interviewing' "
               f"or similar if something's changed.")
        send_whatsapp(app["user_phone"], msg)
        db.mark_nudged(app["id"])
