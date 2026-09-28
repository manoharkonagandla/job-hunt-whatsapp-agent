import os
from xml.sax.saxutils import escape

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

from app import db
from app.agent import handle_message
from app.api_routes import router as api_router
from app.reminders import check_and_nudge

app = FastAPI(title="Job-Hunt Agent (WhatsApp + Dashboard)")

# The React dev server runs on :5173. In production the built frontend is
# served by this same app (see bottom of file), so CORS isn't needed there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup():
    db.init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_nudge, "cron", hour=9)  # 9am daily nudge check
    scheduler.start()


@app.get("/health")
def health():
    return {"status": "ok", "service": "job-hunt-agent"}


@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Twilio posts form-encoded data here for every incoming WhatsApp message."""
    form = await request.form()
    from_number = form.get("From", "")   # e.g. 'whatsapp:+91xxxxxxxxxx'
    body = form.get("Body", "").strip()

    if not body:
        return Response(status_code=200)

    reply_text = handle_message(from_number, body)

    # escape() so characters like & or < in the reply can't break the XML
    twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{escape(reply_text)}</Message></Response>"
    return Response(content=twiml, media_type="application/xml")


# Serve the built React app (frontend/dist) from the same server, if present.
# Mounted last so /api, /webhook and /health take priority.
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
