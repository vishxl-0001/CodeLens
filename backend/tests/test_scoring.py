from __future__ import annotations

import pytest
from app.analyzer.engine import analyze_code
from app.scoring import compute_scores_and_grade, calculate_grade
from app.models import Issue, FunctionMetric


def test_clean_code_scores_high():
    clean_code = '''"""A clean module demonstrating high-quality code."""

def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b
'''
    res = analyze_code(clean_code)
    assert res.score >= 95
    assert res.grade == "A"
    assert len(res.issues) == 0


def test_grade_boundaries():
    assert calculate_grade(95) == "A"
    assert calculate_grade(90) == "A"
    assert calculate_grade(85) == "B"
    assert calculate_grade(75) == "B"
    assert calculate_grade(65) == "C"
    assert calculate_grade(60) == "C"
    assert calculate_grade(50) == "D"
    assert calculate_grade(40) == "D"
    assert calculate_grade(35) == "F"
    assert calculate_grade(0) == "F"


def test_penalty_capping():
    # 5 critical issues of the same rule: 5 * 15 = 75, but capped at 30
    issues = [
        Issue(
            id=f"rule1-{i}-0",
            rule_id="rule1",
            title="Crit",
            message="Crit",
            severity="critical",
            category="security",
            line=i,
            end_line=i,
            column=0,
            why_it_matters="",
            suggestion="",
            fixable=False,
            reference=""
        )
        for i in range(1, 6)
    ]
    score, grade, subscores = compute_scores_and_grade(issues, [], 100)
    # Penalty is capped at 30, so score = 100 - 30 = 70
    assert score == 70
    assert grade == "C"
