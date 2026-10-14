"""Tests for hard eligibility filtering and rejection rules."""

import pytest
from src.models import ParsedResume, FilterPreferences
from src.filters.eligibility import EligibilityFilter


def test_reject_javascript_react_only_profile():
    resume = ParsedResume(
        file_name="react_dev.pdf",
        file_path="dummy.pdf",
        candidate_name="React Dev",
        full_text="Experienced in React.js, Next.js, Node.js, Express, JavaScript, Tailwind CSS. Built MERN stack apps.",
        skills=["React", "Next.js", "JavaScript"]
    )
    result = EligibilityFilter.evaluate(resume)
    assert result.eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons
    assert "No AI/agentic project evidence" in result.rejection_reasons


def test_reject_java_spring_only_profile():
    resume = ParsedResume(
        file_name="java_dev.pdf",
        file_path="dummy.pdf",
        candidate_name="Java Dev",
        full_text="Java Developer with Spring Boot, Hibernate, MySQL, Maven, REST APIs.",
        skills=["Java", "Spring Boot"]
    )
    result = EligibilityFilter.evaluate(resume)
    assert result.eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons
    assert "No AI/agentic project evidence" in result.rejection_reasons


def test_reject_python_only_without_ai():
    resume = ParsedResume(
        file_name="python_script_dev.pdf",
        file_path="dummy.pdf",
        candidate_name="Python Script Dev",
        full_text="Python developer experienced in Django, Flask, PostgreSQL, writing automation scripts and data wrangling.",
        skills=["Python", "Django", "PostgreSQL"]
    )
    result = EligibilityFilter.evaluate(resume)
    assert result.eligible is False
    assert "No evidence of Python stack" not in result.rejection_reasons
    assert "No AI/agentic project evidence" in result.rejection_reasons


def test_accept_python_and_agentic_ai():
    resume = ParsedResume(
        file_name="ai_engineer.pdf",
        file_path="dummy.pdf",
        candidate_name="AI Engineer",
        full_text="Built multi-agent research assistant with LangGraph, LangChain, RAG with ChromaDB vector search and FastAPI.",
        skills=["Python", "LangGraph", "ChromaDB", "FastAPI"]
    )
    result = EligibilityFilter.evaluate(resume)
    assert result.eligible is True
    assert len(result.rejection_reasons) == 0


def test_accept_candidate_with_python_ai_and_react():
    # Should not reject merely because React/JS is also present
    resume = ParsedResume(
        file_name="fullstack_ai.pdf",
        file_path="dummy.pdf",
        candidate_name="Fullstack AI",
        full_text="Python, FastAPI, LangChain, Tool-calling agents, React.js frontend, Docker.",
        skills=["Python", "FastAPI", "LangChain", "React", "Docker"]
    )
    result = EligibilityFilter.evaluate(resume)
    assert result.eligible is True


def test_dynamic_cgpa_filter():
    resume = ParsedResume(
        file_name="ai_engineer.pdf",
        file_path="dummy.pdf",
        candidate_name="AI Engineer",
        cgpa=6.8,
        full_text="Python, LangChain, RAG, FastAPI.",
    )
    # Dial set to 7.5
    prefs = FilterPreferences(min_cgpa=7.5)
    result = EligibilityFilter.evaluate(resume, prefs)
    assert result.eligible is False
    assert any("CGPA" in r and "below minimum threshold" in r for r in result.rejection_reasons)


def test_cgpa_filter_excludes_missing_cgpa():
    # A resume with no stated CGPA must not silently bypass an active dial
    resume = ParsedResume(
        file_name="ai_engineer.pdf",
        file_path="dummy.pdf",
        candidate_name="AI Engineer",
        cgpa=None,
        full_text="Python, LangChain, RAG, FastAPI.",
    )
    prefs = FilterPreferences(min_cgpa=7.5)
    result = EligibilityFilter.evaluate(resume, prefs)
    assert result.eligible is False
    assert any("No stated CGPA" in r for r in result.rejection_reasons)


def test_missing_cgpa_passes_without_dial():
    # Without the dial, a missing CGPA must not disqualify on its own
    resume = ParsedResume(
        file_name="ai_engineer.pdf",
        file_path="dummy.pdf",
        candidate_name="AI Engineer",
        cgpa=None,
        full_text="Python, LangChain, RAG, FastAPI.",
    )
    result = EligibilityFilter.evaluate(resume, FilterPreferences())
    assert result.eligible is True
