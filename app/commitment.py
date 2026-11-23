"""
Commitment router: calculates and stores a user's Commitment Index,
and shows the scores of all members in a group. Requires a valid Supabase JWT.
"""
# ★ معدل: التحقق من التوكن + الخصوصية، وإصلاح الـ except المكسور
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, AuthenticatedUser
from app.access import is_group_member
from ai.commitment_index import calculate_commitment_index
from Supabase.client import supabase

router = APIRouter()

COMPLETED_STATUS = "completed"  # must match the value used when a task is finished


def _parse_deadline(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _compute_for_user(user_id: str):
    """Reads the user's tasks, runs the algorithm, saves the score."""
    tasks = (
        supabase.table("tasks")
        .select("status, deadline")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    now = datetime.now(timezone.utc)
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == COMPLETED_STATUS)
    overdue = 0
    for t in tasks:
        deadline = _parse_deadline(t.get("deadline"))
        if t["status"] != COMPLETED_STATUS and deadline and deadline < now:
            overdue += 1

    result = calculate_commitment_index(total, completed, overdue)

    supabase.table("profiles").update(
        {"commitment_index_score": result.score}
    ).eq("id", user_id).execute()

    return result


# ============================================================
# USER SCORE → GET /api/v1/commitment/{user_id}
# a user can only see their own score
# ============================================================
@router.get("/commitment/{user_id}")
async def get_commitment(user_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    if user_id != current.user_id:
        raise HTTPException(status_code=403, detail="You can only view your own score.")

    try:
        return _compute_for_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GROUP SCORES → GET /api/v1/groups/{group_id}/commitment
# only members of the group can see the board
# ============================================================
@router.get("/groups/{group_id}/commitment")
async def get_group_commitment(group_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    if not is_group_member(group_id, current.user_id):
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    try:
        members = (
            supabase.table("group_members")
            .select("user_id, profiles(full_name)")
            .eq("group_id", group_id)
            .execute()
            .data
        )

        board = []
        for m in members:
            result = _compute_for_user(m["user_id"])
            board.append({
                "user_id": m["user_id"],
                "name": (m.get("profiles") or {}).get("full_name"),
                **result.model_dump(),
            })

        board.sort(key=lambda x: x["score"], reverse=True)
        return {"members": board, "count": len(board)}

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))