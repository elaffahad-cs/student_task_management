"""
Users router: search for users (to add them to a group).
Requires a valid Supabase JWT.
"""
# ★ معدل: البحث يتطلب تسجيل دخول
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, AuthenticatedUser
from Supabase.client import supabase

router = APIRouter()


# ============================================================
# SEARCH USERS → GET /api/v1/users/search?q=...
# ============================================================
@router.get("/users/search")
async def search_users(
    q: str,
    limit: int = 20,
    current: AuthenticatedUser = Depends(get_current_user),
):
    # strip characters that would break the PostgREST filter string
    cleaned = q.strip().replace(",", " ").replace("(", " ").replace(")", " ")
    if len(cleaned) < 2:
        raise HTTPException(status_code=422, detail="Search text must be at least 2 characters.")

    try:
        result = (
            supabase.table("profiles")
            .select("id, full_name, email")
            .or_(f"full_name.ilike.%{cleaned}%,email.ilike.%{cleaned}%")
            .limit(min(limit, 50))
            .execute()
        )
        return {"users": result.data, "count": len(result.data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))