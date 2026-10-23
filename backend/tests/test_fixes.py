from __future__ import annotations

import ast
from app.analyzer.engine import analyze_code
from app.fixes.engine import apply_fixes, apply_single_fix


def test_fix_bare_except():
    code = "try:\n    x = 1\nexcept:\n    x = 2\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "bare-except")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "except Exception:" in fixed
    ast.parse(fixed)


def test_fix_none_comparison():
    code = "if val == None:\n    print(1)\nif other != None:\n    print(2)\n"
    res = analyze_code(code)
    issues = [i for i in res.issues if i.rule_id == "none-comparison"]
    curr = code
    for iss in reversed(issues):
        s, curr, _ = apply_single_fix(curr, iss)
        assert s
    assert "is None" in curr
    assert "is not None" in curr
    ast.parse(curr)


def test_fix_weak_hash():
    code = "import hashlib\nh = hashlib.md5(b'data').hexdigest()\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "weak-hash")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "hashlib.sha256" in fixed
    ast.parse(fixed)


def test_fix_tls_verify():
    code = "import requests\nresp = requests.get('https://example.com', verify=False)\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "tls-verify-disabled")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "verify=False" not in fixed
    ast.parse(fixed)


def test_fix_yaml_load():
    code = "import yaml\ncfg = yaml.load(raw)\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "unsafe-deserialization")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "yaml.safe_load(" in fixed
    ast.parse(fixed)


def test_fix_hardcoded_secret():
    code = "api_key = 'super_secret_token_12345'\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "hardcoded-secret")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "os.environ.get(" in fixed
    assert "import os" in fixed
    ast.parse(fixed)


def test_fix_eval():
    code = "data = eval('{\"key\": 123}')\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "dangerous-eval-exec")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "ast.literal_eval" in fixed
    assert "import ast" in fixed
    ast.parse(fixed)


def test_fix_sql_injection():
    code = "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "sql-injection")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))" in fixed
    ast.parse(fixed)


def test_fix_mutable_default():
    code = "def process(items=[]):\n    items.append(1)\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "mutable-default-arg")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "items=None" in fixed
    assert "if items is None:" in fixed
    ast.parse(fixed)


def test_fix_unused_import():
    code = "import math\nimport os\nx = os.getcwd()\n"
    res = analyze_code(code)
    issue = next(i for i in res.issues if i.rule_id == "unused-import")
    success, fixed, reason = apply_single_fix(code, issue)
    assert success
    assert "import math" not in fixed
    assert "import os" in fixed
    ast.parse(fixed)


def test_fix_all_workflow():
    code = """import math
import hashlib
import yaml

api_key = 'AKIA1234567890SECRETKEY'

def get_data(cached={}):
    try:
        h = hashlib.md5(b'data').hexdigest()
        raw = yaml.load('key: val')
    except:
        raw = None
    if raw == None:
        return None
    return raw
"""
    res = analyze_code(code)
    fix_res = apply_fixes(code, res.issues, fix_all=True)
    assert len(fix_res.applied) > 0
    # Fixed code must parse cleanly
    tree = ast.parse(fix_res.fixed_code)
    assert tree is not None
    # Verify score improved on re-analysis
    new_res = analyze_code(fix_res.fixed_code)
    assert new_res.score > res.score
