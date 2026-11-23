"""
Notifications router: list / mark as read, record user activity,
and check a user's inactivity. All routes require a valid Supabase JWT.
"""
# ★ معدل: التحقق من التوكن + الإشعارات تخص المستخدم الحالي فقط
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, AuthenticatedUser
from ai.inactivity_alert import check_inactivity
from Supabase.client import supabase

router = APIRouter()


def _forbid_other_users(path_user_id: str, current: AuthenticatedUser) -> None:
    if path_user_id != current.user_id:
        raise HTTPException(status_code=403, detail="You can only access your own data.")


# ============================================================
# LIST → GET /api/v1/notifications?unread_only=false
# ============================================================
@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    current: AuthenticatedUser = Depends(get_current_user),
):
    try:
        query = supabase.table("notifications").select("*").eq("user_id", current.user_id)
        if unread_only:
            query = query.eq("is_read", False)
        result = query.order("created_at", desc=True).execute()
        return {"notifications": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MARK ALL READ → PATCH /api/v1/notifications/read-all
# ============================================================
@router.patch("/notifications/read-all")
async def mark_all_read(current: AuthenticatedUser = Depends(get_current_user)):
    try:
        result = (
            supabase.table("notifications")
            .update({"is_read": True})
            .eq("user_id", current.user_id)
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
async def mark_read(notification_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    try:
        res = (
            supabase.table("notifications")
            .select("id, user_id")
            .eq("id", notification_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Notification not found.")
        _forbid_other_users(res.data[0]["user_id"], current)

        result = (
            supabase.table("notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
            .execute()
        )
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
async def record_activity(user_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    _forbid_other_users(user_id, current)
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