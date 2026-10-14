"""Tests for candidate 100-point scoring model and quality penalties."""

import pytest
from src.models import ParsedResume, GitHubMetrics
from src.scoring.scorer import CandidateScorer


def test_high_depth_agentic_candidate_score():
    resume = ParsedResume(
        file_name="top_cand.pdf",
        file_path="top_cand.pdf",
        candidate_name="Top Candidate",
        full_text=(
            "Built stateful multi-agent system using LangGraph and ChromaDB vector search with hybrid search. "
            "Backend written in async FastAPI with PostgreSQL and SQLAlchemy, cached with Redis. "
            "Containerized with Docker and deployed on GCP. Tested with pytest in CI/CD pipeline."
        ),
        projects_text="LangGraph multi-agent orchestration, ChromaDB RAG, async FastAPI, PostgreSQL, Redis, Docker, GCP.",
        skills=["Python", "FastAPI", "LangGraph", "ChromaDB", "PostgreSQL", "Redis", "Docker", "GCP", "PyTest"]
    )
    gh_metrics = GitHubMetrics(
        cohort="Active Builder",
        account_age_years=2.5,
        public_repos=12,
        recent_commits=30,
        relevant_ai_python_repos=4,
    )
    total_score, breakdown, strengths, concerns, penalties, summary = CandidateScorer.score_candidate(
        resume, gh_metrics, github_score=8.5
    )

    assert total_score >= 75.0
    assert breakdown.ai_project_depth >= 25.0
    assert breakdown.python_backend >= 20.0
    assert len(penalties) == 0
    assert "Async FastAPI backend architecture" in strengths


def test_shallow_wrapper_penalty():
    # OpenAI API call without RAG, state, or tools
    resume = ParsedResume(
        file_name="wrapper_cand.pdf",
        file_path="wrapper_cand.pdf",
        candidate_name="Wrapper Dev",
        full_text="Created a ChatGPT clone using Streamlit and OpenAI API completion endpoint. Python, Flask.",
        projects_text="ChatGPT clone using Streamlit and OpenAI API.",
        skills=["Python", "OpenAI", "Streamlit"]
    )
    gh_metrics = GitHubMetrics()
    total_score, breakdown, strengths, concerns, penalties, summary = CandidateScorer.score_candidate(
        resume, gh_metrics, github_score=0.0
    )

    assert any("Thin LLM wrapper" in p for p in penalties)
    assert any("thin API wrapper" in c for c in concerns)
