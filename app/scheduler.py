"""
Scheduler router: endpoints that QStash calls on a schedule.

QStash setup (Upstash console -> QStash -> Schedules):
  - URL:  https://<your-deployed-backend>/api/v1/scheduler/check-inactivity   (e.g. every 6 hours)
  - URL:  https://<your-deployed-backend>/api/v1/scheduler/deadline-reminders  (e.g. every hour)
  - Method: POST
  - Header: Upstash-Forward-x-scheduler-secret: <same value as SCHEDULER_SECRET in .env>

QStash cannot call localhost, so the backend must be deployed first.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException

from ai.inactivity_alert import check_inactivity
from Supabase.client import supabase

router = APIRouter()


def _verify(secret: str | None):
    expected = os.environ.get("SCHEDULER_SECRET")
    if not expected:
        raise HTTPException(status_code=500, detail="SCHEDULER_SECRET is not set.")
    if secret != expected:
        raise HTTPException(status_code=401, detail="Unauthorized.")


def _already_sent(user_id: str, type_: str, since: datetime, message: str | None = None) -> bool:
    query = (
        supabase.table("notifications")
        .select("id")
        .eq("user_id", user_id)
        .eq("type", type_)
        .gte("created_at", since.isoformat())
    )
    if message:
        query = query.eq("message", message)
    return bool(query.limit(1).execute().data)


# ============================================================
# INACTIVITY → POST /api/v1/scheduler/check-inactivity
# ============================================================
@router.post("/scheduler/check-inactivity")
async def run_inactivity_check(x_scheduler_secret: str | None = Header(default=None)):
    _verify(x_scheduler_secret)
    try:
        profiles = supabase.table("profiles").select("id, last_activity").execute().data
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        sent = 0

        for p in profiles:
            if not p.get("last_activity"):
                continue
            result = check_inactivity(p["last_activity"])
            if result.should_alert and not _already_sent(p["id"], "inactivity", since):
                supabase.table("notifications").insert({
                    "user_id": p["id"],
                    "message": result.message,
                    "type": "inactivity",
                }).execute()
                sent += 1

        return {"checked": len(profiles), "alerts_sent": sent}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# DEADLINES → POST /api/v1/scheduler/deadline-reminders
# ============================================================
@router.post("/scheduler/deadline-reminders")
async def run_deadline_reminders(x_scheduler_secret: str | None = Header(default=None)):
    _verify(x_scheduler_secret)
    try:
        now = datetime.now(timezone.utc)
        soon = now + timedelta(hours=24)

        tasks = (
            supabase.table("tasks")
            .select("id, user_id, title, deadline, status")
            .neq("status", "completed")
            .gte("deadline", now.isoformat())
            .lte("deadline", soon.isoformat())
            .execute()
            .data
        )

        sent = 0
        for t in tasks:
            message = f"Reminder: '{t['title']}' is due within 24 hours."
            if not _already_sent(t["user_id"], "deadline", now - timedelta(hours=24), message):
                supabase.table("notifications").insert({
                    "user_id": t["user_id"],
                    "message": message,
                    "type": "deadline",
                }).execute()
                sent += 1

        return {"tasks_due_soon": len(tasks), "reminders_sent": sent}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))