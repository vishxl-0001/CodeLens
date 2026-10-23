"""CodeLens GitHub PR Review Webhook Bot.

Listens for GitHub `pull_request` webhook events, executes static analysis on changed
Python files, and posts a comprehensive review with inline line-level comments.
"""

from __future__ import annotations

import os
import sys
import hmac
import hashlib
from typing import Dict, Any, List
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import httpx
from fastapi import FastAPI, Request, Header, HTTPException, status
from app.analyzer.engine import analyze_code

app = FastAPI(title="CodeLens GitHub Bot", version="1.0.0")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in {"true", "1", "yes"}


def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    if not GITHUB_WEBHOOK_SECRET:
        return True  # If no secret configured, skip verification
    if not signature_header:
        return False
    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)


@app.get("/health")
def health():
    return {"status": "ok", "dry_run": DRY_RUN}


@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"Event '{x_github_event}' is not pull_request"}

    payload: Dict[str, Any] = await request.json()
    action = payload.get("action")
    if action not in {"opened", "synchronize", "reopened"}:
        return {"status": "ignored", "reason": f"Action '{action}' does not trigger review"}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    repo_full_name = repo.get("full_name")
    pr_number = pr.get("number")
    commit_sha = pr.get("head", {}).get("sha")

    if not repo_full_name or not pr_number:
        raise HTTPException(status_code=400, detail="Missing repository or PR metadata")

    print(f"\n[CodeLens Bot] Inspecting PR #{pr_number} in {repo_full_name}...")

    # Fetch changed files
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # In dry run mode without token, we can mock or output
        files_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
        changed_files: List[Dict[str, Any]] = []

        if GITHUB_TOKEN:
            resp = await client.get(files_url, headers=headers)
            if resp.status_code == 200:
                changed_files = resp.json()
            else:
                print(f"[Error] Failed to fetch PR files: {resp.status_code} {resp.text}")
        else:
            print("[Notice] No GITHUB_TOKEN set; operating in dry-run simulation mode.")

        # Analyze each .py file
        comments: List[Dict[str, Any]] = []
        overall_scores: List[int] = []

        for file_info in changed_files:
            filename = file_info.get("filename", "")
            if not filename.endswith(".py"):
                continue

            raw_url = file_info.get("raw_url")
            file_content = ""
            if raw_url:
                raw_resp = await client.get(raw_url)
                if raw_resp.status_code == 200:
                    file_content = raw_resp.text

            if not file_content:
                continue

            analysis = analyze_code(file_content, filename=filename)
            overall_scores.append(analysis.score)

            for issue in analysis.issues:
                body_comment = (
                    f"**CodeLens [{issue.severity.upper()}] - {issue.title}**\n\n"
                    f"{issue.message}\n\n"
                    f"**Why it matters:** {issue.why_it_matters}\n\n"
                    f"💡 **Suggested Fix:** `{issue.suggestion}`\n"
                    f"{f'🔗 *Reference:* {issue.reference}' if issue.reference else ''}"
                )
                comments.append({
                    "path": filename,
                    "line": issue.line,
                    "body": body_comment,
                })

        avg_score = round(sum(overall_scores) / max(1, len(overall_scores))) if overall_scores else 100
        review_body = (
            f"## 🔍 CodeLens Automated Review Summary\n\n"
            f"- **Code Health Score**: `{avg_score}/100`\n"
            f"- **Total Issues Found**: `{len(comments)}`\n"
            f"- **Analyzed Files**: `{len(overall_scores)}`\n\n"
            f"{'⚠️ Please address critical security and bug issues before merging.' if avg_score < 75 else '✅ Code meets quality bar!'}"
        )

        if DRY_RUN or not GITHUB_TOKEN:
            print("================== DRY RUN REVIEW OUTPUT ==================")
            print(review_body)
            print(f"Generated {len(comments)} inline comments:")
            for c in comments:
                print(f" - [{c['path']}:{c['line']}] {c['body'][:80]}...")
            print("===========================================================")
            return {
                "status": "dry_run_success",
                "score": avg_score,
                "comments_count": len(comments),
            }

        # Submit GitHub PR Review
        review_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"
        review_payload = {
            "commit_id": commit_sha,
            "body": review_body,
            "event": "REQUEST_CHANGES" if avg_score < 60 else "COMMENT",
            "comments": comments,
        }

        review_resp = await client.post(review_url, headers=headers, json=review_payload)
        return {
            "status": "review_posted",
            "github_status": review_resp.status_code,
            "score": avg_score,
            "comments_count": len(comments),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
