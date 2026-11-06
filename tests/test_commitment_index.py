import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from ai.commitment_index import calculate_commitment_index


def test_new_user_gets_perfect_score():
    result = calculate_commitment_index(0, 0, 0)
    assert result.score == 100.0
    assert result.grade == "A"


def test_perfect_student():
    result = calculate_commitment_index(10, 10, 0)
    assert result.score == 100.0
    assert result.grade == "A"


def test_at_risk_student():
    result = calculate_commitment_index(10, 3, 5)
    # 30% completion - 25% overdue = 5.0
    assert result.score == 5.0
    assert result.grade == "F"


def test_negative_counts_raise_error():
    with pytest.raises(ValueError):
        calculate_commitment_index(-1, 0, 0)