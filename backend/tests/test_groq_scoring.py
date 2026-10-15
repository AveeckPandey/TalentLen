"""Unit and integration tests for Groq Project Intelligence & Deep Ranking Engine."""

import pytest
from unittest.mock import patch, MagicMock
from src.models import (
    ParsedResume,
    GitHubMetrics,
    ScoreBreakdown,
    CandidateResult,
    ProjectEvaluationResult,
)
from src.llm.adapter import GroqAdapter, OpenAIAdapter, HeuristicAdapter
from src.scoring.scorer import CandidateScorer
from src.pipeline import ScreeningPipeline


def test_heuristic_evaluate_projects_deep_architecture():
    """Verify HeuristicAdapter correctly detects project count and scores deep AI architecture."""
    adapter = HeuristicAdapter()
    projects_text = """
    1. Autonomous Multi-Agent Research Swarm:
       Architected with LangGraph and FastAPI. Built stateful graph with checkpointing in PostgreSQL.
       Integrated hybrid search with ChromaDB and Cohere reranker. Evaluated using Ragas.
    2. Real-Time Streaming RAG:
       Built with FastAPI, Redis semantic cache, and SSE streaming.
    """
    eval_result = adapter.evaluate_projects(
        candidate_name="Deep Engineer",
        projects_text=projects_text,
        experience_text="",
        skills=["Python", "FastAPI", "LangGraph", "ChromaDB"],
    )

    assert eval_result.project_count >= 2
    assert eval_result.ai_project_score >= 30.0
    assert not eval_result.is_tutorial_or_shallow
    assert any("multi-agent" in s.lower() or "langgraph" in s.lower() for s in eval_result.strengths)
    assert any("rag" in s.lower() or "chromadb" in s.lower() for s in eval_result.strengths)


def test_heuristic_evaluate_projects_tutorial_penalty():
    """Verify HeuristicAdapter detects tutorial clones and applies penalties."""
    adapter = HeuristicAdapter()
    projects_text = """
    1. Titanic Survival Classifier: Kaggle tutorial using Random Forest.
    2. Chat with PDF: Streamlit frontend calling OpenAI API.
    """
    eval_result = adapter.evaluate_projects(
        candidate_name="Junior Dev",
        projects_text=projects_text,
        experience_text="",
        skills=["Python", "Streamlit", "OpenAI"],
    )

    assert eval_result.project_count >= 2
    assert eval_result.is_tutorial_or_shallow is True
    assert len(eval_result.penalties) > 0
    assert eval_result.ai_project_score <= 15.0


def test_groq_adapter_evaluate_projects_success():
    """Verify GroqAdapter successfully parses structured JSON completions."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """{
                        "project_count": 3,
                        "ai_project_score": 36.5,
                        "project_titles": ["LangGraph Agent", "Hybrid RAG Engine", "Vision Bot"],
                        "strengths": ["Stateful multi-agent workflows", "Dense vector search with ChromaDB"],
                        "penalties": [],
                        "is_tutorial_or_shallow": false,
                        "architectural_summary": "Demonstrated exceptional multi-agent and RAG capabilities."
                    }"""
                }
            }
        ]
    }

    adapter = GroqAdapter(api_key="gsk_test_mock_key")
    with patch("httpx.Client.post", return_value=mock_response):
        result = adapter.evaluate_projects(
            candidate_name="Alice Candidate",
            projects_text="Projects text...",
            experience_text="Experience...",
            skills=["Python", "LangGraph"],
        )

        assert result.project_count == 3
        assert result.ai_project_score == 36.5
        assert result.is_tutorial_or_shallow is False
        assert "LangGraph Agent" in result.project_titles
        assert result.evaluation_source == "groq"


def test_groq_adapter_fallback_on_network_failure():
    """Verify GroqAdapter gracefully falls back to HeuristicAdapter on API failure."""
    adapter = GroqAdapter(api_key="gsk_test_mock_key")
    with patch("httpx.Client.post", side_effect=Exception("Connection refused")):
        result = adapter.evaluate_projects(
            candidate_name="Fallback Candidate",
            projects_text="1. LangGraph Multi-Agent: Built with ChromaDB and FastAPI.",
            experience_text="",
            skills=["Python", "FastAPI"],
        )

        # Fallback should succeed and return heuristic result without crashing
        assert result.evaluation_source == "heuristic"
        assert result.project_count >= 1
        assert result.ai_project_score > 0.0


def test_candidate_scorer_with_groq_project_eval():
    """Verify CandidateScorer seamlessly incorporates Groq ProjectEvaluationResult."""
    resume = ParsedResume(
        file_name="candidate.pdf",
        file_path="/tmp/candidate.pdf",
        candidate_name="Top Performer",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        projects_text="1. Production LangGraph Swarm.",
        experience_text="Backend Engineer at AI Startup.",
        full_text="Python FastAPI Docker PostgreSQL",
    )
    gh_metrics = GitHubMetrics(
        status="enriched",
        cohort="Active Builder",
        account_age_years=3.0,
        public_repos=15,
        recent_commits=45,
    )

    project_eval = ProjectEvaluationResult(
        project_count=3,
        ai_project_score=38.0,
        project_titles=["Production LangGraph Swarm"],
        strengths=["Stateful multi-agent system", "Evaluated RAG"],
        penalties=[],
        is_tutorial_or_shallow=False,
        architectural_summary="Deep production AI engineering with LangGraph.",
        evaluation_source="groq",
    )

    total, breakdown, strengths, concerns, penalties, summary = CandidateScorer.score_candidate(
        resume=resume,
        github_metrics=gh_metrics,
        github_score=8.0,
        project_eval=project_eval,
    )

    assert breakdown.ai_project_depth == 38.0
    assert "Stateful multi-agent system" in strengths
    assert "3 Verified Projects" in summary
    assert total > 70.0


def test_deep_ranking_engine_tie_breaking():
    """Verify that candidates with equal total score are ranked by AI Project Depth, then project count."""
    cand_a = CandidateResult(
        candidate_name="Alice Deep",
        file_name="alice.pdf",
        eligible=True,
        total_score=80.0,
        score_breakdown=ScoreBreakdown(
            ai_project_depth=38.0,
            python_backend=25.0,
            cloud_fullstack=10.0,
            github=5.0,
            engineering_depth=2.0,
        ),
        project_count=3,
        reason_50_to_100_words="Great candidate.",
    )

    cand_b = CandidateResult(
        candidate_name="Bob Shallow",
        file_name="bob.pdf",
        eligible=True,
        total_score=80.0,
        score_breakdown=ScoreBreakdown(
            ai_project_depth=30.0,
            python_backend=30.0,
            cloud_fullstack=12.0,
            github=5.0,
            engineering_depth=3.0,
        ),
        project_count=1,
        reason_50_to_100_words="Good candidate.",
    )

    candidates = [cand_b, cand_a]

    # Apply Deep Ranking Engine sort
    candidates.sort(
        key=lambda c: (
            round(c.total_score, 1),
            round(c.score_breakdown.ai_project_depth, 1),
            c.project_count,
            round(c.score_breakdown.python_backend, 1),
            round(c.score_breakdown.github, 1),
        ),
        reverse=True,
    )

    for idx, c in enumerate(candidates, start=1):
        c.rank = idx

    # Alice has higher ai_project_depth (38.0 vs 30.0) and more projects (3 vs 1), so she must rank #1
    assert candidates[0].candidate_name == "Alice Deep"
    assert candidates[0].rank == 1
    assert candidates[1].candidate_name == "Bob Shallow"
    assert candidates[1].rank == 2


def test_funnel_short_circuit_bypasses_llm_for_ineligible_candidates(tmp_path):
    """Verify that ineligible resumes (non-Python) short-circuit immediately with 0 LLM/Groq calls."""
    pipeline = ScreeningPipeline()
    pipeline.llm_adapter = MagicMock()

    # Create dummy non-python resume
    dummy_file = tmp_path / "frontend_only.txt"
    dummy_file.write_text("Frontend developer with React, HTML, CSS, JavaScript.", encoding="utf-8")

    result, is_failed = pipeline._process_single_resume(dummy_file, preferences=None)

    assert result.eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons
    # Neither LLM project evaluation nor LLM narrative generation should be called!
    pipeline.llm_adapter.evaluate_projects.assert_not_called()
    pipeline.llm_adapter.generate_narrative_reason.assert_not_called()


def test_funnel_evaluates_only_matched_python_candidate(tmp_path):
    """Verify that matched Python candidates proceed to Groq project intelligence."""
    pipeline = ScreeningPipeline()
    pipeline.llm_adapter = MagicMock()
    pipeline.llm_adapter.evaluate_projects.return_value = ProjectEvaluationResult(
        project_count=2,
        ai_project_score=35.0,
        project_titles=["RAG Pipeline"],
        strengths=["ChromaDB vector search"],
        evaluation_source="groq",
    )
    pipeline.llm_adapter.generate_narrative_reason.return_value = "Excellent candidate."

    # Create Python AI candidate
    dummy_file = tmp_path / "python_ai.txt"
    dummy_file.write_text("Python engineer with FastAPI, LangGraph, and ChromaDB.", encoding="utf-8")

    result, is_failed = pipeline._process_single_resume(dummy_file, preferences=None)

    assert result.eligible is True
    # Matched candidate SHOULD trigger Groq project evaluation!
    pipeline.llm_adapter.evaluate_projects.assert_called_once()
    assert result.score_breakdown.ai_project_depth == 35.0


def test_eligibility_custom_required_skills():
    """Verify HR can specify custom required skills (e.g. FastAPI)."""
    from src.filters.eligibility import EligibilityFilter
    from src.models import FilterPreferences

    resume_django_only = ParsedResume(
        file_name="django.pdf",
        file_path="dummy.pdf",
        candidate_name="Django Dev",
        full_text="Python developer with Django and LangGraph.",
        skills=["Python", "Django", "LangGraph"],
    )

    # HR specifically requires FastAPI
    prefs = FilterPreferences(required_skills=["python", "fastapi"])
    res = EligibilityFilter.evaluate(resume_django_only, prefs)

    assert res.eligible is False
    assert any("fastapi" in r.lower() for r in res.rejection_reasons)

