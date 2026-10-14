"""GitHub API client for candidate activity enrichment, caching, and cohort analysis."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import httpx

from src.config import settings
from src.models import GitHubMetrics

logger = logging.getLogger(__name__)


class GitHubClient:
    """Fetches public GitHub activity, calculates metrics, cohorts, and scores."""

    def __init__(self, token: Optional[str] = None, cache_file: Optional[Path] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.cache_file = cache_file or settings.GITHUB_CACHE_FILE
        self._cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cached profiles from disk if available."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load GitHub cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Persist cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save GitHub cache: {e}")

    def _get_headers(self) -> Dict[str, str]:
        """Generate HTTP headers with optional authorization token."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Kasparro-Resume-Screener/1.0",
        }
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def enrich_profile(self, username: Optional[str]) -> Tuple[GitHubMetrics, float, str]:
        """
        Enrich a GitHub username.
        Returns:
            Tuple of (GitHubMetrics, github_score_0_to_10, github_summary_text)
        """
        if not username:
            metrics = GitHubMetrics(
                status="unlinked",
                cohort="Unlinked / Missing",
            )
            return metrics, 0.0, "No public GitHub profile provided."

        user_clean = username.strip().lower()

        # Check in-memory/file cache first
        if user_clean in self._cache:
            data = self._cache[user_clean]
            metrics = GitHubMetrics(**data["metrics"])
            return metrics, data["score"], data["summary"]

        headers = self._get_headers()
        base_url = "https://api.github.com"

        try:
            with httpx.Client(timeout=settings.REQUEST_TIMEOUT, headers=headers) as client:
                # 1. Fetch User Profile
                user_resp = client.get(f"{base_url}/users/{username}")
                if user_resp.status_code == 404:
                    metrics = GitHubMetrics(
                        username=username,
                        profile_url=f"https://github.com/{username}",
                        status="profile_not_found",
                        cohort="Unlinked / Missing",
                    )
                    summary = f"GitHub user '{username}' not found (404)."
                    self._record_cache(user_clean, metrics, 0.0, summary)
                    return metrics, 0.0, summary

                if user_resp.status_code in [403, 429]:
                    metrics = GitHubMetrics(
                        username=username,
                        profile_url=f"https://github.com/{username}",
                        status="rate_limited",
                        cohort="Unverified (Rate Limited)",
                    )
                    summary = "GitHub API rate limit exceeded; skipped enrichment."
                    return metrics, 0.0, summary

                if user_resp.status_code != 200:
                    metrics = GitHubMetrics(
                        username=username,
                        status=f"http_{user_resp.status_code}",
                        cohort="Unverified",
                    )
                    return metrics, 0.0, f"GitHub API error (HTTP {user_resp.status_code})."

                user_info = user_resp.json()
                public_repos = user_info.get("public_repos", 0)
                created_str = user_info.get("created_at")

                # Compute account age in years
                now = datetime.now(timezone.utc)
                age_years = 0.0
                if created_str:
                    created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    age_years = round((now - created_dt).total_seconds() / (365.25 * 86400), 1)

                # 2. Fetch Public Events (recent activity pulse, commits, and PRs)
                events_resp = client.get(f"{base_url}/users/{username}/events/public?per_page=100")
                events = events_resp.json() if events_resp.status_code == 200 else []

                recent_commits = 0
                prs_count = 0
                issues_count = 0
                days_since_active = 999
                if isinstance(events, list) and events:
                    # Parse latest event date
                    latest_str = events[0].get("created_at")
                    if latest_str:
                        latest_dt = datetime.fromisoformat(latest_str.replace("Z", "+00:00"))
                        days_since_active = (now - latest_dt).days

                    # Track events: commits, PRs, issues
                    for ev in events:
                        ev_type = ev.get("type")
                        if ev_type == "PushEvent":
                            commits = ev.get("payload", {}).get("commits", [])
                            recent_commits += len(commits)
                        elif ev_type in ["PullRequestEvent", "PullRequestReviewEvent"]:
                            prs_count += 1
                        elif ev_type in ["IssuesEvent", "IssueCommentEvent"]:
                            issues_count += 1

                total_events_activity = recent_commits + prs_count + issues_count

                # 3. Fetch Annual Contributions Calendar (captures the full 1-year contributions shown on user's GitHub profile)
                calendar_contributions = 0
                try:
                    cal_resp = client.get(
                        f"https://github.com/users/{username}/contributions",
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    )
                    if cal_resp.status_code == 200:
                        import re
                        m_cal = re.search(r'([0-9,]+)\s+contributions?\s+in\s+the\s+last\s+year', cal_resp.text, re.IGNORECASE)
                        if not m_cal:
                            m_cal = re.search(r'([0-9,]+)\s+contributions?\s+in', cal_resp.text, re.IGNORECASE)
                        if m_cal:
                            calendar_contributions = int(m_cal.group(1).replace(",", ""))
                except Exception as cal_err:
                    logger.debug(f"Could not fetch contributions calendar for {username}: {cal_err}")

                total_contributions = max(total_events_activity, calendar_contributions)

                # 4. Fetch Repositories for relevance, stars, and original vs forked ratio
                repos_resp = client.get(f"{base_url}/users/{username}/repos?sort=updated&per_page=30")
                repos = repos_resp.json() if repos_resp.status_code == 200 else []

                relevant_ai_python = 0
                original_repos = 0
                total_stars = 0
                if isinstance(repos, list):
                    for repo in repos:
                        if not repo.get("fork", False):
                            original_repos += 1
                        total_stars += repo.get("stargazers_count", 0)

                        lang = (repo.get("language") or "").lower()
                        desc = (repo.get("description") or "").lower()
                        name = (repo.get("name") or "").lower()
                        topics = [t.lower() for t in repo.get("topics", [])]
                        
                        is_python = lang == "python" or "python" in desc
                        is_ai = any(kw in f"{name} {desc} {' '.join(topics)}" for kw in [
                            "ai", "rag", "agent", "llm", "langchain", "langgraph", "fastapi", "embeddings"
                        ])

                        if is_python or is_ai:
                            relevant_ai_python += 1

                # 5. Cohort Classification
                cohort = self._determine_cohort(age_years, public_repos, total_contributions, days_since_active)

                # 6. Calculate Score (0-10)
                # 0-5 for recency, commits, and PR contributions
                activity_score = 0.0
                if days_since_active <= 30:
                    activity_score = 5.0
                elif days_since_active <= 90:
                    activity_score = 3.5
                elif days_since_active <= 365 or total_contributions > 0:
                    activity_score = 2.5
                
                if total_contributions >= 50:
                    activity_score = max(activity_score, 4.0)
                elif total_contributions >= 10:
                    activity_score = max(activity_score, 3.0)

                # Extra booster for PR collaboration
                if prs_count > 0:
                    activity_score = min(5.0, activity_score + 0.5)

                # 0-5 for maintained & relevant repos (rewarding original repos and stars)
                repo_score = 0.0
                if relevant_ai_python >= 3:
                    repo_score = 5.0
                elif relevant_ai_python >= 1:
                    repo_score = 3.5
                elif original_repos >= 4:
                    repo_score = 2.5
                elif public_repos >= 1:
                    repo_score = 1.0

                if total_stars >= 5:
                    repo_score = min(5.0, repo_score + 0.5)

                total_gh_score = min(10.0, round(activity_score + repo_score, 1))

                # Human-readable summary
                pr_text = f", {prs_count} PRs" if prs_count > 0 else ""
                star_text = f", {total_stars} stars" if total_stars > 0 else ""
                summary = (
                    f"{cohort} ({age_years} yrs on GitHub, {public_repos} repos [{original_repos} original], "
                    f"{total_contributions} contributions in past year [{recent_commits} commits{pr_text}]{star_text}). "
                    f"{relevant_ai_python} relevant Python/AI repositories identified."
                )

                metrics = GitHubMetrics(
                    username=username,
                    profile_url=f"https://github.com/{username}",
                    account_age_years=age_years,
                    public_repos=public_repos,
                    original_repos_count=original_repos,
                    recent_commits=recent_commits,
                    prs_count=prs_count,
                    issues_count=issues_count,
                    total_contributions=total_contributions,
                    total_stars=total_stars,
                    recent_events_count=len(events) if isinstance(events, list) else 0,
                    relevant_ai_python_repos=relevant_ai_python,
                    cohort=cohort,
                    status="enriched",
                )

                self._record_cache(user_clean, metrics, total_gh_score, summary)
                return metrics, total_gh_score, summary

        except Exception as e:
            logger.warning(f"GitHub client exception for {username}: {e}")
            metrics = GitHubMetrics(
                username=username,
                profile_url=f"https://github.com/{username}",
                status=f"error: {str(e)[:40]}",
                cohort="Unverified",
            )
            return metrics, 0.0, f"GitHub lookup skipped due to network/API error."

    def _determine_cohort(
        self, age_years: float, repos: int, contributions: int, days_since_active: int
    ) -> str:
        """Classify candidate into an intuitive GitHub developer cohort."""
        if repos == 0 and contributions == 0:
            return "Dormant / Minimal"
        if age_years >= 3.0 and repos >= 8 and (contributions > 0 or days_since_active <= 120):
            return "Veteran Builder"
        if age_years >= 1.0 and repos >= 4 and (contributions > 0 or days_since_active <= 90):
            return "Active Builder"
        if age_years < 1.0 or repos < 4:
            return "Emerging Developer"
        return "Active Developer"

    def _record_cache(
        self, user_clean: str, metrics: GitHubMetrics, score: float, summary: str
    ) -> None:
        """Store in cache and save."""
        self._cache[user_clean] = {
            "metrics": metrics.model_dump(),
            "score": score,
            "summary": summary,
        }
        self._save_cache()
