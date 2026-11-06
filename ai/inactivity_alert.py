"""
Inactivity Alert System
-----------------------
Implements the inactivity detection logic from Figure 8.
If (now - last_activity) > threshold → send a motivational notification.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class InactivityResult(BaseModel):
    """Structured output for the inactivity check."""
    should_alert: bool = Field(description="True if an alert should be triggered.")
    hours_inactive: float = Field(description="Hours since the last activity.")
    message: str = Field(description="The notification message to send.")
    severity: str = Field(description="'none', 'warning', or 'critical'.")


def _parse_timestamp(ts_str: str) -> datetime:
    """Safely parses an ISO timestamp into a timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid timestamp format: {ts_str}") from e


def check_inactivity(
    last_activity_str: str,
    warning_hours: int = 24,
    critical_hours: int = 72,
) -> InactivityResult:
    """
    Checks if the user has been inactive for longer than the threshold.

    Args:
        last_activity_str: ISO 8601 timestamp of the user's last activity.
        warning_hours: Hours before a 'warning' alert is sent (default 24h).
        critical_hours: Hours before a 'critical' alert is sent (default 72h).

    Returns:
        InactivityResult with alert status and message.
    """
    last_activity = _parse_timestamp(last_activity_str)
    now = datetime.now(timezone.utc)

    hours_inactive = (now - last_activity).total_seconds() / 3600

    if hours_inactive >= critical_hours:
        return InactivityResult(
            should_alert=True,
            hours_inactive=round(hours_inactive, 1),
            message="⚠️ You've been away for over 3 days! Your deadlines are approaching. "
                    "Let's tackle one small task right now.",
            severity="critical",
        )
    elif hours_inactive >= warning_hours:
        return InactivityResult(
            should_alert=True,
            hours_inactive=round(hours_inactive, 1),
            message="You have pending tasks. Stay on track!",  # From Figure 8
            severity="warning",
        )
    else:
        return InactivityResult(
            should_alert=False,
            hours_inactive=round(hours_inactive, 1),
            message="User is active.",
            severity="none",
        )