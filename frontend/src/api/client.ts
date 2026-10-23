import { AnalysisResult, FixResponse, SampleItem, ExplainResponse } from "../types";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function checkHealth(): Promise<{ status: string }> {
  const resp = await fetch(`${API_BASE_URL}/api/health`);
  if (!resp.ok) {
    throw new ApiError(`Health check failed: ${resp.statusText}`, resp.status);
  }
  return resp.json();
}

export async function getSamples(): Promise<SampleItem[]> {
  const resp = await fetch(`${API_BASE_URL}/api/samples`);
  if (!resp.ok) {
    throw new ApiError(`Failed to load samples: ${resp.statusText}`, resp.status);
  }
  return resp.json();
}

export async function analyzeCode(code: string, filename = "main.py"): Promise<AnalysisResult> {
  const resp = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, filename }),
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Analysis failed with code ${resp.status}`, resp.status);
  }
  return resp.json();
}

export async function analyzeFile(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await fetch(`${API_BASE_URL}/api/analyze-file`, {
    method: "POST",
    body: formData,
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `File analysis failed with code ${resp.status}`, resp.status);
  }
  return resp.json();
}

export async function applyFix(
  code: string,
  issueId?: string,
  fixAll = false
): Promise<FixResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/fix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, issue_id: issueId, fix_all: fixAll }),
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Fix operation failed with code ${resp.status}`, resp.status);
  }
  return resp.json();
}

export async function explainIssue(code: string, issueId: string): Promise<ExplainResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, issue_id: issueId }),
  });
  if (!resp.ok) {
    throw new ApiError(`AI Explanation request failed with code ${resp.status}`, resp.status);
  }
  return resp.json();
}
