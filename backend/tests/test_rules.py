from __future__ import annotations

import pytest
from app.analyzer.engine import analyze_code


# ---------------------------------------------------------
# Security Rules Tests (S1 - S9)
# ---------------------------------------------------------

def test_s1_hardcoded_secret():
    pos = "api_key = 'AKIA1234567890EXAMPLE'\npassword = 'supersecretpassword123'"
    neg = "api_key = os.environ.get('API_KEY', '')\npassword = ''"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "hardcoded-secret" for i in res_pos.issues)
    assert not any(i.rule_id == "hardcoded-secret" for i in res_neg.issues)


def test_s2_sql_injection():
    pos = "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')"
    neg = "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "sql-injection" for i in res_pos.issues)
    assert not any(i.rule_id == "sql-injection" for i in res_neg.issues)


def test_s3_dangerous_eval_exec():
    pos = "result = eval(user_input)\nexec('x = 1')"
    neg = "import ast\nresult = ast.literal_eval(safe_str)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "dangerous-eval-exec" for i in res_pos.issues)
    assert not any(i.rule_id == "dangerous-eval-exec" for i in res_neg.issues)


def test_s4_shell_injection():
    pos = "subprocess.run('ls -la', shell=True)\nos.system('echo hi')"
    neg = "subprocess.run(['ls', '-la'], shell=False)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "shell-injection" for i in res_pos.issues)
    assert not any(i.rule_id == "shell-injection" for i in res_neg.issues)


def test_s5_unsafe_deserialization():
    pos = "import pickle, yaml\ndata = pickle.loads(raw)\ncfg = yaml.load(raw)"
    neg = "import yaml\ncfg = yaml.safe_load(raw)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "unsafe-deserialization" for i in res_pos.issues)
    assert not any(i.rule_id == "unsafe-deserialization" for i in res_neg.issues)


def test_s6_weak_hash():
    pos = "import hashlib\nh = hashlib.md5(b'data').hexdigest()"
    neg = "import hashlib\nh = hashlib.sha256(b'data').hexdigest()"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "weak-hash" for i in res_pos.issues)
    assert not any(i.rule_id == "weak-hash" for i in res_neg.issues)


def test_s7_tls_verify_disabled():
    pos = "import requests\nresp = requests.get('https://example.com', verify=False)"
    neg = "import requests\nresp = requests.get('https://example.com', verify=True)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "tls-verify-disabled" for i in res_pos.issues)
    assert not any(i.rule_id == "tls-verify-disabled" for i in res_neg.issues)


def test_s8_debug_mode_enabled():
    pos = "app.run(debug=True)\nDEBUG = True"
    neg = "app.run(debug=False)\nDEBUG = False"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "debug-mode-enabled" for i in res_pos.issues)
    assert not any(i.rule_id == "debug-mode-enabled" for i in res_neg.issues)


def test_s9_insecure_random():
    pos = "import random\nauth_token = random.randint(1000, 9999)"
    neg = "import secrets\nauth_token = secrets.token_hex(16)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "insecure-random" for i in res_pos.issues)
    assert not any(i.rule_id == "insecure-random" for i in res_neg.issues)


# ---------------------------------------------------------
# Bug / Reliability Rules Tests (B1 - B9)
# ---------------------------------------------------------

def test_b1_bare_except():
    pos = "try:\n    x = 1\nexcept:\n    x = 2"
    neg = "try:\n    x = 1\nexcept Exception:\n    x = 2"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "bare-except" for i in res_pos.issues)
    assert not any(i.rule_id == "bare-except" for i in res_neg.issues)


def test_b2_swallowed_exception():
    pos = "try:\n    x = 1\nexcept ValueError:\n    pass"
    neg = "try:\n    x = 1\nexcept ValueError:\n    logger.error('failed')"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "swallowed-exception" for i in res_pos.issues)
    assert not any(i.rule_id == "swallowed-exception" for i in res_neg.issues)


def test_b3_mutable_default_arg():
    pos = "def process(items=[]):\n    pass"
    neg = "def process(items=None):\n    if items is None:\n        items = []"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "mutable-default-arg" for i in res_pos.issues)
    assert not any(i.rule_id == "mutable-default-arg" for i in res_neg.issues)


def test_b4_none_comparison():
    pos = "if x == None or y != None:\n    pass"
    neg = "if x is None or y is not None:\n    pass"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "none-comparison" for i in res_pos.issues)
    assert not any(i.rule_id == "none-comparison" for i in res_neg.issues)


def test_b5_unreachable_code():
    pos = "def calculate():\n    return 42\n    print('never reached')"
    neg = "def calculate():\n    print('calculating')\n    return 42"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "unreachable-code" for i in res_pos.issues)
    assert not any(i.rule_id == "unreachable-code" for i in res_neg.issues)


def test_b6_shadowed_builtin():
    pos = "def fetch(id, list):\n    dict = {}\n    return dict"
    neg = "def fetch(item_id, item_list):\n    item_map = {}\n    return item_map"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "shadowed-builtin" for i in res_pos.issues)
    assert not any(i.rule_id == "shadowed-builtin" for i in res_neg.issues)


def test_b7_unused_variable():
    pos = "def foo():\n    unused_item = 10\n    return 42"
    neg = "def foo():\n    _ = 10\n    used_item = 10\n    return used_item"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "unused-variable" for i in res_pos.issues)
    assert not any(i.rule_id == "unused-variable" for i in res_neg.issues)


def test_b8_unused_import():
    pos = "import math\nfrom os import path\nx = 10"
    neg = "import math\nx = math.sqrt(10)"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "unused-import" for i in res_pos.issues)
    assert not any(i.rule_id == "unused-import" for i in res_neg.issues)


def test_b9_missing_resource_close():
    pos = "f = open('data.txt')\ncontent = f.read()"
    neg = "with open('data.txt') as f:\n    content = f.read()"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "missing-resource-close" for i in res_pos.issues)
    assert not any(i.rule_id == "missing-resource-close" for i in res_neg.issues)


# ---------------------------------------------------------
# Maintainability / Style Rules Tests (M1 - M10)
# ---------------------------------------------------------

def test_m1_function_too_long():
    lines = ["def very_long_function():"] + ["    x = 1"] * 55
    pos = "\n".join(lines)
    neg = "def short_func():\n    return 1"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "function-too-long" for i in res_pos.issues)
    assert not any(i.rule_id == "function-too-long" for i in res_neg.issues)


def test_m2_deep_nesting():
    pos = """
def deep():
    if True:
        for i in range(1):
            while False:
                try:
                    if 1:
                        print(1)
                except Exception:
                    pass
"""
    neg = """
def shallow():
    if True:
        print(1)
"""
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "deep-nesting" for i in res_pos.issues)
    assert not any(i.rule_id == "deep-nesting" for i in res_neg.issues)


def test_m3_too_many_parameters():
    pos = "def func(a, b, c, d, e, f, g):\n    return a"
    neg = "def func(a, b, c):\n    return a"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "too-many-parameters" for i in res_pos.issues)
    assert not any(i.rule_id == "too-many-parameters" for i in res_neg.issues)


def test_m4_high_complexity():
    branches = "\n".join([f"    if x == {i}: return {i}" for i in range(15)])
    pos = f"def complex_fn(x):\n{branches}\n    return -1"
    neg = "def simple_fn(x):\n    return x + 1"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "high-complexity" for i in res_pos.issues)
    assert not any(i.rule_id == "high-complexity" for i in res_neg.issues)


def test_m5_missing_docstring():
    pos = "def public_no_doc():\n    pass\nclass MyClass:\n    pass"
    neg = 'def public_with_doc():\n    """Documented."""\n    pass'
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "missing-docstring" for i in res_pos.issues)
    assert not any(i.rule_id == "missing-docstring" for i in res_neg.issues)


def test_m6_magic_number():
    pos = "if status_code == 404 or retry_count > 99:\n    pass"
    neg = "if status_code == 0 or retry_count == 1:\n    pass"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "magic-number" for i in res_pos.issues)
    assert not any(i.rule_id == "magic-number" for i in res_neg.issues)


def test_m7_duplicate_code():
    block = "    a = 1\n    b = 2\n    c = 3\n    d = 4\n    e = 5\n"
    pos = f"def fn1():\n{block}\ndef fn2():\n{block}"
    neg = "def fn1():\n    a = 1\ndef fn2():\n    b = 2"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "duplicate-code" for i in res_pos.issues)
    assert not any(i.rule_id == "duplicate-code" for i in res_neg.issues)


def test_m8_todo_comment():
    pos = "# TODO: refactor this method\nx = 1"
    neg = "# Regular explanation comment\nx = 1"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "todo-comment" for i in res_pos.issues)
    assert not any(i.rule_id == "todo-comment" for i in res_neg.issues)


def test_m9_print_statement():
    pos = "def debug_me():\n    print('debugging info')"
    neg = "import logging\ndef log_me():\n    logging.info('info')"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "print-statement" for i in res_pos.issues)
    assert not any(i.rule_id == "print-statement" for i in res_neg.issues)


def test_m10_naming_convention():
    pos = "def myBadFunction():\n    pass\nclass bad_class:\n    pass"
    neg = "def my_good_function():\n    pass\nclass GoodClass:\n    pass"
    res_pos = analyze_code(pos)
    res_neg = analyze_code(neg)
    assert any(i.rule_id == "naming-convention" for i in res_pos.issues)
    assert not any(i.rule_id == "naming-convention" for i in res_neg.issues)


def test_syntax_error_handling():
    code = "def broken(\n   return 42"
    res = analyze_code(code)
    assert res.score == 0
    assert res.grade == "F"
    assert len(res.issues) == 1
    assert res.issues[0].rule_id == "syntax-error"
