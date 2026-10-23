from __future__ import annotations

from typing import List, Dict, Tuple
from app.models import Issue, FunctionMetric, Subscores, GradeType

SEVERITY_PENALTIES: Dict[str, float] = {
    "critical": 15.0,
    "high": 8.0,
    "medium": 4.0,
    "low": 1.5,
}

RULE_MAX_PENALTY: float = 30.0


def calculate_grade(score: int) -> GradeType:
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def compute_penalty_for_issues(issues: List[Issue], total_lines: int) -> float:
    # Group penalties by rule_id
    penalties_by_rule: Dict[str, float] = {}
    for issue in issues:
        base_penalty = SEVERITY_PENALTIES.get(issue.severity, 2.0)
        penalties_by_rule[issue.rule_id] = penalties_by_rule.get(issue.rule_id, 0.0) + base_penalty

    # Cap each rule's total penalty at 30
    capped_penalty = sum(min(p, RULE_MAX_PENALTY) for p in penalties_by_rule.values())

    # Size normalization: for files over 300 lines, scale penalty by 300/lines (min factor 0.5)
    if total_lines > 300:
        scaling_factor = max(0.5, 300.0 / total_lines)
        capped_penalty *= scaling_factor

    return capped_penalty


def compute_scores_and_grade(
    issues: List[Issue],
    functions: List[FunctionMetric],
    total_lines: int
) -> Tuple[int, GradeType, Subscores]:
    total_issue_penalty = compute_penalty_for_issues(issues, total_lines)

    # Complexity penalty: +min(10, sum over functions of max(0, cc - 10))
    complexity_penalty = min(10.0, sum(max(0, fn.cyclomatic_complexity - 10) for fn in functions))

    total_penalty = total_issue_penalty + complexity_penalty
    raw_score = 100.0 - total_penalty
    final_score = int(round(max(0.0, min(100.0, raw_score))))
    grade = calculate_grade(final_score)

    # Subscores:
    # Security: category == "security"
    sec_issues = [i for i in issues if i.category == "security"]
    sec_penalty = compute_penalty_for_issues(sec_issues, total_lines)
    sec_score = int(round(max(0.0, min(100.0, 100.0 - sec_penalty))))

    # Reliability: category == "bug"
    rel_issues = [i for i in issues if i.category == "bug"]
    rel_penalty = compute_penalty_for_issues(rel_issues, total_lines)
    rel_score = int(round(max(0.0, min(100.0, 100.0 - rel_penalty))))

    # Maintainability: category in ("maintainability", "style") + complexity penalty
    maint_issues = [i for i in issues if i.category in {"maintainability", "style"}]
    maint_penalty = compute_penalty_for_issues(maint_issues, total_lines) + complexity_penalty
    maint_score = int(round(max(0.0, min(100.0, 100.0 - maint_penalty))))

    subscores = Subscores(
        security=sec_score,
        reliability=rel_score,
        maintainability=maint_score,
    )

    return final_score, grade, subscores
