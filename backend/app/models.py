from __future__ import annotations

from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field

SeverityLevel = Literal["critical", "high", "medium", "low"]
CategoryType = Literal["security", "bug", "maintainability", "style"]
GradeType = Literal["A", "B", "C", "D", "F"]


class Issue(BaseModel):
    id: str
    rule_id: str
    title: str
    message: str
    severity: SeverityLevel
    category: CategoryType
    line: int
    end_line: int
    column: int
    why_it_matters: str
    suggestion: str
    fixable: bool = False
    reference: str = ""


class FunctionMetric(BaseModel):
    name: str
    line: int
    end_line: int
    length: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    max_nesting: int
    params: int
    rank: GradeType


class AnalysisSummary(BaseModel):
    total_issues: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    lines_of_code: int
    analysis_ms: float


class Subscores(BaseModel):
    security: int
    reliability: int
    maintainability: int


class CodeMetrics(BaseModel):
    maintainability_index: float
    avg_complexity: float
    comment_ratio: float
    docstring_coverage: float


class AnalysisResult(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: GradeType
    summary: AnalysisSummary
    subscores: Subscores
    issues: List[Issue]
    functions: List[FunctionMetric]
    metrics: CodeMetrics


class AnalyzeRequest(BaseModel):
    code: str
    filename: Optional[str] = "main.py"


class FixRequest(BaseModel):
    code: str
    issue_id: Optional[str] = None
    fix_all: Optional[bool] = False


class SkippedFix(BaseModel):
    issue_id: str
    rule_id: str
    reason: str


class FixResponse(BaseModel):
    fixed_code: str
    applied: List[str]
    skipped: List[SkippedFix]


class SampleItem(BaseModel):
    id: str
    name: str
    description: str
    code: str


class ExplainRequest(BaseModel):
    code: str
    issue_id: str


class ExplainResponse(BaseModel):
    explanation: str
    source: Literal["ollama", "builtin"]
