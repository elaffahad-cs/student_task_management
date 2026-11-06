"""
Commitment Index
----------------
Evaluates a student's long-term discipline based on task completion history.
The score (0-100) reflects both reliability and timeliness.

Formula:
    Base = (Completed / Total) * 100
    Penalty = (Overdue / Total) * 50
    Final = clamp(Base - Penalty, 0, 100)
"""

from pydantic import BaseModel, Field


class CommitmentResult(BaseModel):
    """Structured output for the Commitment Index."""
    score: float = Field(description="Score from 0.0 to 100.0.")
    grade: str = Field(description="Letter grade A-F.")
    label: str = Field(description="User-facing label (Excellent/Good/At Risk).")
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int


def _grade(score: float) -> tuple[str, str]:
    """Maps a numeric score to a letter grade and label."""
    if score >= 90:
        return "A", "Excellent"
    elif score >= 75:
        return "B", "Good"
    elif score >= 60:
        return "C", "Fair"
    elif score >= 40:
        return "D", "Needs Improvement"
    return "F", "At Risk"


def calculate_commitment_index(
    total_tasks: int,
    completed_tasks: int,
    overdue_tasks: int,
) -> CommitmentResult:
    """
    Calculates the Commitment Index.

    Args:
        total_tasks: Total number of tasks assigned to the student.
        completed_tasks: Number of tasks marked as 'completed'.
        overdue_tasks: Number of tasks that missed their deadline.

    Returns:
        CommitmentResult with score, grade, and label.
    """
    # Edge cases: validate inputs
    if total_tasks < 0 or completed_tasks < 0 or overdue_tasks < 0:
        raise ValueError("Task counts cannot be negative.")

    if completed_tasks > total_tasks:
        raise ValueError("Completed tasks cannot exceed total tasks.")

    # New user with no tasks → neutral perfect score
    if total_tasks == 0:
        return CommitmentResult(
            score=100.0,
            grade="A",
            label="New User",
            total_tasks=0,
            completed_tasks=0,
            overdue_tasks=0,
        )

    completion_rate = completed_tasks / total_tasks
    overdue_rate = overdue_tasks / total_tasks

    raw_score = (completion_rate * 100) - (overdue_rate * 50)
    final_score = round(max(0.0, min(100.0, raw_score)), 2)

    grade, label = _grade(final_score)

    return CommitmentResult(
        score=final_score,
        grade=grade,
        label=label,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
    )