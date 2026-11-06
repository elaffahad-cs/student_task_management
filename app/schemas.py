"""
Pydantic schemas — the API contract between Flutter and FastAPI.
Field names match the database columns exactly.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# PROFILE
# ============================================================
class ProfileResponse(BaseModel):
    id: str
    nickname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    avatar_path: Optional[str] = None
    numoftasks: int = 0
    progrissbar: int = 100
    updated_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    username: Optional[str] = None
    avatar_path: Optional[str] = None


# ============================================================
# TASK
# ============================================================
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    subject_name: Optional[str] = None
    deadline: datetime
    subject_importance: int = Field(default=3, ge=1, le=5)
    complexity: int = Field(default=3, ge=1, le=5)
    group_id: Optional[str] = None   # None = personal task


class SubtaskResponse(BaseModel):
    id: str
    task_id: str
    title: str
    estimated_hours: float
    is_completed: bool
    created_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    user_id: str
    group_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    subject_name: Optional[str] = None
    deadline: datetime
    subject_importance: int
    complexity: int
    priority_level: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    subtasks: List[SubtaskResponse] = []


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|completed|overdue)$")


# ============================================================
# GROUP
# ============================================================
class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = "folder"


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    member_count: int = 0


class GroupMemberResponse(BaseModel):
    id: str
    group_id: str
    user_id: str
    role: Optional[str] = "member"
    joined_at: Optional[datetime] = None
    profile: Optional[ProfileResponse] = None


class AddMemberRequest(BaseModel):
    user_id: str


# ============================================================
# NOTIFICATION
# ============================================================
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: Optional[datetime] = None


# ============================================================
# AI / UTILITY
# ============================================================
class InactivityCheckRequest(BaseModel):
    last_activity_time: str


# Resolve forward references
TaskResponse.model_rebuild()