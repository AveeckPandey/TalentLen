// Mirrors src/models.py — keep in sync with the FastAPI backend.
export interface ScoreBreakdown {
  ai_project_depth: number;
  python_backend: number;
  cloud_fullstack: number;
  github: number;
  engineering_depth: number;
}

export interface GitHubMetrics {
  username?: string | null;
  profile_url?: string | null;
  account_age_years: number;
  public_repos: number;
  original_repos_count: number;
  recent_commits: number;
  prs_count: number;
  issues_count: number;
  total_contributions: number;
  total_stars: number;
  recent_events_count: number;
  relevant_ai_python_repos: number;
  cohort: string;
  status: string;
}

export interface CandidateResult {
  rank: number | null;
  candidate_name: string;
  file_name: string;
  eligible: boolean;
  total_score: number;
  score_breakdown: ScoreBreakdown;
  matched_skills: string[];
  project_summary: string;
  github_summary: string;
  strengths: string[];
  concerns: string[];
  rejection_reasons: string[];
  reason_50_to_100_words: string;
  email?: string | null;
  phone?: string | null;
  resume_url?: string | null;
  github_metrics?: GitHubMetrics | null;
  cgpa?: number | null;
  has_related_experience: boolean;
  penalties_applied: string[];
}

export interface BatchSummary {
  total_resumes: number;
  successfully_parsed: number;
  eligible: number;
  rejected: number;
  failed_unreadable: number;
  github_cohorts: Record<string, number>;
  average_score_eligible: number;
}

export interface ScreeningReport {
  batch_summary: BatchSummary;
  ranked_candidates: CandidateResult[];
  rejected_candidates: CandidateResult[];
}

export type ActiveTab = "eligible" | "rejected";
export type TopNLimit = "all" | 5 | 10 | 20;
