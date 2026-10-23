from __future__ import annotations

import os
import httpx
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AnalysisResult,
    AnalyzeRequest,
    FixRequest,
    FixResponse,
    SampleItem,
    ExplainRequest,
    ExplainResponse,
)
from app.analyzer.engine import analyze_code
from app.fixes.engine import apply_fixes

app = FastAPI(
    title="CodeLens Analysis Engine",
    description="Deterministic Python Code Review and Auto-Fix API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_CODE_BYTES = 200 * 1024  # 200 KB

# Determine samples directory path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"


def validate_code_size(code_bytes: bytes) -> None:
    if len(code_bytes) > MAX_CODE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Payload Too Large: Python code exceeds maximum allowed size of 200KB ({len(code_bytes)} bytes provided).",
        )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/samples", response_model=List[SampleItem])
def get_samples():
    samples_meta = [
        {
            "id": "terrible",
            "name": "terrible.py",
            "filename": "terrible.py",
            "description": "Legacy script intentionally containing every security, bug, and style rule violation (Grade F).",
        },
        {
            "id": "average",
            "name": "average.py",
            "filename": "average.py",
            "description": "Typical day-to-day code with moderate technical debt and minor style issues (Grade C).",
        },
        {
            "id": "clean",
            "name": "clean.py",
            "filename": "clean.py",
            "description": "Production-grade, fully typed, documented user management module (Grade A).",
        },
        {
            "id": "flask_app",
            "name": "flask_app.py",
            "filename": "flask_app.py",
            "description": "Realistic microservice with SQL injection, hardcoded secret, and debug enabled.",
        },
    ]

    result: List[SampleItem] = []
    for meta in samples_meta:
        file_path = SAMPLES_DIR / meta["filename"]
        code = ""
        if file_path.exists():
            code = file_path.read_text(encoding="utf-8")
        result.append(
            SampleItem(
                id=meta["id"],
                name=meta["name"],
                description=meta["description"],
                code=code,
            )
        )
    return result


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzeRequest):
    code_bytes = payload.code.encode("utf-8")
    validate_code_size(code_bytes)
    return analyze_code(payload.code, filename=payload.filename or "input.py")


@app.post("/api/analyze-file", response_model=AnalysisResult)
async def analyze_file(file: UploadFile = File(...)):
    contents = await file.read()
    validate_code_size(contents)
    try:
        source_code = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be UTF-8 encoded Python source code.",
        )
    return analyze_code(source_code, filename=file.filename or "upload.py")


@app.post("/api/fix", response_model=FixResponse)
def fix_code(payload: FixRequest):
    code_bytes = payload.code.encode("utf-8")
    validate_code_size(code_bytes)

    # First analyze current code to obtain issue references
    analysis = analyze_code(payload.code)
    return apply_fixes(
        code=payload.code,
        issues=analysis.issues,
        target_issue_id=payload.issue_id,
        fix_all=bool(payload.fix_all),
    )


@app.post("/api/explain", response_model=ExplainResponse)
async def explain_issue(payload: ExplainRequest):
    """Optional AI explanation endpoint with graceful offline fallback to built-in explanation."""
    analysis = analyze_code(payload.code)
    issue = next((i for i in analysis.issues if i.id == payload.issue_id), None)

    if not issue:
        # Try matching by rule_id if line changed
        issue = next((i for i in analysis.issues if payload.issue_id.startswith(i.rule_id)), None)

    if not issue:
        return ExplainResponse(
            explanation="The requested issue could not be located in the current code analysis.",
            source="builtin",
        )

    fallback_explanation = (
        f"**{issue.title}** ({issue.severity.upper()} severity):\n\n"
        f"{issue.why_it_matters}\n\n"
        f"**Recommendation**: {issue.suggestion}"
    )

    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

    # Extract relevant code slice around issue line
    lines = payload.code.splitlines()
    start_line = max(0, issue.line - 6)
    end_line = min(len(lines), issue.end_line + 6)
    snippet = "\n".join(lines[start_line:end_line])

    prompt = (
        f"You are a senior Python security engineer. Concisely explain this code issue:\n"
        f"Rule: {issue.title} ({issue.rule_id})\n"
        f"Offending line {issue.line}: {issue.message}\n"
        f"Code context:\n```python\n{snippet}\n```\n"
        f"Explain in 2-3 clear paragraphs why this matters and how to safely fix it."
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{ollama_host}/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                ai_text = data.get("response", "").strip()
                if ai_text:
                    return ExplainResponse(explanation=ai_text, source="ollama")
    except Exception:
        pass

    return ExplainResponse(explanation=fallback_explanation, source="builtin")
