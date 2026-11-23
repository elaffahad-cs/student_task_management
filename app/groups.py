"""
Groups router: create group, list my groups, list members, add member, leave group.
All routes require a valid Supabase JWT.
"""
# ★ معدل: التحقق من التوكن + العضوية + صلاحية الأدمن
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user, AuthenticatedUser
from app.access import is_group_member, is_group_admin
from Supabase.client import supabase

router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class MemberAdd(BaseModel):
    user_id: str


# ============================================================
# CREATE GROUP → POST /api/v1/groups
# ============================================================
@router.post("/groups")
async def create_group(body: GroupCreate, current: AuthenticatedUser = Depends(get_current_user)):
    try:
        group_id = str(uuid.uuid4())

        group = (
            supabase.table("groups")
            .insert({
                "id": group_id,
                "name": body.name,
                "description": body.description,
                "created_by": current.user_id,
            })
            .execute()
        )
        if not group.data:
            raise HTTPException(status_code=400, detail="Failed to create group.")

        # the creator becomes the admin member
        supabase.table("group_members").insert({
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "user_id": current.user_id,
            "role": "admin",
        }).execute()

        return group.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MY GROUPS → GET /api/v1/groups
# ============================================================
@router.get("/groups")
async def list_my_groups(current: AuthenticatedUser = Depends(get_current_user)):
    try:
        result = (
            supabase.table("group_members")
            .select("role, groups(*)")
            .eq("user_id", current.user_id)
            .execute()
        )
        groups = [
            {**row["groups"], "my_role": row["role"]}
            for row in result.data
            if row.get("groups")
        ]
        return {"groups": groups, "count": len(groups)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GROUP MEMBERS → GET /api/v1/groups/{group_id}/members
# only members of the group can see its members
# ============================================================
@router.get("/groups/{group_id}/members")
async def list_members(group_id: str, current: AuthenticatedUser = Depends(get_current_user)):
    if not is_group_member(group_id, current.user_id):
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    try:
        result = (
            supabase.table("group_members")
            .select("role, profiles(*)")
            .eq("group_id", group_id)
            .execute()
        )
        return {"members": result.data, "count": len(result.data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ADD MEMBER → POST /api/v1/groups/{group_id}/members
# only an admin of the group can add members
# ============================================================
@router.post("/groups/{group_id}/members")
async def add_member(
    group_id: str,
    body: MemberAdd,
    current: AuthenticatedUser = Depends(get_current_user),
):
    if not is_group_admin(group_id, current.user_id):
        raise HTTPException(status_code=403, detail="Only a group admin can add members.")

    try:
        existing = (
            supabase.table("group_members")
            .select("id")
            .eq("group_id", group_id)
            .eq("user_id", body.user_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="User is already a member.")

        result = (
            supabase.table("group_members")
            .insert({
                "id": str(uuid.uuid4()),
                "group_id": group_id,
                "user_id": body.user_id,
                "role": "member",
            })
            .execute()
        )
        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# LEAVE GROUP → DELETE /api/v1/groups/{group_id}/members/{user_id}
# a user can remove themselves; an admin can remove other members
# ============================================================
@router.delete("/groups/{group_id}/members/{user_id}")
async def leave_group(
    group_id: str,
    user_id: str,
    current: AuthenticatedUser = Depends(get_current_user),
):
    is_self = user_id == current.user_id
    if not (is_self or is_group_admin(group_id, current.user_id)):
        raise HTTPException(status_code=403, detail="You can only remove yourself from a group.")

    try:
        result = (
            supabase.table("group_members")
            .delete()
            .eq("group_id", group_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Membership not found.")

        # if nobody is left, remove the empty group
        remaining = (
            supabase.table("group_members")
            .select("id")
            .eq("group_id", group_id)
            .execute()
        )
        group_deleted = False
        if not remaining.data:
            supabase.table("groups").delete().eq("id", group_id).execute()
            group_deleted = True

        return {"left": True, "group_id": group_id, "group_deleted": group_deleted}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))