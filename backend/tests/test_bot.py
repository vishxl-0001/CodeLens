from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from github_bot.bot import app

client = TestClient(app)


def test_bot_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_bot_ignores_non_pr_event():
    resp = client.post(
        "/webhook",
        headers={"X-GitHub-Event": "push"},
        json={"ref": "refs/heads/main"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_bot_dry_run_pr():
    payload = {
        "action": "opened",
        "number": 42,
        "repository": {"full_name": "example/repo"},
        "pull_request": {
            "number": 42,
            "head": {"sha": "abc12345"}
        }
    }
    resp = client.post(
        "/webhook",
        headers={"X-GitHub-Event": "pull_request"},
        json=payload
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "dry_run_success"
