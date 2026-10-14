"""Tests for 50-100 word narrative reasoning engine."""

import pytest
from src.llm.adapter import HeuristicAdapter


def test_narrative_word_count_eligible():
    adapter = HeuristicAdapter()
    text = adapter.generate_narrative_reason(
        candidate_name="Asha Rao",
        eligible=True,
        total_score=86.0,
        breakdown_dict={"ai_project_depth": 35, "python_backend": 27},
        strengths=["Stateful multi-agent orchestration", "Async FastAPI backend"],
        concerns=["Limited Redis caching evidence"],
        rejection_reasons=[],
        matched_skills=["Python", "FastAPI", "LangGraph", "Docker"],
        github_summary="Active Builder (2.5 yrs on GitHub, 14 repos, 32 commits).",
    )

    words = text.split()
    assert 50 <= len(words) <= 100, f"Expected 50-100 words, got {len(words)}: {text}"
    assert "Asha Rao" in text
    assert "86.0" in text


def test_narrative_word_count_rejected():
    adapter = HeuristicAdapter()
    text = adapter.generate_narrative_reason(
        candidate_name="Rohan Sharma",
        eligible=False,
        total_score=0.0,
        breakdown_dict={},
        strengths=[],
        concerns=[],
        rejection_reasons=["No evidence of Python stack", "No AI/agentic project evidence"],
        matched_skills=["React", "Next.js", "TypeScript"],
        github_summary="Skipped",
    )

    words = text.split()
    assert 50 <= len(words) <= 100, f"Expected 50-100 words, got {len(words)}: {text}"
    assert "ineligible" in text.lower() or "rejected" in text.lower()
    assert "python" in text.lower()
