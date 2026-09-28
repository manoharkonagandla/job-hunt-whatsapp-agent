# Job-Hunt Agent — WhatsApp agent + React dashboard

A full-stack app for tracking job applications. I text a WhatsApp agent
("applied to Swiggy for SDE intern") and it logs it; a React dashboard shows
the same data so I can filter, edit and see where things stand. Both talk to
one FastAPI backend and one database.

**Why I built it:** I kept losing track of which companies I'd applied to and
when to follow up. A spreadsheet felt like something I'd stop updating, so I
built something that lives in the app I already use all day.

```
WhatsApp ──> Twilio ──> /webhook ──┐
                                   ├──> FastAPI ──> SQLite
React dashboard ──> /api/* ────────┘        │
                                            └── daily job: nudges me about stale applications
```

## What's in it

**Backend** (`backend/`, Python + FastAPI)
- `app/agent.py` — Claude tool-use loop with three tools (`log_application`,
  `update_status`, `list_applications`) and conversation memory
- `app/db.py` — SQLite storage shared by both surfaces
- `app/api_routes.py` — REST API for the dashboard (`GET/POST/PATCH /api/applications`),
  validated with Pydantic, optional token auth, results scoped to the owner's number
- `app/whatsapp.py` + `main.py` — Twilio webhook (replies are XML-escaped)
- `app/reminders.py` — daily job that messages me when an application has sat at
  "applied" for 7+ days

**Frontend** (`frontend/`, React + Vite)
- Stats bar, status breakdown chart (Recharts), status filter tabs
- Application cards with inline status editing and a "Follow up?" badge for stale ones
- Add-application form, loading/error states, token prompt when the API is protected

## Run it locally

```bash
# 1. backend
cd backend
pip install -r requirements.txt
cp .env.example .env        # fill in keys
uvicorn main:app --reload   # http://localhost:8000

# 2. frontend (new terminal)
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

The dashboard works without WhatsApp/Twilio set up — you can add and edit
applications from the UI. To use the WhatsApp side, create a free Twilio
WhatsApp sandbox, join it from your phone, and point its webhook at
`https://<your-url>/webhook` (use ngrok locally).

## Deploy as one service

FastAPI serves the built React app when `frontend/dist` exists, so one server
does everything (no CORS needed in production).

- Build: `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
- Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set the env vars from `backend/.env.example`. **Set `DASHBOARD_TOKEN`** before
  making the URL public, otherwise anyone with the link can read your applications.
- SQLite lives on the server's disk. On hosts with an ephemeral filesystem
  (e.g. Render's free tier) the data resets on redeploy — attach a persistent
  disk/volume, or move to Postgres.

## API

| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `/api/applications` | — | list, newest first |
| POST | `/api/applications` | `{company, role?, status?}` | 201 + created row |
| PATCH | `/api/applications/{id}` | `{status}` | 404 if not yours |
| GET | `/health` | — | liveness |
| POST | `/webhook` | Twilio form | WhatsApp entry point |

Status is one of `applied | interviewing | offer | rejected | withdrawn`.
Send `X-API-Key: <DASHBOARD_TOKEN>` when a token is configured.

## Known limitations / next
- Single-user by design (one owner number), no real login
- The agent's LLM path needs live Anthropic + Twilio keys; I tested the API,
  DB, auth and webhook plumbing with the LLM call stubbed
- Next: parse forwarded rejection/interview emails, weekly digest, Postgres
