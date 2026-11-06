import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timedelta, timezone
from ai.priority_engine import calculate_priority


def _future_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_overdue_task_is_critical():
    deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    result = calculate_priority(deadline, subject_importance=5, complexity=5)
    assert result.is_overdue is True
    assert result.label == "Critical"
    # Formula: (urgency * 2) + importance + complexity
    # urgency=5, importance=5, complexity=5 → 20
    assert result.priority_score == 20


def test_far_task_is_low_priority():
    result = calculate_priority(_future_iso(30), subject_importance=1, complexity=1)
    assert result.label == "Low"
    # urgency=1, importance=1, complexity=1 → (1*2)+1+1 = 4
    assert result.priority_score == 4


def test_invalid_deadline_raises_error():
    with pytest.raises(ValueError):
        calculate_priority("not-a-date")


def test_inputs_are_clamped():
    # Passing out-of-range values should be clamped to [1, 5]
    # urgency=5, clamped importance=5, clamped complexity=1 → (5*2)+5+1 = 16
    result = calculate_priority(_future_iso(1), subject_importance=99, complexity=-5)
    assert result.priority_score == 16