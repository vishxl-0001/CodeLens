from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_samples_endpoint():
    resp = client.get("/api/samples")
    assert resp.status_code == 200
    samples = resp.json()
    assert len(samples) >= 4
    sample_ids = [s["id"] for s in samples]
    assert "terrible" in sample_ids
    assert "average" in sample_ids
    assert "clean" in sample_ids
    assert "flask_app" in sample_ids


def test_analyze_endpoint():
    code = "def add(x, y):\n    return x + y\n"
    resp = client.post("/api/analyze", json={"code": code})
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "grade" in data
    assert "issues" in data
    assert "functions" in data
    assert "metrics" in data


def test_analyze_file_endpoint():
    file_content = b"x = 1\ny = 2\n"
    files = {"file": ("test.py", io.BytesIO(file_content), "text/x-python")}
    resp = client.post("/api/analyze-file", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] > 0


def test_fix_endpoint_single():
    code = "try:\n    x = 1\nexcept:\n    x = 2\n"
    # First analyze
    an_resp = client.post("/api/analyze", json={"code": code})
    issue_id = an_resp.json()["issues"][0]["id"]

    resp = client.post("/api/fix", json={"code": code, "issue_id": issue_id})
    assert resp.status_code == 200
    data = resp.json()
    assert "except Exception:" in data["fixed_code"]
    assert len(data["applied"]) == 1


def test_fix_endpoint_all():
    code = "if x == None:\n    pass\ntry:\n    y = 1\nexcept:\n    y = 2\n"
    resp = client.post("/api/fix", json={"code": code, "fix_all": True})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["applied"]) >= 2
    assert "is None" in data["fixed_code"]
    assert "except Exception:" in data["fixed_code"]


def test_payload_too_large():
    huge_code = "# Comment\n" * 25000  # > 200KB
    resp = client.post("/api/analyze", json={"code": huge_code})
    assert resp.status_code == 413


def test_syntax_error_not_500():
    broken_code = "def broken(:\n    pass"
    resp = client.post("/api/analyze", json={"code": broken_code})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 0
    assert data["grade"] == "F"
    assert len(data["issues"]) == 1
    assert data["issues"][0]["rule_id"] == "syntax-error"


def test_explain_fallback_offline():
    code = "import yaml\ncfg = yaml.load(raw)\n"
    an_resp = client.post("/api/analyze", json={"code": code})
    issue_id = an_resp.json()["issues"][0]["id"]

    resp = client.post("/api/explain", json={"code": code, "issue_id": issue_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] in ("ollama", "builtin")
    assert len(data["explanation"]) > 20


def test_samples_score_criteria():
    resp = client.get("/api/samples")
    samples = {s["id"]: s["code"] for s in resp.json()}

    # Clean must be >= 95
    res_clean = client.post("/api/analyze", json={"code": samples["clean"]}).json()
    assert res_clean["score"] >= 95, f"clean.py score was {res_clean['score']}"
    assert res_clean["grade"] == "A"

    # Terrible must be <= 35
    res_terrible = client.post("/api/analyze", json={"code": samples["terrible"]}).json()
    assert res_terrible["score"] <= 35, f"terrible.py score was {res_terrible['score']}"
    assert res_terrible["grade"] == "F"
    assert len(res_terrible["issues"]) >= 20

    # Average must be 60-75
    res_avg = client.post("/api/analyze", json={"code": samples["average"]}).json()
    assert 60 <= res_avg["score"] <= 75, f"average.py score was {res_avg['score']}"

    # Flask app should be analyzed
    res_flask = client.post("/api/analyze", json={"code": samples["flask_app"]}).json()
    assert any(i["rule_id"] == "sql-injection" for i in res_flask["issues"])
