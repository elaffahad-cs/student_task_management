# ★ ملف جديد: فحص العضوية وصلاحية الأدمن للمجموعات
"""
Access helpers: check group membership and roles.
Used by routers to make sure a user may touch a group's data.
"""

from Supabase.client import supabase


def get_membership(group_id: str, user_id: str) -> dict | None:
    """Returns the membership row (with role) or None if the user is not in the group."""
    res = (
        supabase.table("group_members")
        .select("id, role")
        .eq("group_id", group_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def is_group_member(group_id: str, user_id: str) -> bool:
    return get_membership(group_id, user_id) is not None


def is_group_admin(group_id: str, user_id: str) -> bool:
    membership = get_membership(group_id, user_id)
    return bool(membership and membership.get("role") == "admin")