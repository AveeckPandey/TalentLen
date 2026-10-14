"""Tests for GitHub enrichment, metrics, cohorts, and caching."""

import pytest
from unittest.mock import patch, MagicMock
from src.enrichment.github_client import GitHubClient
from src.models import GitHubMetrics


def test_github_unlinked_candidate():
    client = GitHubClient()
    metrics, score, summary = client.enrich_profile(None)
    assert score == 0.0
    assert metrics.status == "unlinked"
    assert metrics.cohort == "Unlinked / Missing"


def test_github_caching(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    client = GitHubClient(cache_file=cache_file)
    
    # Pre-populate cache
    cached_metrics = GitHubMetrics(
        username="testuser",
        account_age_years=3.0,
        public_repos=15,
        recent_commits=42,
        cohort="Veteran Builder",
        status="enriched"
    )
    client._record_cache("testuser", cached_metrics, 9.0, "Veteran Builder (3.0 yrs, 15 repos)")

    # Call should hit cache without network
    metrics, score, summary = client.enrich_profile("testuser")
    assert score == 9.0
    assert metrics.public_repos == 15
    assert metrics.cohort == "Veteran Builder"


def test_github_rate_limit_resilience():
    client = GitHubClient()
    
    # Mock rate limited response
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch("httpx.Client.get", return_value=mock_resp):
        metrics, score, summary = client.enrich_profile("ratelimiteduser")
        assert score == 0.0
        assert metrics.status == "rate_limited"
        assert "rate limit exceeded" in summary.lower()
