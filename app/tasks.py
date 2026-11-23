from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

"""
Tasks router: CRUD with authentication and ownership checks.
The user is identified from the Supabase JWT (Authorization: Bearer <token>).
"""
import uuid

from app.auth import get_current_user, AuthenticatedUser
from app.access import is_group_member
from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
)
from ai.priority_engine import calculate_priority
from ai.task_decomposer import decompose_academic_task
from Supabase.client import supabase

router = APIRouter()


# ------------------------------------------------------------
# helpers
# ------------------------------------------------------------
def _get_task_or_404(task_id: str) -> dict:
    res = supabase.table("tasks").select("*").eq("id", task_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found.")
    return res.data[0]


def _require_owner(task: dict, user_id: str) -> None:
    if task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this task.")


# ============================================================
# CREATE TASK  →  POST /api/v1/tasks
# ============================================================
@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, current: AuthenticatedUser = Depends(get_current_user)):
    user_id = current.user_id

    # a group task is only allowed for members of that group
    if task.group_id and not is_group_member(task.group_id, user_id):
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    try:
        # 1. AI: priority
        priority = calculate_priority(
            deadline_str=task.deadline.isoformat(),
            subject_importance=task.subject_importance,
            complexity=task.complexity,
        )

        # 2. AI: decomposition
        ai_result = decompose_academic_task(task.title, task.description or "")

        task_id = str(uuid.uuid4())

        # 3. Insert task
        task_row = {
            "id": task_id,
            "user_id": user_id,
            "group_id": task.group_id,
            "title": task.title,
            "description": task.description,
            "subject_name": task.subject_name,
            "deadline": task.deadline.isoformat(),
            "subject_importance": task.subject_importance,
            "complexity": task.complexity,
            "priority_level": priority.priority_score,
            "status": "pending",
        }

        inserted = supabase.table("tasks").insert(task_row).execute()
        if not inserted.data:
            raise HTTPException(status_code=400, detail="Failed to insert task.")

        # 4. Insert subtasks (only if AI said complex)
        subtasks_out = []
        if ai_result.is_complex and ai_result.subtasks:
            subtask_rows = [
                {
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "title": sub.title,
                    "estimated_hours": sub.estimated_hours,
                    "is_completed": False,
                }
                for sub in ai_result.subtasks
            ]
            subtasks_out = supabase.table("subtasks").insert(subtask_rows).execute().data

        # 5. Return
        return TaskResponse(**inserted.data[0], subtasks=subtasks_out)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ============================================================
# LIST MY TASKS  →  GET /api/v1/tasks?group_id=...
# ============================================================
@router.get("/tasks")
async def list_tasks(
    group_id: str | None = None,
    current: AuthenticatedUser = Depends(get_current_user),
):
    try:
        query = (
            supabase.table("tasks")
            .select("*, subtasks(*)")
            .eq("user_id", current.user_id)
        )
        if group_id:
            query = query.eq("group_id", group_id)

        result = query.order("priority_level", desc=True).execute()
        return {"tasks": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GET ONE TASK  →  GET /api/v1/tasks/{task_id}
# owner, or a member of the task's group
# ============================================================
@router.get("/tasks/{task_id}")
async def get_task(task_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    try:
        res = (
            supabase.table("tasks")
            .select("*, subtasks(*)")
            .eq("id", task_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Task not found.")

        task = res.data[0]
        is_owner = task["user_id"] == current.user_id
        in_group = bool(task.get("group_id")) and is_group_member(task["group_id"], current.user_id)
        if not (is_owner or in_group):
            raise HTTPException(status_code=403, detail="You do not have access to this task.")

        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# UPDATE STATUS  →  PATCH /api/v1/tasks/{task_id}/status
# ============================================================
@router.patch("/tasks/{task_id}/status")
async def update_status(
    task_id: str,
    body: TaskStatusUpdate,
    current: AuthenticatedUser = Depends(get_current_user),
):
    try:
        task = _get_task_or_404(task_id)
        _require_owner(task, current.user_id)

        result = (
            supabase.table("tasks")
            .update({"status": body.status})
            .eq("id", task_id)
            .execute()
        )
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TOGGLE SUBTASK  →  PATCH /api/v1/subtasks/{subtask_id}/toggle
# ============================================================
@router.patch("/subtasks/{subtask_id}/toggle")
async def toggle_subtask(subtask_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    try:
        res = (
            supabase.table("subtasks")
            .select("*")
            .eq("id", subtask_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Subtask not found.")
        subtask = res.data[0]

        # the subtask belongs to its parent task, so check the parent's owner
        _require_owner(_get_task_or_404(subtask["task_id"]), current.user_id)

        result = (
            supabase.table("subtasks")
            .update({"is_completed": not subtask["is_completed"]})
            .eq("id", subtask_id)
            .execute()
        )
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# DELETE TASK  →  DELETE /api/v1/tasks/{task_id}
# ============================================================
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    try:
        task = _get_task_or_404(task_id)
        _require_owner(task, current.user_id)

        supabase.table("tasks").delete().eq("id", task_id).execute()
        return {"deleted": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# BREAKDOWN PREVIEW  →  POST /api/v1/tasks/breakdown
# Returns suggested subtasks WITHOUT saving anything.
# ============================================================
class BreakdownRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


@router.post("/tasks/breakdown")
async def preview_breakdown(
    body: BreakdownRequest,
    current: AuthenticatedUser = Depends(get_current_user),
):
    result = decompose_academic_task(body.title, body.description or "")
    return result.model_dump()