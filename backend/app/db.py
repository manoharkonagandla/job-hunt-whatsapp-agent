"""
Storage layer = the agent's memory.

Two things are remembered:
1. applications  -> structured record of every job you've told the agent about
2. messages      -> raw conversation history per user, so the agent has context
                     for follow-up messages like "actually make that 'interviewing'"
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PATH = "jobhunt.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT,
                status TEXT DEFAULT 'applied',
                applied_on TEXT NOT NULL,
                last_update TEXT NOT NULL,
                last_nudged TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT NOT NULL,
                role TEXT NOT NULL,      -- 'user' or 'agent'
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


# ---------- applications ----------

def add_application(user_phone: str, company: str, role: str | None, status: str = "applied") -> int:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO applications (user_phone, company, role, status, applied_on, last_update) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_phone, company, role, status, now, now),
        )
        return cur.lastrowid


def update_status(user_phone: str, company: str, status: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM applications WHERE user_phone=? AND company LIKE ? "
            "ORDER BY id DESC LIMIT 1",
            (user_phone, f"%{company}%"),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE applications SET status=?, last_update=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), row["id"]),
        )
        return True


def list_applications(user_phone: str, days: int | None = None):
    with get_db() as conn:
        if days:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                "SELECT * FROM applications WHERE user_phone=? AND applied_on >= ? ORDER BY applied_on DESC",
                (user_phone, since),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications WHERE user_phone=? ORDER BY applied_on DESC",
                (user_phone,),
            ).fetchall()
        return [dict(r) for r in rows]


def stale_applications(stale_after_days: int = 7):
    """Applications with status 'applied' that haven't moved in N days and
    haven't been nudged in the last N days either — used by the reminder job."""
    cutoff = (datetime.utcnow() - timedelta(days=stale_after_days)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM applications WHERE status='applied' AND last_update <= ? "
            "AND (last_nudged IS NULL OR last_nudged <= ?)",
            (cutoff, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_nudged(app_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE applications SET last_nudged=? WHERE id=?",
            (datetime.utcnow().isoformat(), app_id),
        )


# ---------- conversation memory ----------

def add_message(user_phone: str, role: str, content: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (user_phone, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_phone, role, content, datetime.utcnow().isoformat()),
        )


def recent_messages(user_phone: str, limit: int = 8):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_phone=? ORDER BY id DESC LIMIT ?",
            (user_phone, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


# ---------- helpers used by the REST API (dashboard) ----------

def get_application(app_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        return dict(row) if row else None


def update_status_by_id(app_id: int, status: str) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE applications SET status=?, last_update=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), app_id),
        )
        return cur.rowcount > 0


def list_all_applications():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM applications ORDER BY applied_on DESC").fetchall()
        return [dict(r) for r in rows]
