"""Pydantic data models for candidate screening, scoring, and output schemas."""

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
    """Dynamic filtering criteria for UI dials and CLI overrides."""
    min_cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Minimum CGPA on 10.0 scale")
    require_ai_project: bool = Field(default=True, description="Strict AI project presence")
    require_experience: bool = Field(default=False, description="Require verified work/internship experience")
    require_github_link: bool = Field(default=False, description="Require public GitHub profile link")
