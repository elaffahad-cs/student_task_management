"""
Tasks router — basic CRUD.
Auth will be added in a later step.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import uuid

from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    SubtaskResponse,
)
from ai.priority_engine import calculate_priority
from ai.task_decomposer import decompose_academic_task
from Supabase.client import supabase

router = APIRouter()


# ============================================================
# CREATE TASK  →  POST /api/v1/tasks
# ============================================================
@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, user_id: str):
    """
    Temporary: user_id passed as a query parameter.
    Will be replaced by auth token in a later step.
    """
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
            sub_data = supabase.table("subtasks").insert(subtask_rows).execute().data
            subtasks_out = sub_data

        # 5. Return
        return TaskResponse(
            **inserted.data[0],
            subtasks=subtasks_out,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ============================================================
# LIST MY TASKS  →  GET /api/v1/tasks?user_id=...
# ============================================================
@router.get("/tasks")
async def list_tasks(user_id: str, group_id: str | None = None):
    try:
        query = supabase.table("tasks").select("*, subtasks(*)").eq("user_id", user_id)
        if group_id:
            query = query.eq("group_id", group_id)

        result = query.order("priority_level", desc=True).execute()
        return {"tasks": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GET ONE TASK  →  GET /api/v1/tasks/{task_id}
# ============================================================
@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    try:
        result = (
            supabase.table("tasks")
            .select("*, subtasks(*)")
            .eq("id", task_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found.")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# UPDATE STATUS  →  PATCH /api/v1/tasks/{task_id}/status
# ============================================================
@router.patch("/tasks/{task_id}/status")
async def update_status(task_id: str, body: TaskStatusUpdate):
    try:
        result = (
            supabase.table("tasks")
            .update({"status": body.status})
            .eq("id", task_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TOGGLE SUBTASK  →  PATCH /api/v1/subtasks/{subtask_id}/toggle
# ============================================================
@router.patch("/subtasks/{subtask_id}/toggle")
async def toggle_subtask(subtask_id: str):
    try:
        current = (
            supabase.table("subtasks")
            .select("is_completed")
            .eq("id", subtask_id)
            .single()
            .execute()
        )
        if not current.data:
            raise HTTPException(status_code=404, detail="Subtask not found.")

        new_value = not current.data["is_completed"]

        result = (
            supabase.table("subtasks")
            .update({"is_completed": new_value})
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
async def delete_task(task_id: str):
    try:
        result = supabase.table("tasks").delete().eq("id", task_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Task not found.")
        return {"deleted": True, "id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))