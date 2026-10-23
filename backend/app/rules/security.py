from __future__ import annotations

import ast
import re
from typing import List
from app.models import Issue
from app.rules.base import BaseRule, registry


@registry.register
class HardcodedSecretRule(BaseRule):
    rule_id = "hardcoded-secret"
    title = "Hardcoded Secret or API Key"
    severity = "critical"
    category = "security"
    why_it_matters = (
        "Hardcoded credentials (passwords, tokens, API keys) can easily be leaked in version control "
        "or binary distributions, giving attackers unauthorized access to databases, cloud resources, and user accounts."
    )
    suggestion = "Retrieve sensitive secrets from environment variables (e.g. `os.environ.get('SECRET_KEY')`) or a secrets manager."
    reference = "CWE-798 / OWASP A07:2021"
    fixable = True

    SECRET_NAMES = {"password", "passwd", "secret", "api_key", "token", "auth", "private_key", "jwt_secret", "access_key"}
    AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
    HEX_TOKEN_PATTERN = re.compile(r"^[0-9a-fA-F]{32,}$")

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check variable targets
                for target in node.targets:
                    var_name = ""
                    if isinstance(target, ast.Name):
                        var_name = target.id
                    elif isinstance(target, ast.Attribute):
                        var_name = target.attr
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.slice, ast.Constant) and isinstance(target.slice.value, str):
                            var_name = target.slice.value

                    norm_name = var_name.lower()
                    matches_name = any(sec in norm_name for sec in self.SECRET_NAMES)

                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value
                        val_strip = val.strip()
                        # If matches variable name and value is non-trivial string
                        if matches_name:
                            # Skip common placeholders
                            if val_strip.lower() not in {"", "none", "todo", "xxx", "test", "dummy", "placeholder", "changeme"} and len(val_strip) >= 4:
                                issues.append(self.create_issue(
                                    message=f"Hardcoded sensitive value assigned to '{var_name}'.",
                                    line=node.lineno,
                                    column=node.col_offset,
                                    end_line=getattr(node, "end_lineno", node.lineno)
                                ))
                                break
                        else:
                            # Check regex matches in any string constant
                            if self.AWS_KEY_PATTERN.search(val) or self.HEX_TOKEN_PATTERN.match(val_strip):
                                issues.append(self.create_issue(
                                    message=f"String literal appears to be a secret or AWS access key in '{var_name}'.",
                                    line=node.lineno,
                                    column=node.col_offset,
                                    end_line=getattr(node, "end_lineno", node.lineno)
                                ))
                                break
        return issues


@registry.register
class SqlInjectionRule(BaseRule):
    rule_id = "sql-injection"
    title = "Potential SQL Injection"
    severity = "critical"
    category = "security"
    why_it_matters = (
        "Constructing SQL queries using dynamic string formatting allows untrusted input to alter the query logic, "
        "potentially exposing, altering, or deleting the entire database."
    )
    suggestion = "Use parameterized queries with placeholders (e.g. `cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))`)."
    reference = "CWE-89 / OWASP A03:2021"
    fixable = True

    SQL_METHODS = {"execute", "executemany"}

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in self.SQL_METHODS and node.args:
                    first_arg = node.args[0]
                    is_dynamic = False
                    # 1. f-string
                    if isinstance(first_arg, ast.JoinedStr):
                        is_dynamic = True
                    # 2. % formatting
                    elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                        is_dynamic = True
                    # 3. .format() call
                    elif isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Attribute) and first_arg.func.attr == "format":
                        is_dynamic = True
                    # 4. String concatenation
                    elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
                        is_dynamic = True

                    if is_dynamic:
                        issues.append(self.create_issue(
                            message=f"SQL query dynamically formatted in call to '{node.func.attr}()'.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno)
                        ))
        return issues


@registry.register
class DangerousEvalExecRule(BaseRule):
    rule_id = "dangerous-eval-exec"
    title = "Dangerous Use of eval() or exec()"
    severity = "critical"
    category = "security"
    why_it_matters = (
        "`eval()` and `exec()` execute arbitrary Python code. If any portion of the input is controlled by a user, "
        "it can lead to Remote Code Execution (RCE) and full system takeover."
    )
    suggestion = "Replace `eval()` with `ast.literal_eval()` for parsing literals, or use safe data parsers like `json.loads()`."
    reference = "CWE-95 / OWASP A03:2021"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    issues.append(self.create_issue(
                        message=f"Direct call to '{node.func.id}()' found; can lead to arbitrary code execution.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        fixable=(node.func.id == "eval")
                    ))
        return issues


@registry.register
class ShellInjectionRule(BaseRule):
    rule_id = "shell-injection"
    title = "Potential Shell Injection"
    severity = "high"
    category = "security"
    why_it_matters = (
        "Executing commands through the system shell (`shell=True` or `os.system`) allows attackers to inject "
        "arbitrary shell commands via arguments or environment variables."
    )
    suggestion = "Pass command arguments as a list to `subprocess.run([...], shell=False)` without invoking the shell."
    reference = "CWE-78 / OWASP A03:2021"
    fixable = True

    SUBPROCESS_CALLS = {"run", "Popen", "call", "check_call", "check_output"}

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check subprocess.*(..., shell=True)
                if isinstance(node.func, ast.Attribute) and node.func.attr in self.SUBPROCESS_CALLS:
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            issues.append(self.create_issue(
                                message=f"Subprocess call '{node.func.attr}()' executed with `shell=True`.",
                                line=node.lineno,
                                column=node.col_offset,
                                end_line=getattr(node, "end_lineno", node.lineno)
                            ))
                # Check os.system(...)
                elif isinstance(node.func, ast.Attribute) and node.func.attr in {"system", "popen"}:
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                        issues.append(self.create_issue(
                            message=f"Command executed using unsafe `os.{node.func.attr}()`.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            fixable=False
                        ))
        return issues


@registry.register
class UnsafeDeserializationRule(BaseRule):
    rule_id = "unsafe-deserialization"
    title = "Unsafe Object Deserialization"
    severity = "high"
    category = "security"
    why_it_matters = (
        "Deserializing untrusted data with `pickle` or unconstrained `yaml.load` can instantiate arbitrary objects "
        "and execute code upon loading, causing complete compromise."
    )
    suggestion = "Use `yaml.safe_load()` instead of `yaml.load()`. Avoid `pickle` for untrusted data; use `json` or protobuf."
    reference = "CWE-502 / OWASP A08:2021"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                mod = getattr(node.func.value, "id", None)
                method = node.func.attr
                # pickle.load / pickle.loads
                if mod == "pickle" and method in {"load", "loads"}:
                    issues.append(self.create_issue(
                        message=f"Unsafe deserialization with `pickle.{method}()`.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        fixable=False
                    ))
                # marshal.loads
                elif mod == "marshal" and method in {"load", "loads"}:
                    issues.append(self.create_issue(
                        message=f"Unsafe deserialization with `marshal.{method}()`.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        fixable=False
                    ))
                # yaml.load without SafeLoader
                elif mod == "yaml" and method == "load":
                    has_safe_loader = False
                    for kw in node.keywords:
                        if kw.arg == "Loader":
                            loader_name = getattr(kw.value, "id", "") or getattr(kw.value, "attr", "")
                            if "Safe" in loader_name:
                                has_safe_loader = True
                    if not has_safe_loader:
                        issues.append(self.create_issue(
                            message="`yaml.load()` used without SafeLoader; vulnerable to code execution.",
                            line=node.lineno,
                            column=node.col_offset,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            fixable=True
                        ))
        return issues


@registry.register
class WeakHashRule(BaseRule):
    rule_id = "weak-hash"
    title = "Weak Cryptographic Hash (MD5 / SHA-1)"
    severity = "medium"
    category = "security"
    why_it_matters = (
        "MD5 and SHA-1 have known collision vulnerabilities. Using them for integrity checks, signatures, or passwords "
        "makes systems vulnerable to spoofing and collision attacks."
    )
    suggestion = "Use a collision-resistant algorithm like SHA-256 (`hashlib.sha256()`) or bcrypt/argon2 for passwords."
    reference = "CWE-328 / OWASP A02:2021"
    fixable = True

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                mod = getattr(node.func.value, "id", None)
                if mod == "hashlib" and node.func.attr in {"md5", "sha1"}:
                    issues.append(self.create_issue(
                        message=f"Use of broken or weak cryptographic hash function `hashlib.{node.func.attr}()`.",
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=getattr(node, "end_lineno", node.lineno)
                    ))
        return issues


@registry.register
class TlsVerifyDisabledRule(BaseRule):
    rule_id = "tls-verify-disabled"
    title = "TLS Certificate Verification Disabled"
    severity = "high"
    category = "security"
    why_it_matters = (
        "Disabling SSL/TLS certificate verification exposes network traffic to Man-in-the-Middle (MitM) attacks, "
        "allowing eavesdroppers to intercept or tamper with encrypted communication."
    )
    suggestion = "Keep certificate verification enabled (`verify=True`, or omit the parameter)."
    reference = "CWE-295 / OWASP A07:2021"
    fixable = True

    HTTP_CALLS = {"get", "post", "put", "delete", "patch", "head", "request"}

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in self.HTTP_CALLS:
                    for kw in node.keywords:
                        if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                            issues.append(self.create_issue(
                                message=f"TLS verification explicitly disabled in `{node.func.attr}(..., verify=False)`.",
                                line=node.lineno,
                                column=node.col_offset,
                                end_line=getattr(node, "end_lineno", node.lineno)
                            ))
        return issues


@registry.register
class DebugModeEnabledRule(BaseRule):
    rule_id = "debug-mode-enabled"
    title = "Debug Mode Enabled in Configuration"
    severity = "medium"
    category = "security"
    why_it_matters = (
        "Running in debug mode displays interactive debuggers, full stack traces, and internal environment variables "
        "to end users, which can be leveraged for privilege escalation and RCE."
    )
    suggestion = "Ensure debug mode is disabled in production, controlled by an environment variable like `os.environ.get('DEBUG', 'False').lower() == 'true'`."
    reference = "CWE-489 / OWASP A05:2021"
    fixable = False

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            # Check app.run(..., debug=True)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run":
                    for kw in node.keywords:
                        if kw.arg == "debug" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            issues.append(self.create_issue(
                                message="Server started with `debug=True`.",
                                line=node.lineno,
                                column=node.col_offset,
                                end_line=getattr(node, "end_lineno", node.lineno)
                            ))
            # Check DEBUG = True assignment
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "DEBUG":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            issues.append(self.create_issue(
                                message="Setting `DEBUG = True` directly in source code.",
                                line=node.lineno,
                                column=node.col_offset,
                                end_line=getattr(node, "end_lineno", node.lineno)
                            ))
        return issues


@registry.register
class InsecureRandomRule(BaseRule):
    rule_id = "insecure-random"
    title = "Insecure Pseudo-Random Generator for Sensitive Data"
    severity = "low"
    category = "security"
    why_it_matters = (
        "The standard `random` module uses Mersenne Twister, which is not cryptographically secure. "
        "Internal state can be determined from observed outputs, allowing attackers to predict tokens or passwords."
    )
    suggestion = "Use Python's `secrets` module (`secrets.token_hex()`, `secrets.choice()`) for security-sensitive values."
    reference = "CWE-338 / OWASP A02:2021"
    fixable = False

    SENSITIVE_NAMES = {"token", "password", "key", "secret", "salt", "nonce", "pin"}

    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    var_name = ""
                    if isinstance(target, ast.Name):
                        var_name = target.id
                    elif isinstance(target, ast.Attribute):
                        var_name = target.attr
                    elif isinstance(target, ast.Subscript):
                        if isinstance(target.slice, ast.Constant) and isinstance(target.slice.value, str):
                            var_name = target.slice.value

                    norm_name = var_name.lower()
                    if any(term in norm_name for term in self.SENSITIVE_NAMES):
                        # Check if value calls random.*
                        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                            if getattr(node.value.func.value, "id", None) == "random":
                                issues.append(self.create_issue(
                                    message=f"Insecure `random.{node.value.func.attr}()` used to generate sensitive value '{var_name}'.",
                                    line=node.lineno,
                                    column=node.col_offset,
                                    end_line=getattr(node, "end_lineno", node.lineno)
                                ))
        return issues
