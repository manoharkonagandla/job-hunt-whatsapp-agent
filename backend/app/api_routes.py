"""
REST API used by the React dashboard.

It reads and writes the same SQLite tables the WhatsApp agent uses, so the
chat surface and the web surface always show the same data.

Config (environment variables):
  OWNER_PHONE      e.g. "whatsapp:+91XXXXXXXXXX". If set, the API only shows
                   that number's applications. If unset, it shows all rows
                   (fine for a single-user personal tool).
  DASHBOARD_TOKEN  If set, every /api request must send it in the
                   X-API-Key header. Set this before deploying publicly.
"""
import os
import hmac
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app import db

Status = Literal["applied", "interviewing", "offer", "rejected", "withdrawn"]


def require_token(x_api_key: Optional[str] = Header(default=None)):
    expected = os.environ.get("DASHBOARD_TOKEN")
    if not expected:
        return  # auth disabled (local dev)
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


router = APIRouter(prefix="/api", dependencies=[Depends(require_token)])


class NewApplication(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: Optional[str] = Field(default=None, max_length=120)
    status: Status = "applied"


class StatusUpdate(BaseModel):
    status: Status


def _owner():
    return os.environ.get("OWNER_PHONE") or "dashboard"


def _visible(row) -> bool:
    owner = os.environ.get("OWNER_PHONE")
    return row is not None and (not owner or row["user_phone"] == owner)


@router.get("/applications")
def list_applications():
    owner = os.environ.get("OWNER_PHONE")
    return db.list_applications(owner) if owner else db.list_all_applications()


@router.post("/applications", status_code=201)
def create_application(payload: NewApplication):
    new_id = db.add_application(_owner(), payload.company.strip().title(), payload.role, payload.status)
    return db.get_application(new_id)


@router.patch("/applications/{app_id}")
def patch_application(app_id: int, payload: StatusUpdate):
    if not _visible(db.get_application(app_id)):
        raise HTTPException(status_code=404, detail="Application not found")
    db.update_status_by_id(app_id, payload.status)
    return db.get_application(app_id)
