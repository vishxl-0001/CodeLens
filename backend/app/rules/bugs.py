from __future__ import annotations

import ast
from typing import List, Set, Dict, Any
from app.models import Issue
from app.rules.base import BaseRule, registry


@registry.register
class BareExceptRule(BaseRule):
    rule_id = "bare-except"
    title = "Bare 'except:' Statement"
    severity = "medium"
    category = "bug"
    why_it_matters = (
        "A bare `except:` catches all exceptions, including `KeyboardInterrupt`, `SystemExit`, "
        "and `MemoryError`. This makes graceful shutdowns difficult and masks serious bugs like NameError or TypeError."
    )
    suggestion = "Catch specific exceptions, or at least `except Exception:` to preserve system signals."
    reference = "PEP 8 / CWE-396"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append(self.create_issue(
                            message="Bare `except:` used without specifying an exception class.",
                            line=handler.lineno,
                            column=handler.col_offset,
                            end_line=getattr(handler, "end_lineno", handler.lineno)
                        ))
        return issues


@registry.register
class SwallowedExceptionRule(BaseRule):
    rule_id = "swallowed-exception"
    title = "Swallowed Exception with pass"
    severity = "medium"
    category = "bug"
    why_it_matters = (
        "Silently discarding exceptions with `pass` hides critical failures, corrupts downstream state, "
        "and makes debugging nearly impossible in production."
    )
    suggestion = "Log the error using `logging.exception()` or handle it explicitly with fallback logic."
    reference = "CWE-390 / PEP 8"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    # Check if handler body is only Pass or Pass + docstring
                    body_stmts = [s for s in handler.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
                    if len(body_stmts) == 1 and isinstance(body_stmts[0], ast.Pass):
                        issues.append(self.create_issue(
                            message="Exception is caught but silently ignored with `pass`.",
                            line=handler.lineno,
                            column=handler.col_offset,
                            end_line=getattr(handler, "end_lineno", handler.lineno)
                        ))
        return issues


@registry.register
class MutableDefaultArgRule(BaseRule):
    rule_id = "mutable-default-arg"
    title = "Mutable Default Argument"
    severity = "high"
    category = "bug"
    why_it_matters = (
        "Default parameter values are evaluated once when the function is defined, not each time it is called. "
        "Mutating a default list or dict shares changes across all subsequent invocations, causing subtle bugs."
    )
    suggestion = "Use `None` as the default value and initialize the mutable object inside the function body."
    reference = "PEP 570 / Common Python Gotchas"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Match defaults with args
                all_defaults = node.args.defaults
                for default in all_defaults:
                    is_mutable = False
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        is_mutable = True
                    elif isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
                        if default.func.id in {"list", "dict", "set"}:
                            is_mutable = True

                    if is_mutable:
                        issues.append(self.create_issue(
                            message=f"Mutable default argument used in function '{node.name}'.",
                            line=default.lineno,
                            column=default.col_offset,
                            end_line=getattr(default, "end_lineno", default.lineno)
                        ))
        return issues


@registry.register
class NoneComparisonRule(BaseRule):
    rule_id = "none-comparison"
    title = "Comparison to None using Equality Operator"
    severity = "low"
    category = "bug"
    why_it_matters = (
        "Comparing to `None` using `==` or `!=` can trigger custom `__eq__` implementations on objects, "
        "producing unexpected boolean values. In Python, `None` is a singleton and should always be checked with `is`."
    )
    suggestion = "Use `x is None` or `x is not None` instead of `== None` or `!= None`."
    reference = "PEP 8"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Check left and comparators
                comparators = [node.left] + node.comparators
                for i, op in enumerate(node.ops):
                    left_op = comparators[i]
                    right_op = comparators[i+1]
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        has_none = (
                            (isinstance(left_op, ast.Constant) and left_op.value is None) or
                            (isinstance(right_op, ast.Constant) and right_op.value is None)
                        )
                        if has_none:
                            op_str = "==" if isinstance(op, ast.Eq) else "!="
                            issues.append(self.create_issue(
                                message=f"Comparison to `None` using `{op_str}` instead of identity operator.",
                                line=node.lineno,
                                column=node.col_offset,
                                end_line=getattr(node, "end_lineno", node.lineno)
                            ))
        return issues


@registry.register
class UnreachableCodeRule(BaseRule):
    rule_id = "unreachable-code"
    title = "Unreachable Code"
    severity = "medium"
    category = "bug"
    why_it_matters = (
        "Statements following `return`, `raise`, `break`, or `continue` in the same sequential block can never execute. "
        "This usually indicates leftover debugging code or flawed control flow."
    )
    suggestion = "Remove unreachable statements or reorganize conditional branches so the logic executes."
    reference = "CWE-561"
    fixable = False

    TERMINAL_TYPES = (ast.Return, ast.Raise, ast.Break, ast.Continue)

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            for body_attr in ["body", "orelse", "finalbody"]:
                stmts = getattr(node, body_attr, None)
                if isinstance(stmts, list) and len(stmts) > 1:
                    found_terminal = False
                    for stmt in stmts:
                        if found_terminal:
                            issues.append(self.create_issue(
                                message="Code is unreachable because it follows a terminating statement.",
                                line=stmt.lineno,
                                column=stmt.col_offset,
                                end_line=getattr(stmt, "end_lineno", stmt.lineno)
                            ))
                            break
                        if isinstance(stmt, self.TERMINAL_TYPES):
                            found_terminal = True
        return issues


@registry.register
class ShadowedBuiltinRule(BaseRule):
    rule_id = "shadowed-builtin"
    title = "Shadowed Built-in Identifier"
    severity = "low"
    category = "bug"
    why_it_matters = (
        "Overwriting Python built-in names (e.g. `list`, `dict`, `str`, `id`, `type`, `input`) shadows the built-in function "
        "or type in local scope, preventing standard calls and confusing readers."
    )
    suggestion = "Rename the variable to a descriptive name (e.g. `items` instead of `list`, `user_id` instead of `id`)."
    reference = "PEP 8 / Code Smells"
    fixable = False

    BUILTINS = {
        "list", "dict", "str", "int", "float", "id", "type", "input",
        "sum", "max", "min", "format", "open", "range", "len", "set",
        "tuple", "bool", "bytes", "dir", "hash", "map", "filter", "all", "any"
    }

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            # Check function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in self.BUILTINS:
                    issues.append(self.create_issue(
                        message=f"Function name '{node.name}' shadows Python built-in.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
                # Check parameters
                for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                    if arg.arg in self.BUILTINS:
                        issues.append(self.create_issue(
                            message=f"Parameter '{arg.arg}' shadows Python built-in in '{node.name}'.",
                            line=arg.lineno,
                            column=arg.col_offset,
                            end_line=getattr(arg, "end_lineno", arg.lineno)
                        ))
            # Check variable assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in self.BUILTINS:
                        issues.append(self.create_issue(
                            message=f"Variable '{target.id}' shadows Python built-in.",
                            line=target.lineno,
                            column=target.col_offset,
                            end_line=getattr(target, "end_lineno", target.lineno)
                        ))
        return issues


@registry.register
class UnusedVariableRule(BaseRule):
    rule_id = "unused-variable"
    title = "Unused Local Variable"
    severity = "low"
    category = "bug"
    why_it_matters = (
        "Unused variables indicate incomplete refactoring, discarded results, or potential typos where a variable was "
        "assigned but another was mistakenly read."
    )
    suggestion = "Prefix the variable with an underscore `_` if intentionally unused, or remove it."
    reference = "PEP 8"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assigned_names: Dict[str, ast.AST] = {}
                used_names: Set[str] = set()

                for node in ast.walk(fn):
                    if isinstance(node, ast.Name):
                        if isinstance(node.ctx, ast.Store):
                            if not node.id.startswith("_"):
                                if node.id not in assigned_names:
                                    assigned_names[node.id] = node
                        elif isinstance(node.ctx, ast.Load):
                            used_names.add(node.id)

                for name, node in assigned_names.items():
                    if name not in used_names:
                        issues.append(self.create_issue(
                            message=f"Local variable '{name}' is assigned but never used.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno)
                        ))
        return issues


@registry.register
class UnusedImportRule(BaseRule):
    rule_id = "unused-import"
    title = "Unused Import"
    severity = "low"
    category = "bug"
    why_it_matters = (
        "Unused imports increase startup time, bloat namespace pollution, and confuse developers about external dependencies."
    )
    suggestion = "Remove the unused import from the file header."
    reference = "PEP 8 / F401"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        imported_symbols: Dict[str, tuple[ast.AST, str]] = {}
        used_symbols: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_to_track = alias.asname or alias.name.split(".")[0]
                    imported_symbols[name_to_track] = (node, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        name_to_track = alias.asname or alias.name
                        imported_symbols[name_to_track] = (node, alias.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_symbols.add(node.id)

        # Check __all__
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    used_symbols.add(elt.value)

        for sym, (import_node, orig_name) in imported_symbols.items():
            if sym not in used_symbols:
                issues.append(self.create_issue(
                    message=f"Imported module or symbol '{sym}' is never used.",
                    line=import_node.lineno,
                    column=import_node.col_offset,
                    end_line=getattr(import_node, "end_lineno", import_node.lineno)
                ))
        return issues


@registry.register
class MissingResourceCloseRule(BaseRule):
    rule_id = "missing-resource-close"
    title = "File Opened Outside 'with' Statement"
    severity = "medium"
    category = "bug"
    why_it_matters = (
        "Files opened without a `with` context manager may stay open indefinitely if an exception occurs before `.close()`. "
        "This leads to file descriptor leaks, locked files, and incomplete disk flushes."
    )
    suggestion = "Use a `with open(...) as f:` context manager to ensure automatic closure upon block exit."
    reference = "PEP 343 / CWE-775"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []

        # Find all open() calls that are within a withitem
        with_open_nodes: Set[ast.AST] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if getattr(item.context_expr.func, "id", None) == "open":
                            with_open_nodes.add(item.context_expr)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if getattr(node.func, "id", None) == "open" and node not in with_open_nodes:
                    issues.append(self.create_issue(
                        message="File opened without `with` statement context manager.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
        return issues
