"""LLM Provider Adapter interface and implementations (Groq, OpenAI, Gemini, Anthropic, Heuristic Fallback)."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """Abstract adapter interface for LLM-assisted evaluation and narrative reasoning."""

    @abstractmethod
    def generate_narrative_reason(
        self,
        candidate_name: str,
        eligible: bool,
        total_score: float,
        breakdown_dict: Dict[str, float],
        strengths: List[str],
        concerns: List[str],
        rejection_reasons: List[str],
        matched_skills: List[str],
        github_summary: str,
    ) -> str:
        """Generate an explainable 50 to 100 word evaluation justification."""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API adapter using standard HTTP completions endpoint."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate_narrative_reason(
        self,
        candidate_name: str,
        eligible: bool,
        total_score: float,
        breakdown_dict: Dict[str, float],
        strengths: List[str],
        concerns: List[str],
        rejection_reasons: List[str],
        matched_skills: List[str],
        github_summary: str,
    ) -> str:
        # Build differentiated, candidate-specific prompt.
        # Include full breakdown numbers + top skills so Qwen can't reuse a generic template.
        top_strengths = "; ".join(strengths[:4]) if strengths else "None listed"
        top_concerns = "; ".join(concerns[:2]) if concerns else "None major"
        top_skills = ", ".join(matched_skills[:8]) if matched_skills else "generalist"
        breakdown_str = ", ".join(f"{k}={v}" for k, v in breakdown_dict.items()) if breakdown_dict else "none (rejected)"

        if eligible:
            task = (
                f"Write a DISTINCT 60-90 word hiring justification for '{candidate_name}' "
                f"(score {total_score:.1f}/100, {breakdown_str}). "
                f"Start with a varied opening — do NOT start with '{candidate_name} qualifies as'. "
                f"Mention 2-3 most distinctive strengths from [{top_strengths}], "
                f"cite concrete stack [{top_skills}], "
                f"reference GitHub [{github_summary}], "
                f"and close with the one real gap [{top_concerns}] + internship fit. "
                f"No bullet points, no generic filler, 60-90 words only."
            )
        else:
            task = (
                f"Write a DISTINCT 60-90 word rejection explanation for '{candidate_name}'. "
                f"Reasons: {rejection_reasons}. Skills seen: [{top_skills}]. "
                f"Start with a varied opening — do NOT use template phrasing. "
                f"State exactly which mandatory bar failed (Python backend? agentic/RAG evidence?), "
                f"acknowledge one positive, then state the bar to clear. 60-90 words only."
            )

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a senior tech lead screening SDE AI interns. Every evaluation must sound written for THAT candidate only — specific evidence, varied openings, zero copy-paste phrasing. Strictly 60-90 words."},
                            {"role": "user", "content": task}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 260,
                    }
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    # Verify length
                    words = text.split()
                    if 40 <= len(words) <= 120:
                        # Guard: LLM sometimes echoes the banned template — force fallback to diversified heuristic instead
                        if "qualifies as an eligible candidate" in text:
                            logger.warning("LLM returned templated phrasing, using diversified heuristic instead")
                        else:
                            return text
                else:
                    logger.warning(f"LLM API non-200 ({resp.status_code}): {resp.text[:300]}")
        except Exception as e:
            logger.warning(f"OpenAI API call failed, falling back to heuristic engine: {e}")

        # Fallback if call fails
        return HeuristicAdapter().generate_narrative_reason(
            candidate_name, eligible, total_score, breakdown_dict, strengths,
            concerns, rejection_reasons, matched_skills, github_summary
        )


class GroqAdapter(OpenAIAdapter):
    """Groq API adapter (OpenAI-compatible /chat/completions). Supports Qwen, Llama, etc."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b", base_url: str = "https://api.groq.com/openai/v1"):
        super().__init__(api_key=api_key, model=model, base_url=base_url)


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini API adapter via HTTP."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate_narrative_reason(
        self,
        candidate_name: str,
        eligible: bool,
        total_score: float,
        breakdown_dict: Dict[str, float],
        strengths: List[str],
        concerns: List[str],
        rejection_reasons: List[str],
        matched_skills: List[str],
        github_summary: str,
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        top_strengths = "; ".join(strengths[:4]) if strengths else "None listed"
        top_skills = ", ".join(matched_skills[:8]) if matched_skills else "generalist"
        breakdown_str = ", ".join(f"{k}={v}" for k, v in breakdown_dict.items()) if breakdown_dict else "none (rejected)"
        if eligible:
            prompt = (
                f"Senior tech lead: write a DISTINCT 60-90 word hiring justification for '{candidate_name}' "
                f"(score {total_score:.1f}/100, {breakdown_str}). Vary the opening, never reuse template phrasing. "
                f"Highlight distinctive strengths [{top_strengths}], stack [{top_skills}], GitHub [{github_summary}], "
                f"and the one gap [{concerns[0] if concerns else 'minor polish needed'}]. 60-90 words only."
            )
        else:
            prompt = (
                f"Senior tech lead: write a DISTINCT 60-90 word rejection for '{candidate_name}'. "
                f"Failed: {rejection_reasons}. Skills: [{top_skills}]. Vary opening, name the exact missing bar, "
                f"note one positive, state bar to clear. 60-90 words only."
            )

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    words = text.split()
                    if 40 <= len(words) <= 120:
                        return text
        except Exception as e:
            logger.warning(f"Gemini API call failed, falling back to heuristic engine: {e}")

        return HeuristicAdapter().generate_narrative_reason(
            candidate_name, eligible, total_score, breakdown_dict, strengths,
            concerns, rejection_reasons, matched_skills, github_summary
        )


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Messages API adapter (Claude models)."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest", base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate_narrative_reason(
        self,
        candidate_name: str,
        eligible: bool,
        total_score: float,
        breakdown_dict: Dict[str, float],
        strengths: List[str],
        concerns: List[str],
        rejection_reasons: List[str],
        matched_skills: List[str],
        github_summary: str,
    ) -> str:
        top_strengths = "; ".join(strengths[:4]) if strengths else "None listed"
        top_skills = ", ".join(matched_skills[:8]) if matched_skills else "generalist"
        breakdown_str = ", ".join(f"{k}={v}" for k, v in breakdown_dict.items()) if breakdown_dict else "none (rejected)"
        if eligible:
            prompt = (
                f"Write a DISTINCT 60-90 word hiring justification for '{candidate_name}' "
                f"(score {total_score:.1f}/100, {breakdown_str}). Vary the opening, never reuse template phrasing. "
                f"Highlight distinctive strengths [{top_strengths}], stack [{top_skills}], GitHub [{github_summary}], "
                f"and the one gap [{concerns[0] if concerns else 'minor polish needed'}]. 60-90 words only."
            )
        else:
            prompt = (
                f"Write a DISTINCT 60-90 word rejection for '{candidate_name}'. "
                f"Failed: {rejection_reasons}. Skills: [{top_skills}]. Vary opening, name the exact missing bar, "
                f"note one positive, state bar to clear. 60-90 words only."
            )
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    blocks = data.get("content", [])
                    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
                    if text and 40 <= len(text.split()) <= 120 and "qualifies as an eligible candidate" not in text:
                        return text
        except Exception as e:
            logger.warning(f"Anthropic API call failed, falling back to heuristic engine: {e}")

        return HeuristicAdapter().generate_narrative_reason(
            candidate_name, eligible, total_score, breakdown_dict, strengths,
            concerns, rejection_reasons, matched_skills, github_summary
        )


class HeuristicAdapter(BaseLLMAdapter):
    """
    Deterministic rule-based reasoning engine ensuring guaranteed 50-100 word
    explanations with zero external API dependencies or network latency.
    Uses rotated templates + candidate-specific signals so back-to-back
    candidates never read identically.
    """

    def generate_narrative_reason(
        self,
        candidate_name: str,
        eligible: bool,
        total_score: float,
        breakdown_dict: Dict[str, float],
        strengths: List[str],
        concerns: List[str],
        rejection_reasons: List[str],
        matched_skills: List[str],
        github_summary: str,
    ) -> str:
        import hashlib
        seed = int(hashlib.md5(f"{candidate_name}|{total_score}|{len(strengths)}".encode()).hexdigest(), 16)

        if not eligible:
            reasons_text = ", ".join(rejection_reasons) if rejection_reasons else "missing mandatory Python/AI bar"
            skills_text = ", ".join(matched_skills[:5]) if matched_skills else "general software development"
            variant = seed % 3
            if variant == 0:
                full = (
                    f"{candidate_name} was marked ineligible at {total_score:.1f}/100 due to {reasons_text.lower()}. "
                    f"Background shows {skills_text}, but the resume lacks concrete Python backend work "
                    f"and verifiable agentic, RAG, or LLM-tooling evidence. "
                    f"For this SDE AI internship the bar is shipped Python services plus agent orchestration, tool calling, "
                    f"or vector retrieval. This profile does not clear that baseline, though relevant Python building would change the outcome."
                )
            elif variant == 1:
                full = (
                    f"Screening result: {candidate_name} ineligible ({total_score:.1f}/100) — {reasons_text.lower()}. "
                    f"Seen skills ({skills_text}) skew away from the required Python and AI/agentic core, "
                    f"with no convincing FastAPI/Django service or RAG/agent project to score. "
                    f"The internship requires demonstrable Python backend depth alongside LLM workflows, embeddings search, or multi-agent logic. "
                    f"Add a deployed Python + RAG/agent build to become competitive."
                )
            else:
                full = (
                    f"{candidate_name} does not advance (ineligible, {total_score:.1f}/100). Core gap: {reasons_text.lower()}. "
                    f"While {skills_text} shows engineering interest, there is insufficient Python evidence and no production-grade "
                    f"agentic or retrieval pipeline. Successful candidates typically show async Python APIs wired to vector search, "
                    f"guardrailed agents, or evaluated RAG. Without that Python plus AI linkage, the profile falls below the hiring threshold."
                )
            return self._ensure_word_count(full, 55, 95)

        # Eligible: build candidate-specific signals
        ai_pts = breakdown_dict.get("ai_project_depth", 0) if breakdown_dict else 0
        py_pts = breakdown_dict.get("python_backend", 0) if breakdown_dict else 0
        cloud_pts = breakdown_dict.get("cloud_fullstack", 0) if breakdown_dict else 0
        gh_pts = breakdown_dict.get("github", 0) if breakdown_dict else 0
        # Rotate strength order deterministically so same-strength candidates still differ
        rot = seed % max(1, len(strengths)) if strengths else 0
        ordered = (strengths[rot:] + strengths[:rot]) if strengths else []
        s1 = ordered[0] if len(ordered) > 0 else "Python backend development"
        s2 = ordered[1] if len(ordered) > 1 else None
        s3 = ordered[2] if len(ordered) > 2 else None
        # Vary skill slice length 4-6 by seed
        skill_n = 4 + (seed % 3)
        skills_str = ", ".join(matched_skills[:skill_n]) if matched_skills else "Python, backend tooling"
        c_text = concerns[seed % len(concerns)] if concerns else "polishing production hardening"
        variant = seed % 3

        if variant == 0:
            extra = f" Backed by {s3.lower()}." if s3 else ""
            full = (
                f"{candidate_name} scored {total_score:.1f}/100 (AI {ai_pts}/40, Python {py_pts}/30, Cloud {cloud_pts}/15, GitHub {gh_pts}/10), "
                f"led by {s1.lower()}"
                f"{f' and {s2.lower()}' if s2 else ''}{extra} "
                f"Stack centers on {skills_str}. GitHub: {github_summary} "
                f"Watch-item: {c_text.lower()}. Fit for SDE AI internship is strong on shipped agentic depth."
            )
        elif variant == 1:
            extra = f" Plus {s3.lower()} rounds out the build." if s3 else ""
            full = (
                f"At {total_score:.1f}/100, {candidate_name} stands out through {s1.lower()}"
                f"{f', complemented by {s2.lower()}' if s2 else ''}.{extra} "
                f"Core evidence in {skills_str} maps to AI {ai_pts} and Python {py_pts} bands. "
                f"GitHub profile: {github_summary} "
                f"Growth edge to probe in interview: {c_text.lower()}."
            )
        else:
            extra = f" Also notable: {s3.lower()}." if s3 else ""
            full = (
                f"{candidate_name} ({total_score:.1f}/100) impressed with {s1.lower()}"
                f"{f' alongside {s2.lower()}' if s2 else ''}.{extra} "
                f"Depth spans {skills_str} (cloud {cloud_pts}/15, GitHub {gh_pts}/10). "
                f"Activity: {github_summary} "
                f"Interview focus should be {c_text.lower()}, but overall internship readiness is high."
            )
        return self._ensure_word_count(full, 55, 95)

    @staticmethod
    def _ensure_word_count(text: str, min_words: int, max_words: int) -> str:
        """Trim or pad text gracefully to remain between min_words and max_words."""
        words = text.split()
        if len(words) > max_words:
            # Cut at last period before max_words
            truncated = " ".join(words[:max_words])
            last_dot = truncated.rfind(".")
            if last_dot > 200:
                return truncated[:last_dot + 1]
            return truncated + "."
        elif len(words) < min_words:
            padding = " Demonstrates clear relevance to the engineering requirements."
            text += padding
        return text


def get_llm_adapter() -> BaseLLMAdapter:
    """Factory to retrieve configured LLM adapter with automatic fallback."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        if settings.GROQ_API_KEY:
            return GroqAdapter(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                base_url=settings.GROQ_BASE_URL,
            )
        return HeuristicAdapter()

    if provider == "openai" or (provider == "auto" and settings.OPENAI_API_KEY):
        if settings.OPENAI_API_KEY:
            return OpenAIAdapter(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                base_url=settings.OPENAI_BASE_URL,
            )

    if provider == "gemini" or (provider == "auto" and settings.GEMINI_API_KEY):
        if settings.GEMINI_API_KEY:
            return GeminiAdapter(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
            )

    if provider == "anthropic" or (provider == "auto" and settings.ANTHROPIC_API_KEY):
        if settings.ANTHROPIC_API_KEY:
            return AnthropicAdapter(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL,
                base_url=settings.ANTHROPIC_BASE_URL,
            )

    if provider == "auto" and settings.GROQ_API_KEY:
        return GroqAdapter(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            base_url=settings.GROQ_BASE_URL,
        )

    return HeuristicAdapter()
