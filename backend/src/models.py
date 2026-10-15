"""Pydantic data models for candidate screening, scoring, and output schemas."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Breakdown of candidate 100-point score across all 5 categories."""
    ai_project_depth: float = Field(default=0.0, ge=0, le=40, description="Max 40 points")
    python_backend: float = Field(default=0.0, ge=0, le=30, description="Max 30 points")
    cloud_fullstack: float = Field(default=0.0, ge=0, le=15, description="Max 15 points")
    github: float = Field(default=0.0, ge=0, le=10, description="Max 10 points")
    engineering_depth: float = Field(default=0.0, ge=0, le=5, description="Max 5 points")


class GitHubMetrics(BaseModel):
    """Detailed GitHub activity metrics."""
    username: Optional[str] = None
    profile_url: Optional[str] = None
    account_age_years: float = Field(default=0.0, description="Years since GitHub account creation")
    public_repos: int = Field(default=0, description="Total public repositories")
    original_repos_count: int = Field(default=0, description="Non-forked original repositories")
    recent_commits: int = Field(default=0, description="Total commits in recent public events")
    prs_count: int = Field(default=0, description="Total Pull Requests created/participated")
    issues_count: int = Field(default=0, description="Issues opened or participated in")
    total_contributions: int = Field(default=0, description="Total contributions (commits + PRs + issues + reviews)")
    total_stars: int = Field(default=0, description="Total stars received across public repos")
    recent_events_count: int = Field(default=0, description="Count of recent public events")
    relevant_ai_python_repos: int = Field(default=0, description="Count of Python / AI / Backend repositories")
    cohort: str = Field(default="Unlinked / Missing", description="Veteran Builder, Active Builder, Emerging, Dormant, Unlinked")
    status: str = Field(default="not_checked", description="enriched, rate_limited, profile_not_found, unlinked, error")


class ParsedResume(BaseModel):
    """Raw parsed data extracted from a candidate resume file."""
    file_name: str
    file_path: str
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    cgpa: Optional[float] = None
    cgpa_raw: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    projects_text: str = ""
    experience_text: str = ""
    has_related_experience: bool = False
    estimated_experience_years: float = 0.0
    full_text: str = ""
    parsing_status: str = "success"  # success, error, partial


class EligibilityResult(BaseModel):
    """Hard filter eligibility decision."""
    candidate: str
    eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    python_evidence: List[str] = Field(default_factory=list)
    ai_evidence: List[str] = Field(default_factory=list)


class ProjectEvaluationResult(BaseModel):
    """Structured evaluation of candidate projects (Groq API or Heuristic fallback)."""
    project_count: int = Field(default=0, ge=0, description="Total distinct projects identified")
    ai_project_score: float = Field(default=0.0, ge=0, le=40, description="Evaluated score for AI/Agentic/RAG project depth (0-40)")
    project_titles: List[str] = Field(default_factory=list, description="Titles/names of identified projects")
    strengths: List[str] = Field(default_factory=list, description="Architectural strengths identified in projects")
    penalties: List[str] = Field(default_factory=list, description="Penalties for thin wrappers, tutorial copies, etc.")
    is_tutorial_or_shallow: bool = Field(default=False, description="Flag if candidate only has tutorial or thin wrapper projects")
    architectural_summary: str = Field(default="", description="Concise assessment of project architecture and depth")
    evaluation_source: str = Field(default="heuristic", description="Source of evaluation: groq, openai, or heuristic")


class CandidateResult(BaseModel):
    """Screened candidate output matching required schema and extended fields."""
    rank: Optional[int] = Field(default=None, description="Ranking among eligible candidates (1-indexed)")
    candidate_name: str
    file_name: str
    eligible: bool
    total_score: float = Field(default=0.0, ge=0, le=100)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    matched_skills: List[str] = Field(default_factory=list)
    project_summary: str = ""
    github_summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    reason_50_to_100_words: str = Field(default="", description="Detailed 50-100 word justification")
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    github_metrics: Optional[GitHubMetrics] = None
    cgpa: Optional[float] = None
    has_related_experience: bool = False
    penalties_applied: List[str] = Field(default_factory=list)
    project_count: int = Field(default=0, description="Total distinct projects verified")
    project_evaluation: Optional[ProjectEvaluationResult] = Field(default=None, description="Detailed project intelligence evaluation")


class BatchSummary(BaseModel):
    """Overall batch processing statistics."""
    total_resumes: int = 0
    successfully_parsed: int = 0
    eligible: int = 0
    rejected: int = 0
    failed_unreadable: int = 0
    github_cohorts: Dict[str, int] = Field(default_factory=dict)
    average_score_eligible: float = 0.0


class ScreeningReport(BaseModel):
    """Complete screening report containing batch summary and candidate lists."""
    batch_summary: BatchSummary
    ranked_candidates: List[CandidateResult]
    rejected_candidates: List[CandidateResult]


class FilterPreferences(BaseModel):
    """Dynamic filtering criteria for HR pre-screening and UI dials."""
    target_role: Optional[str] = Field(default="Python Developer", description="Target role name (e.g. Python Developer, AI Engineer)")
    required_skills: List[str] = Field(default_factory=lambda: ["python"], description="Mandatory skills required by HR (e.g. ['python'])")
    min_cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Minimum CGPA on 10.0 scale")
    require_ai_project: bool = Field(default=True, description="Strict AI project presence")
    require_experience: bool = Field(default=False, description="Require verified work/internship experience")
    require_github_link: bool = Field(default=False, description="Require public GitHub profile link")


class PlanTier(str, Enum):
    """Available user billing and quota tiers."""
    FREE = "free"
    PRO_29 = "pro_29"
    ENTERPRISE = "enterprise"


class TierConfig(BaseModel):
    """Configuration limits and benefits for each tier."""
    tier: PlanTier
    display_name: str
    price_usd: int
    screenings_limit: int
    max_resumes_per_batch: int


TIER_CONFIGS: Dict[PlanTier, TierConfig] = {
    PlanTier.FREE: TierConfig(
        tier=PlanTier.FREE,
        display_name="Starter (Free)",
        price_usd=0,
        screenings_limit=3,
        max_resumes_per_batch=50,
    ),
    PlanTier.PRO_29: TierConfig(
        tier=PlanTier.PRO_29,
        display_name="Recruiter Pro",
        price_usd=29,
        screenings_limit=30,
        max_resumes_per_batch=100,
    ),
    PlanTier.ENTERPRISE: TierConfig(
        tier=PlanTier.ENTERPRISE,
        display_name="Enterprise",
        price_usd=99,
        screenings_limit=500,
        max_resumes_per_batch=500,
    ),
}


class UserQuota(BaseModel):
    """Current usage, limits, and remaining balance for a user/session."""
    user_id: str
    tier: PlanTier = PlanTier.FREE
    tier_display_name: str = "Starter (Free)"
    price_usd: int = 0
    screenings_limit: int = 3
    screenings_used: int = 0
    screenings_remaining: int = 3
    max_resumes_per_batch: int = 50
    can_screen: bool = True


class UpgradeRequest(BaseModel):
    """Payload to upgrade user tier."""
    tier: PlanTier = PlanTier.PRO_29


class CreateOrderRequest(BaseModel):
    """Payload to initiate a Razorpay checkout order."""
    tier: PlanTier = PlanTier.PRO_29
    currency: str = "INR"


class CreateOrderResponse(BaseModel):
    """Order details returned to frontend to initialize Razorpay checkout modal."""
    order_id: str
    amount: int  # in paise (e.g. 249900 = ₹2,499)
    currency: str
    key_id: str
    tier: PlanTier
    tier_name: str


class VerifyPaymentRequest(BaseModel):
    """Payload sent from frontend after user completes Razorpay payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    tier: PlanTier = PlanTier.PRO_29


class VerifyPaymentResponse(BaseModel):
    """Verification response returning updated user quota."""
    status: str
    message: str
    tier: PlanTier
    quota: UserQuota


class ApiKeyInfo(BaseModel):
    """Public representation of a user's API Key (raw secret omitted)."""
    key_id: str
    key_prefix: str
    name: str
    user_id: str
    created_at: str
    last_used_at: Optional[str] = None
    is_active: bool = True


class CreateApiKeyRequest(BaseModel):
    """Payload to generate a new API key."""
    name: str = "Default API Key"


class CreateApiKeyResponse(BaseModel):
    """Response returned ONLY once upon API key creation containing the raw secret."""
    key_id: str
    key_prefix: str
    name: str
    api_key: str  # Raw secret shown only once!
    created_at: str
    message: str = "Store this API key safely. You will not be able to view it again."


class ScreeningHistoryItem(BaseModel):
    """Metadata for a historical screening batch saved for the user."""
    batch_id: str
    user_id: str
    target_role: str
    total_resumes: int
    eligible_count: int
    rejected_count: int
    avg_score: float
    top_score: float
    created_at: str


