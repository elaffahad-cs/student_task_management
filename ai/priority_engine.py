"""
Dynamic Priority Engine
-----------------------
Implements the priority scoring algorithm from Figure 7 of the Phase 1 report.
Score = (Urgency Weight * 2) + Subject Importance + Task Complexity
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class PriorityResult(BaseModel):
    """Structured output for the frontend to render priority badges."""
    priority_score: int = Field(description="Final score (3-15). Higher = more urgent.")
    urgency_weight: int = Field(description="Weight derived from days remaining (1-5).")
    days_remaining: int = Field(description="Days left until deadline (negative if overdue).")
    is_overdue: bool = Field(description="True if the deadline has passed.")
    label: str = Field(description="Human-readable priority label (Low/Medium/High/Critical).")


def _parse_deadline(deadline_str: str) -> datetime:
    """Safely parses an ISO date string into a timezone-aware datetime."""
    try:
        # Handles both 'Z' and '+00:00' suffixes
        dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        # If no timezone provided, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid deadline format: {deadline_str}") from e


def _urgency_weight(days_remaining: int) -> int:
    """Maps days remaining to an urgency weight (Figure 7 logic)."""
    if days_remaining < 0:      # Overdue
        return 5
    elif days_remaining <= 2:   # Critical
        return 5
    elif days_remaining <= 5:   # Medium
        return 3
    else:                        # Low
        return 1


def _priority_label(score: int) -> str:
    """Maps a numeric score to a user-facing label."""
    if score >= 13:
        return "Critical"
    elif score >= 9:
        return "High"
    elif score >= 6:
        return "Medium"
    return "Low"


def calculate_priority(
    deadline_str: str,
    subject_importance: int = 3,
    complexity: int = 3,
) -> PriorityResult:
    """
    Calculates the priority score for a task.

    Args:
        deadline_str: ISO 8601 formatted deadline (e.g., '2026-05-10T14:00:00Z').
        subject_importance: 1-5 scale (5 = most important subject).
        complexity: 1-5 scale (5 = most complex task).

    Returns:
        PriorityResult with score, label, and reasoning data.
    """
    # Clamp inputs to valid range [1, 5]
    subject_importance = max(1, min(5, subject_importance))
    complexity = max(1, min(5, complexity))

    deadline = _parse_deadline(deadline_str)
    now = datetime.now(timezone.utc)

    # Calculate days remaining (round down for "days left")
    delta = deadline - now
    days_remaining = delta.days

    urgency = _urgency_weight(days_remaining)
    score = (urgency * 2) + subject_importance + complexity

    return PriorityResult(
        priority_score=score,
        urgency_weight=urgency,
        days_remaining=days_remaining,
        is_overdue=days_remaining < 0,
        label=_priority_label(score),
    )