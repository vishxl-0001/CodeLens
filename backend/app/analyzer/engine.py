from __future__ import annotations

import ast
import time
import io
import tokenize
import re
from typing import List, Dict, Set, Tuple

try:
    import radon.complexity as radon_cc
    import radon.metrics as radon_mi
except ImportError:
    radon_cc = None
    radon_mi = None

from app.models import (
    AnalysisResult,
    AnalysisSummary,
    CodeMetrics,
    FunctionMetric,
    GradeType,
    Issue,
    Subscores,
)
from app.rules import registry
from app.scoring import compute_scores_and_grade


SEVERITY_ORDER: Dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def compute_cognitive_complexity(func_node: ast.AST) -> int:
    """Computes cognitive complexity for a function AST node."""
    complexity = 0

    def visit_node(node: ast.AST, nesting: int) -> None:
        nonlocal complexity
        is_structure = isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler))
        if is_structure:
            complexity += 1 + nesting
            new_nesting = nesting + 1
        else:
            new_nesting = nesting

        if isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1

        for child in ast.iter_child_nodes(node):
            visit_node(child, new_nesting)

    for child in ast.iter_child_nodes(func_node):
        visit_node(child, 0)

    return complexity


def compute_max_nesting(func_node: ast.AST) -> int:
    """Calculates max nesting depth inside a function."""
    max_depth = 0
    BLOCK_TYPES = (ast.If, ast.While, ast.For, ast.Try, ast.With)

    def visit(node: ast.AST, depth: int) -> None:
        nonlocal max_depth
        current = depth + (1 if isinstance(node, BLOCK_TYPES) else 0)
        if current > max_depth:
            max_depth = current
        for child in ast.iter_child_nodes(node):
            visit(child, current)

    for child in ast.iter_child_nodes(func_node):
        visit(child, 0)
    return max_depth


def get_function_rank(cc: int) -> GradeType:
    if cc <= 5:
        return "A"
    elif cc <= 10:
        return "B"
    elif cc <= 15:
        return "C"
    elif cc <= 20:
        return "D"
    return "F"


def analyze_code(source_code: str, filename: str = "main.py") -> AnalysisResult:
    start_time = time.perf_counter()
    source_lines = source_code.splitlines()
    total_lines = len(source_lines)

    # 1. Syntax check
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as e:
        analysis_ms = round((time.perf_counter() - start_time) * 1000, 2)
        err_line = e.lineno or 1
        err_col = e.offset or 0
        syntax_issue = Issue(
            id=f"syntax-error-{err_line}-{err_col}",
            rule_id="syntax-error",
            title="Syntax Error",
            message=f"SyntaxError: {e.msg} on line {err_line}, column {err_col}.",
            severity="critical",
            category="bug",
            line=err_line,
            end_line=err_line,
            column=err_col,
            why_it_matters="Code containing syntax errors cannot be compiled or executed by the Python runtime.",
            suggestion="Fix the syntax error shown above before re-analyzing.",
            fixable=False,
            reference="Python Language Specification",
        )
        return AnalysisResult(
            score=0,
            grade="F",
            summary=AnalysisSummary(
                total_issues=1,
                by_severity={"critical": 1, "high": 0, "medium": 0, "low": 0},
                by_category={"security": 0, "bug": 1, "maintainability": 0, "style": 0},
                lines_of_code=total_lines,
                analysis_ms=analysis_ms,
            ),
            subscores=Subscores(security=100, reliability=0, maintainability=0),
            issues=[syntax_issue],
            functions=[],
            metrics=CodeMetrics(
                maintainability_index=0.0,
                avg_complexity=0.0,
                comment_ratio=0.0,
                docstring_coverage=0.0,
            ),
        )

    # 2. Extract function metrics & Radon metrics
    functions: List[FunctionMetric] = []
    function_nodes: List[ast.FunctionDef | ast.AsyncFunctionDef] = []
    classes_and_funcs: List[ast.AST] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_nodes.append(node)
            classes_and_funcs.append(node)
        elif isinstance(node, ast.ClassDef):
            classes_and_funcs.append(node)

    # Map radon cc
    radon_cc_map: Dict[Tuple[str, int], int] = {}
    if radon_cc:
        try:
            blocks = radon_cc.cc_visit(source_code)
            for b in blocks:
                # b.name, b.lineno, b.complexity
                radon_cc_map[(b.name, b.lineno)] = b.complexity
        except Exception:
            pass

    for fn in function_nodes:
        end_lineno = getattr(fn, "end_lineno", fn.lineno)
        length = end_lineno - fn.lineno + 1

        # Complexity: try Radon, fallback to AST
        cc = radon_cc_map.get((fn.name, fn.lineno))
        if cc is None:
            cc = 1
            for child in ast.walk(fn):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.Assert)):
                    cc += 1
                elif isinstance(child, ast.ExceptHandler):
                    cc += 1
                elif isinstance(child, ast.BoolOp):
                    cc += len(child.values) - 1

        cognitive = compute_cognitive_complexity(fn)
        nesting = compute_max_nesting(fn)
        num_params = len(fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs)

        functions.append(FunctionMetric(
            name=fn.name,
            line=fn.lineno,
            end_line=end_lineno,
            length=length,
            cyclomatic_complexity=cc,
            cognitive_complexity=cognitive,
            max_nesting=nesting,
            params=num_params,
            rank=get_function_rank(cc),
        ))

    # Maintainability Index
    mi_score = 100.0
    if radon_mi and source_code.strip():
        try:
            mi_score = round(float(radon_mi.mi_visit(source_code, multi=True)), 1)
            mi_score = max(0.0, min(100.0, mi_score))
        except Exception:
            mi_score = 100.0

    # Comment ratio
    comment_lines = 0
    try:
        tokens = tokenize.tokenize(io.BytesIO(source_code.encode("utf-8")).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comment_lines += 1
    except Exception:
        # Fallback regex
        comment_lines = sum(1 for line in source_lines if line.strip().startswith("#"))

    comment_ratio = round(comment_lines / max(1, total_lines), 2)

    # Docstring coverage
    documented = sum(1 for item in classes_and_funcs if ast.get_docstring(item) is not None)
    docstring_coverage = round(documented / max(1, len(classes_and_funcs)), 2) if classes_and_funcs else 1.0

    avg_cc = round(sum(f.cyclomatic_complexity for f in functions) / len(functions), 1) if functions else 1.0

    # 3. Run all rules
    all_issues: List[Issue] = []
    seen_issues: Set[Tuple[str, int]] = set()

    for rule in registry.get_all_rules():
        try:
            found = rule.check(tree, source_code, source_lines)
            for iss in found:
                key = (iss.rule_id, iss.line)
                if key not in seen_issues:
                    seen_issues.add(key)
                    all_issues.append(iss)
        except Exception as e:
            # Rule exception shouldn't crash analyzer
            print(f"Rule {rule.rule_id} error: {e}")

    # Sort issues by severity then line
    all_issues.sort(key=lambda x: (SEVERITY_ORDER.get(x.severity, 4), x.line))

    # 4. Compute score & grade
    score, grade, subscores = compute_scores_and_grade(all_issues, functions, total_lines)

    # Summary
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_category = {"security": 0, "bug": 0, "maintainability": 0, "style": 0}
    for iss in all_issues:
        by_severity[iss.severity] = by_severity.get(iss.severity, 0) + 1
        by_category[iss.category] = by_category.get(iss.category, 0) + 1

    analysis_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return AnalysisResult(
        score=score,
        grade=grade,
        summary=AnalysisSummary(
            total_issues=len(all_issues),
            by_severity=by_severity,
            by_category=by_category,
            lines_of_code=total_lines,
            analysis_ms=analysis_ms,
        ),
        subscores=subscores,
        issues=all_issues,
        functions=functions,
        metrics=CodeMetrics(
            maintainability_index=mi_score,
            avg_complexity=avg_cc,
            comment_ratio=comment_ratio,
            docstring_coverage=docstring_coverage,
        ),
    )
