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

export interface ProjectEvaluationResult {
  project_count: number;
  ai_project_score: number;
  project_titles: string[];
  strengths: string[];
  penalties: string[];
  is_tutorial_or_shallow: boolean;
  architectural_summary: string;
  evaluation_source: string;
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
  project_count?: number;
  project_evaluation?: ProjectEvaluationResult | null;
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

export interface FilterPreferences {
  target_role?: string;
  required_skills?: string[];
  min_cgpa?: number | null;
  require_ai_project?: boolean;
  require_experience?: boolean;
  require_github_link?: boolean;
}

export type PlanTier = "free" | "pro_29" | "enterprise";

export interface UserQuota {
  user_id: string;
  tier: PlanTier;
  tier_display_name: string;
  price_usd: number;
  screenings_limit: number;
  screenings_used: number;
  screenings_remaining: number;
  max_resumes_per_batch: number;
  can_screen: boolean;
}


export type ActiveTab = "eligible" | "rejected";
export type TopNLimit = "all" | 5 | 10 | 20;

export interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  tier: PlanTier;
  tier_name: string;
}

export interface VerifyPaymentResponse {
  status: string;
  message: string;
  tier: PlanTier;
  quota: UserQuota;
}

export interface ApiKeyItem {
  key_id: string;
  key_prefix: string;
  name: string;
  user_id: string;
  created_at: string;
  last_used_at?: string | null;
  is_active: boolean;
}

export interface CreateApiKeyResponse {
  key_id: string;
  key_prefix: string;
  name: string;
  api_key: string;
  created_at: string;
  message: string;
}

export interface ScreeningHistoryItem {
  batch_id: string;
  user_id: string;
  target_role: string;
  total_resumes: number;
  eligible_count: number;
  rejected_count: number;
  avg_score: number;
  top_score: number;
  created_at: string;
}

