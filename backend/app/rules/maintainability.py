from __future__ import annotations

import ast
import re
import tokenize
import io
from typing import List, Dict, Set
from app.models import Issue
from app.rules.base import BaseRule, registry


@registry.register
class FunctionTooLongRule(BaseRule):
    rule_id = "function-too-long"
    title = "Function Exceeds 50 Lines"
    severity = "medium"
    category = "maintainability"
    why_it_matters = (
        "Long functions tend to violate the Single Responsibility Principle, contain multiple hidden concerns, "
        "and are difficult to unit test and maintain."
    )
    suggestion = "Extract logical sub-steps into smaller helper functions with clear responsibilities."
    reference = "Clean Code / Refactoring"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                length = end_lineno - node.lineno + 1
                if length > 50:
                    issues.append(self.create_issue(
                        message=f"Function '{node.name}' has {length} lines (recommended maximum is 50).",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=end_lineno
                    ))
        return issues


@registry.register
class DeepNestingRule(BaseRule):
    rule_id = "deep-nesting"
    title = "Excessive Nesting Depth (>4 levels)"
    severity = "medium"
    category = "maintainability"
    why_it_matters = (
        "Deeply nested control structures exponentially increase cognitive load, make edge cases harder to trace, "
        "and usually signal arrow anti-patterns."
    )
    suggestion = "Use guard clauses, early returns, or break inner blocks into separate functions."
    reference = "Code Smells / Arrow Anti-Pattern"
    fixable = False

    BLOCK_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []

        def traverse(node: ast.AST, depth: int) -> None:
            new_depth = depth + (1 if isinstance(node, self.BLOCK_NODES) else 0)
            if isinstance(node, self.BLOCK_NODES) and new_depth == 5:
                issues.append(self.create_issue(
                    message="Nesting depth exceeded maximum recommended depth of 4 levels.",
                    line=node.lineno,
                    column=node.col_offset,
                    end_line=getattr(node, "end_lineno", node.lineno)
                ))
            for child in ast.iter_child_nodes(node):
                # Reset nesting for new functions
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    traverse(child, 0)
                else:
                    traverse(child, new_depth)

        traverse(tree, 0)
        return issues


@registry.register
class TooManyParametersRule(BaseRule):
    rule_id = "too-many-parameters"
    title = "Too Many Parameters (>5)"
    severity = "low"
    category = "maintainability"
    why_it_matters = (
        "Functions with more than 5 parameters are prone to caller argument misordering, high coupling, "
        "and indicate that the function may be doing too much."
    )
    suggestion = "Group related parameters into a dataclass, Pydantic model, or configuration dictionary."
    reference = "Clean Code / Refactoring"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Exclude 'self' or 'cls'
                args_list = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                param_names = [a.arg for a in args_list if a.arg not in {"self", "cls"}]
                if len(param_names) > 5:
                    issues.append(self.create_issue(
                        message=f"Function '{node.name}' has {len(param_names)} parameters (recommended maximum is 5).",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
        return issues


@registry.register
class HighComplexityRule(BaseRule):
    rule_id = "high-complexity"
    title = "High Cyclomatic Complexity"
    severity = "medium"
    category = "maintainability"
    why_it_matters = (
        "Cyclomatic complexity measures the number of linearly independent paths through the code. "
        "A complexity above 10 correlates strongly with high bug counts and low test coverage."
    )
    suggestion = "Decompose the function into smaller helper methods or simplify boolean conditions."
    reference = "McCabe Cyclomatic Complexity"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.Assert)):
                        cc += 1
                    elif isinstance(child, ast.ExceptHandler):
                        cc += 1
                    elif isinstance(child, ast.BoolOp):
                        cc += len(child.values) - 1

                if cc > 10:
                    sev = "high" if cc > 15 else "medium"
                    issue = self.create_issue(
                        message=f"Function '{node.name}' has cyclomatic complexity of {cc} (threshold is 10).",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    )
                    issue.severity = sev
                    issues.append(issue)
        return issues


@registry.register
class MissingDocstringRule(BaseRule):
    rule_id = "missing-docstring"
    title = "Missing Docstring on Public Interface"
    severity = "low"
    category = "style"
    why_it_matters = (
        "Public functions and classes without docstrings make the codebase harder for other engineers to understand, "
        "reducing discoverability and self-documenting code clarity."
    )
    suggestion = "Add a docstring explaining parameters, return values, and behavior."
    reference = "PEP 257"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    doc = ast.get_docstring(node)
                    if not doc:
                        kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
                        issues.append(self.create_issue(
                            message=f"{kind} '{node.name}' lacks a descriptive docstring.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno)
                        ))
        return issues


@registry.register
class MagicNumberRule(BaseRule):
    rule_id = "magic-number"
    title = "Magic Number in Expression"
    severity = "low"
    category = "style"
    why_it_matters = (
        "Unexplained numeric literals make logic cryptic and create maintenance risks if the value must be updated in multiple places."
    )
    suggestion = "Replace literal numbers with named constants in UPPER_CASE describing their purpose."
    reference = "Clean Code / Refactoring"
    fixable = False

    ALLOWED_NUMS = {0, 1, -1, 2, 0.0, 1.0, 2.0}

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []

        # Find line numbers of top-level module constants so we don't flag them
        module_constant_lines: Set[int] = set()
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        module_constant_lines.add(node.lineno)

        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Check for magic numbers in comparison operations
                for sub in [node.left] + node.comparators:
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, (int, float)):
                        if sub.value not in self.ALLOWED_NUMS and sub.lineno not in module_constant_lines:
                            issues.append(self.create_issue(
                                message=f"Magic number '{sub.value}' used directly in comparison.",
                                line=sub.lineno,
                                column=sub.col_offset,
                                end_line=getattr(sub, "end_lineno", sub.lineno)
                            ))
                            break
        return issues


@registry.register
class DuplicateCodeRule(BaseRule):
    rule_id = "duplicate-code"
    title = "Duplicate Code Block (5+ Lines)"
    severity = "medium"
    category = "maintainability"
    why_it_matters = (
        "Duplicated code blocks violate DRY (Don't Repeat Yourself). Bug fixes made in one copy "
        "are often missed in the other, causing regression bugs."
    )
    suggestion = "Extract duplicated logic into a shared reusable utility function or method."
    reference = "DRY Principle / Refactoring"
    fixable = False

    WINDOW_SIZE = 5

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        if len(source_lines) < self.WINDOW_SIZE * 2:
            return issues

        # Normalize lines
        normalized = []
        for line in source_lines:
            stripped = line.strip()
            # Strip comments
            stripped = re.sub(r"#.*$", "", stripped).strip()
            normalized.append(stripped)

        # Build sliding windows
        window_map: Dict[tuple, int] = {}
        reported_lines: Set[int] = set()

        for i in range(len(normalized) - self.WINDOW_SIZE + 1):
            curr_line = i + 1
            if curr_line in reported_lines:
                continue

            window = tuple(normalized[i:i + self.WINDOW_SIZE])
            # Skip trivial or single-repeated-line windows
            if len(set(window)) <= 1:
                continue
            non_empty_count = sum(1 for line in window if line and line not in {"pass", "return", "continue", "break"})
            if non_empty_count < self.WINDOW_SIZE - 1:
                continue

            if window in window_map:
                prev_line = window_map[window]
                # Ensure they don't overlap
                if curr_line - prev_line >= self.WINDOW_SIZE:
                    issues.append(self.create_issue(
                        message=f"Duplicated {self.WINDOW_SIZE}-line code block detected (also at line {prev_line}).",
                        line=curr_line,
                        column=0,
                        end_line=curr_line + self.WINDOW_SIZE - 1
                    ))
                    for offset in range(self.WINDOW_SIZE):
                        reported_lines.add(curr_line + offset)
            else:
                window_map[window] = curr_line

        return issues


@registry.register
class TodoCommentRule(BaseRule):
    rule_id = "todo-comment"
    title = "TODO or FIXME Comment Found"
    severity = "low"
    category = "style"
    why_it_matters = (
        "TODO, FIXME, and HACK markers in production code indicate incomplete implementations, "
        "technical debt, or known bugs that have not been tracked in the issue tracker."
    )
    suggestion = "Address the technical debt or convert it into a tracked issue in your project management system."
    reference = "Technical Debt / Code Smells"
    fixable = False

    TODO_PATTERN = re.compile(r"#\s*(TODO|FIXME|HACK|XXX)\b.*", re.IGNORECASE)

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for line_num, line in enumerate(source_lines, 1):
            match = self.TODO_PATTERN.search(line)
            if match:
                issues.append(self.create_issue(
                    message=f"Unresolved marker found: '{match.group(0).strip()}'.",
                    line=line_num,
                    column=match.start(),
                    end_line=line_num
                ))
        return issues


@registry.register
class PrintStatementRule(BaseRule):
    rule_id = "print-statement"
    title = "print() Statement in Production Code"
    severity = "low"
    category = "style"
    why_it_matters = (
        "`print()` outputs directly to stdout without log levels, timestamps, or configuration control, "
        "polluting standard output and preventing centralized log management."
    )
    suggestion = "Replace `print()` with standard logging using `logging.info()` or `logging.debug()`."
    reference = "12-Factor App / Logging Best Practices"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    issues.append(self.create_issue(
                        message="Use of `print()` statement instead of standard `logging`.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
        return issues


@registry.register
class NamingConventionRule(BaseRule):
    rule_id = "naming-convention"
    title = "Non-standard Naming Convention"
    severity = "low"
    category = "style"
    why_it_matters = (
        "Python PEP 8 specifies snake_case for functions and variables, and PascalCase for classes. "
        "Inconsistent naming damages readability and makes APIs less predictable."
    )
    suggestion = "Rename classes to PascalCase (e.g. `UserAccount`) and functions/variables to snake_case (e.g. `calculate_total`)."
    reference = "PEP 8"
    fixable = False

    SNAKE_CASE_REGEX = re.compile(r"^[a-z_][a-z0-9_]*$")
    PASCAL_CASE_REGEX = re.compile(r"^[A-Z][a-zA-Z0-9]*$")

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            # Check classes
            if isinstance(node, ast.ClassDef):
                if not self.PASCAL_CASE_REGEX.match(node.name):
                    issues.append(self.create_issue(
                        message=f"Class '{node.name}' should follow PascalCase naming convention.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
            # Check functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not (node.name.startswith("__") and node.name.endswith("__")):
                    if not self.SNAKE_CASE_REGEX.match(node.name):
                        issues.append(self.create_issue(
                            message=f"Function '{node.name}' should follow snake_case naming convention.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno)
                        ))
        return issues
