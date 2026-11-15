"""
Notifications router: list / mark as read, record user activity,
and check a single user's inactivity.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ai.inactivity_alert import check_inactivity
from Supabase.client import supabase

router = APIRouter()


# ============================================================
# LIST → GET /api/v1/notifications?user_id=...&unread_only=false
# ============================================================
@router.get("/notifications")
async def list_notifications(user_id: str, unread_only: bool = False):
    try:
        query = supabase.table("notifications").select("*").eq("user_id", user_id)
        if unread_only:
            query = query.eq("is_read", False)
        result = query.order("created_at", desc=True).execute()
        return {"notifications": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MARK ALL READ → PATCH /api/v1/notifications/read-all?user_id=...
# ============================================================
@router.patch("/notifications/read-all")
async def mark_all_read(user_id: str):
    try:
        result = (
            supabase.table("notifications")
            .update({"is_read": True})
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return {"updated": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MARK ONE READ → PATCH /api/v1/notifications/{id}/read
# ============================================================
@router.patch("/notifications/{notification_id}/read")
async def mark_read(notification_id: str):
    try:
        result = (
            supabase.table("notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RECORD ACTIVITY → POST /api/v1/users/{user_id}/activity
# (Flutter calls this when the app opens / a task is changed)
# ============================================================
@router.post("/users/{user_id}/activity")
async def record_activity(user_id: str):
    try:
        now = datetime.now(timezone.utc).isoformat()
        result = (
            supabase.table("profiles")
            .update({"last_activity": now})
            .eq("id", user_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"user_id": user_id, "last_activity": now}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CHECK INACTIVITY → GET /api/v1/users/{user_id}/inactivity
# ============================================================
@router.get("/users/{user_id}/inactivity")
async def user_inactivity(user_id: str):
    try:
        row = (
            supabase.table("profiles")
            .select("last_activity")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not row.data or not row.data.get("last_activity"):
            raise HTTPException(status_code=404, detail="No activity recorded.")
        return check_inactivity(row.data["last_activity"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))