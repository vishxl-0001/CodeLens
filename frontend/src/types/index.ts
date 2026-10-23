export type SeverityLevel = "critical" | "high" | "medium" | "low";
export type CategoryType = "security" | "bug" | "maintainability" | "style";
export type GradeType = "A" | "B" | "C" | "D" | "F";

export interface Issue {
  id: string;
  rule_id: string;
  title: string;
  message: string;
  severity: SeverityLevel;
  category: CategoryType;
  line: number;
  end_line: number;
  column: number;
  why_it_matters: string;
  suggestion: string;
  fixable: boolean;
  reference: string;
}

export interface FunctionMetric {
  name: string;
  line: number;
  end_line: number;
  length: number;
  cyclomatic_complexity: number;
  cognitive_complexity: number;
  max_nesting: number;
  params: number;
  rank: GradeType;
}

export interface AnalysisSummary {
  total_issues: number;
  by_severity: Record<SeverityLevel, number>;
  by_category: Record<CategoryType, number>;
  lines_of_code: number;
  analysis_ms: number;
}

export interface Subscores {
  security: number;
  reliability: number;
  maintainability: number;
}

export interface CodeMetrics {
  maintainability_index: number;
  avg_complexity: number;
  comment_ratio: number;
  docstring_coverage: number;
}

export interface AnalysisResult {
  score: number;
  grade: GradeType;
  summary: AnalysisSummary;
  subscores: Subscores;
  issues: Issue[];
  functions: FunctionMetric[];
  metrics: CodeMetrics;
}

export interface SampleItem {
  id: string;
  name: string;
  description: string;
  code: string;
}

export interface SkippedFix {
  issue_id: string;
  rule_id: string;
  reason: string;
}

export interface FixResponse {
  fixed_code: string;
  applied: string[];
  skipped: SkippedFix[];
}

export interface ExplainResponse {
  explanation: string;
  source: "ollama" | "builtin";
}
