import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta, timezone
from ai.inactivity_alert import check_inactivity


def _hours_ago(h: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()


def test_active_user_no_alert():
    result = check_inactivity(_hours_ago(2))
    assert result.should_alert is False
    assert result.severity == "none"


def test_warning_after_24_hours():
    result = check_inactivity(_hours_ago(30))
    assert result.should_alert is True
    assert result.severity == "warning"


def test_critical_after_72_hours():
    result = check_inactivity(_hours_ago(100))
    assert result.should_alert is True
    assert result.severity == "critical"