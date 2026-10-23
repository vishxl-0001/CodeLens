from __future__ import annotations

import ast
import re
from typing import List, Tuple, Optional
from app.models import Issue, SkippedFix, FixResponse


def ensure_import(code: str, module_name: str) -> str:
    """Ensure an import statement exists at top of file, preserving comments if any."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module_name:
                    return code
        elif isinstance(node, ast.ImportFrom):
            if node.module == module_name:
                return code

    lines = code.splitlines(keepends=True)
    # Find position after future imports or module docstring
    insert_idx = 0
    in_docstring = False
    docstring_quotes = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_quotes = stripped[:3]
                if stripped.count(docstring_quotes) >= 2 and len(stripped) > 3:
                    insert_idx = i + 1
                    break
                in_docstring = True
                continue
            elif stripped.startswith("#") or not stripped:
                insert_idx = i + 1
                continue
            else:
                insert_idx = i
                break
        else:
            if docstring_quotes and docstring_quotes in stripped:
                in_docstring = False
                insert_idx = i + 1
                break

    lines.insert(insert_idx, f"import {module_name}\n")
    return "".join(lines)


def fix_bare_except(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    # Replace except: with except Exception:
    fixed_line = re.sub(r"\bexcept\s*:", "except Exception:", orig_line)
    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""
    return False, code, "Could not find 'except:' on line"


def fix_none_comparison(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    fixed_line = re.sub(r"==\s*None\b", "is None", orig_line)
    fixed_line = re.sub(r"!=\s*None\b", "is not None", fixed_line)
    fixed_line = re.sub(r"\bNone\s*==", "None is", fixed_line)
    fixed_line = re.sub(r"\bNone\s*!=", "None is not", fixed_line)

    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""
    return False, code, "Could not match '== None' or '!= None'"


def fix_weak_hash(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    fixed_line = re.sub(r"\bhashlib\.(md5|sha1)\b", "hashlib.sha256", orig_line)
    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""
    return False, code, "Could not match hashlib.md5 or hashlib.sha1"


def fix_yaml_load(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    fixed_line = re.sub(r"\byaml\.load\(", "yaml.safe_load(", orig_line)
    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""
    return False, code, "Could not match yaml.load"


def fix_tls_verify(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    fixed_line = re.sub(r",\s*verify\s*=\s*False\b", "", orig_line)
    if fixed_line == orig_line:
        fixed_line = re.sub(r"\bverify\s*=\s*False\s*,\s*", "", orig_line)
    if fixed_line == orig_line:
        fixed_line = re.sub(r"\bverify\s*=\s*False\b", "", orig_line)

    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""
    return False, code, "Could not match verify=False"


def fix_shell_injection(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    if "os.system" in orig_line or "os.popen" in orig_line:
        return False, code, "os.system requires manual refactoring to subprocess.run"

    # Match shell=True
    if "shell=True" not in orig_line:
        return False, code, "Could not locate shell=True"

    # Check if the command passed is a literal string, e.g. subprocess.run('ls -la', shell=True)
    match_str = re.search(r"subprocess\.\w+\(\s*(['\"][^'\"]+['\"])", orig_line)
    if match_str:
        raw_cmd = match_str.group(1)[1:-1]
        args = raw_cmd.split()
        args_repr = repr(args)
        fixed_line = orig_line.replace(match_str.group(1), args_repr)
        fixed_line = re.sub(r",\s*shell\s*=\s*True\b", "", fixed_line)
        fixed_line = re.sub(r"\bshell\s*=\s*True\s*,\s*", "", fixed_line)
        lines[idx] = fixed_line
        return True, "".join(lines), ""

    # If already a list or variable, just remove shell=True
    fixed_line = re.sub(r",\s*shell\s*=\s*True\b", "", orig_line)
    fixed_line = re.sub(r"\bshell\s*=\s*True\s*,\s*", "", fixed_line)
    if fixed_line != orig_line:
        lines[idx] = fixed_line
        return True, "".join(lines), ""

    return False, code, "Complex command argument requires manual review"


def fix_hardcoded_secret(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    # Match var = "secret" or var = 'secret'
    match = re.search(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*['\"][^'\"]*['\"](.*)$", orig_line)
    if match:
        indent = match.group(1)
        var_name = match.group(2)
        tail = match.group(3)
        env_key = var_name.upper()
        fixed_line = f'{indent}{var_name} = os.environ.get("{env_key}", ""){tail}\n'
        lines[idx] = fixed_line
        new_code = "".join(lines)
        new_code = ensure_import(new_code, "os")
        return True, new_code, ""

    return False, code, "Assignment pattern not recognized for automatic replacement"


def fix_eval(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    if "exec(" in orig_line:
        return False, code, "exec() executes arbitrary statements and cannot be safely auto-fixed"

    fixed_line = re.sub(r"\beval\(", "ast.literal_eval(", orig_line)
    if fixed_line != orig_line:
        lines[idx] = fixed_line
        new_code = "".join(lines)
        new_code = ensure_import(new_code, "ast")
        return True, new_code, ""

    return False, code, "Could not locate eval() call"


def fix_sql_injection(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]

    # Pattern 1: f-string e.g. cursor.execute(f"SELECT ... WHERE col = {var}") or '{var}'
    f_match = re.search(r"(\w+\.execute\w*)\(f([\"'])(.*?)\{([a-zA-Z0-9_]+)\}(.*?)\2(\s*\))", orig_line)
    if f_match:
        prefix = f_match.group(1)
        quote = f_match.group(2)
        before = f_match.group(3)
        var_name = f_match.group(4)
        after = f_match.group(5)
        # Strip internal quotes if wrapped in '{var}'
        if before.endswith("'") and after.startswith("'"):
            before = before[:-1]
            after = after[1:]
        elif before.endswith('"') and after.startswith('"'):
            before = before[:-1]
            after = after[1:]
        replacement = f'{prefix}("{before}%s{after}", ({var_name},))'
        fixed_line = orig_line[:f_match.start()] + replacement + orig_line[f_match.end():]
        lines[idx] = fixed_line
        return True, "".join(lines), ""

    # Pattern 2: % format e.g. cursor.execute("SELECT ... %s" % var)
    mod_match = re.search(r"(\w+\.execute\w*)\((['\"].*?['\"])\s*%\s*([a-zA-Z0-9_]+)\)", orig_line)
    if mod_match:
        prefix = mod_match.group(1)
        query = mod_match.group(2)
        var_name = mod_match.group(3)
        replacement = f'{prefix}({query}, ({var_name},))'
        fixed_line = orig_line[:mod_match.start()] + replacement + orig_line[mod_match.end():]
        lines[idx] = fixed_line
        return True, "".join(lines), ""

    # Pattern 3: .format() e.g. cursor.execute("SELECT ... {}".format(var))
    fmt_match = re.search(r"(\w+\.execute\w*)\((['\"].*?)\{\}(.*?['\"])\.format\(([a-zA-Z0-9_]+)\)\)", orig_line)
    if fmt_match:
        prefix = fmt_match.group(1)
        before = fmt_match.group(2)
        after = fmt_match.group(3)
        var_name = fmt_match.group(4)
        replacement = f'{prefix}({before}%s{after}, ({var_name},))'
        fixed_line = orig_line[:fmt_match.start()] + replacement + orig_line[fmt_match.end():]
        lines[idx] = fixed_line
        return True, "".join(lines), ""

    return False, code, "Complex dynamic SQL query requires manual parameterization"


def fix_mutable_default(code: str, issue: Issue) -> Tuple[bool, str, str]:
    try:
        tree = ast.parse(code)
    except Exception:
        return False, code, "Failed to parse code"

    # Find the function def that encompasses issue.line
    target_fn: Optional[ast.FunctionDef | ast.AsyncFunctionDef] = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.lineno <= issue.line <= getattr(node, "end_lineno", node.lineno):
                target_fn = node
                break

    if not target_fn:
        return False, code, "Could not locate function containing mutable default argument"

    # Find which argument has the mutable default
    arg_name = None
    default_type = "[]"
    for i, default in enumerate(target_fn.args.defaults):
        if default.lineno == issue.line:
            idx_in_args = len(target_fn.args.args) - len(target_fn.args.defaults) + i
            if idx_in_args < len(target_fn.args.args):
                arg_name = target_fn.args.args[idx_in_args].arg
                if isinstance(default, ast.Dict):
                    default_type = "{}"
                elif isinstance(default, ast.Set):
                    default_type = "set()"
                break

    if not arg_name:
        return False, code, "Could not determine parameter name with mutable default"

    lines = code.splitlines(keepends=True)
    def_line_idx = issue.line - 1

    # Replace parameter default with None on definition line
    orig_def = lines[def_line_idx]
    # Replace arg=[] or arg={} with arg=None
    pattern = rf"\b{arg_name}\s*=\s*(\[[^\]]*\]|\{{[^\}}]*\}}|set\(\)|list\(\)|dict\(\))"
    new_def = re.sub(pattern, f"{arg_name}=None", orig_def)
    if new_def == orig_def:
        return False, code, "Could not update parameter default to None"
    lines[def_line_idx] = new_def

    # Insert initialization at top of function body
    body_idx = target_fn.body[0].lineno - 1
    # Check if first statement is docstring
    first_stmt = target_fn.body[0]
    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
        if len(target_fn.body) > 1:
            body_idx = target_fn.body[1].lineno - 1
        else:
            body_idx = getattr(first_stmt, "end_lineno", first_stmt.lineno)

    # Indentation of function body
    indent = "    "
    if body_idx < len(lines):
        line_content = lines[body_idx]
        indent = line_content[:len(line_content) - len(line_content.lstrip())]

    init_stmt = f"{indent}if {arg_name} is None:\n{indent}    {arg_name} = {default_type}\n"
    lines.insert(body_idx, init_stmt)
    return True, "".join(lines), ""


def fix_unused_import(code: str, issue: Issue) -> Tuple[bool, str, str]:
    lines = code.splitlines(keepends=True)
    idx = issue.line - 1
    if idx < 0 or idx >= len(lines):
        return False, code, "Line index out of bounds"

    orig_line = lines[idx]
    # Extract symbol from message: e.g. "Imported module or symbol 'math' is never used."
    sym_match = re.search(r"symbol '([^']+)'", issue.message)
    sym = sym_match.group(1) if sym_match else ""

    # If it's a multi-symbol import: from os import path, sys
    if "," in orig_line and sym:
        # Remove sym from comma list
        pattern1 = rf",\s*{sym}\b"
        new_line = re.sub(pattern1, "", orig_line)
        if new_line == orig_line:
            pattern2 = rf"\b{sym}\s*,\s*"
            new_line = re.sub(pattern2, "", orig_line)
        if new_line != orig_line:
            lines[idx] = new_line
            return True, "".join(lines), ""

    # Otherwise remove the whole line
    lines.pop(idx)
    return True, "".join(lines), ""


DISPATCHER = {
    "bare-except": fix_bare_except,
    "none-comparison": fix_none_comparison,
    "weak-hash": fix_weak_hash,
    "unsafe-deserialization": fix_yaml_load,
    "tls-verify-disabled": fix_tls_verify,
    "shell-injection": fix_shell_injection,
    "hardcoded-secret": fix_hardcoded_secret,
    "dangerous-eval-exec": fix_eval,
    "sql-injection": fix_sql_injection,
    "mutable-default-arg": fix_mutable_default,
    "unused-import": fix_unused_import,
}


def apply_single_fix(code: str, issue: Issue) -> Tuple[bool, str, str]:
    if issue.rule_id == "missing-resource-close":
        return False, code, "Refactoring open() to a with-statement requires restructuring block scope."

    fix_func = DISPATCHER.get(issue.rule_id)
    if not fix_func:
        return False, code, f"No auto-fix available for rule '{issue.rule_id}'."

    success, new_code, reason = fix_func(code, issue)
    if not success:
        return False, code, reason or "Could not apply fix template."

    # Validate syntax
    try:
        ast.parse(new_code)
    except SyntaxError as e:
        return False, code, f"Fix produced invalid Python syntax: {e.msg}"

    return True, new_code, ""


def apply_fixes(code: str, issues: List[Issue], target_issue_id: Optional[str] = None, fix_all: bool = False) -> FixResponse:
    applied_ids: List[str] = []
    skipped_fixes: List[SkippedFix] = []
    current_code = code

    if target_issue_id:
        target = next((i for i in issues if i.id == target_issue_id), None)
        if not target:
            return FixResponse(
                fixed_code=code,
                applied=[],
                skipped=[SkippedFix(issue_id=target_issue_id, rule_id="", reason="Issue ID not found in current analysis")]
            )
        success, new_code, reason = apply_single_fix(current_code, target)
        if success:
            return FixResponse(fixed_code=new_code, applied=[target.id], skipped=[])
        else:
            return FixResponse(
                fixed_code=code,
                applied=[],
                skipped=[SkippedFix(issue_id=target.id, rule_id=target.rule_id, reason=reason)]
            )

    if fix_all:
        from app.analyzer.engine import analyze_code
        seen_failed_rules = set()

        # Iteratively apply up to 25 fix cycles
        for _ in range(25):
            current_analysis = analyze_code(current_code)
            fixable_issues = [
                i for i in current_analysis.issues
                if i.fixable and (i.rule_id, i.line) not in seen_failed_rules
            ]
            if not fixable_issues:
                break

            applied_in_pass = False
            for target_issue in fixable_issues:
                success, next_code, reason = apply_single_fix(current_code, target_issue)
                if success:
                    current_code = next_code
                    applied_ids.append(target_issue.id)
                    applied_in_pass = True
                    # Re-analyze with new coordinates after each successful mutation
                    break
                else:
                    seen_failed_rules.add((target_issue.rule_id, target_issue.line))
                    skipped_fixes.append(SkippedFix(
                        issue_id=target_issue.id,
                        rule_id=target_issue.rule_id,
                        reason=reason
                    ))

            if not applied_in_pass:
                break

        # Record remaining non-fixable issues
        final_analysis = analyze_code(current_code)
        for issue in final_analysis.issues:
            if not issue.fixable:
                skipped_fixes.append(SkippedFix(
                    issue_id=issue.id,
                    rule_id=issue.rule_id,
                    reason=f"Rule '{issue.rule_id}' is not marked as auto-fixable"
                ))

        return FixResponse(fixed_code=current_code, applied=applied_ids, skipped=skipped_fixes)

    return FixResponse(fixed_code=code, applied=[], skipped=[])
