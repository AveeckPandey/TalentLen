"""LLM Provider Adapter interface and implementations (Groq, OpenAI, Gemini, Anthropic, Heuristic Fallback)."""

import json
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import httpx

from src.config import settings
from src.models import ProjectEvaluationResult

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

    @abstractmethod
    def evaluate_projects(
        self,
        candidate_name: str,
        projects_text: str,
        experience_text: str,
        skills: List[str],
        full_text: str = "",
    ) -> ProjectEvaluationResult:
        """Analyze candidate projects for quantity, architectural depth, and authenticity."""
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

    def evaluate_projects(
        self,
        candidate_name: str,
        projects_text: str,
        experience_text: str,
        skills: List[str],
        full_text: str = "",
    ) -> ProjectEvaluationResult:
        """Analyze candidate projects using LLM completions with structured JSON output."""
        sys_prompt = (
            "You are a Principal AI Architect screening candidate resumes for an AI Engineering role.\n"
            "Analyze the candidate's actual projects, experience, and technical accomplishments to evaluate project quantity and AI architecture depth.\n\n"
            "SCORING RUBRIC (Max 40 points):\n"
            "- Stateful multi-agent orchestration, LangGraph, CrewAI, AutoGen, tool calling (up to 15 pts)\n"
            "- Production RAG, hybrid search, rerankers, vector databases (ChromaDB, FAISS, Pinecone, Qdrant) (up to 12 pts)\n"
            "- AI evaluation pipelines (Ragas, TruLens, LangSmith), fine-tuning, streaming SSE (up to 8 pts)\n"
            "- Production architecture, caching, guardrails, error recovery (up to 5 pts)\n"
            "- PENALTIES:\n"
            "  * Deduct 10-12 pts if projects are thin LLM wrappers without retrieval or agentic state.\n"
            "  * Deduct 8-10 pts for generic tutorial clones (Iris, Titanic, Chat-with-PDF boilerplate, basic todo app).\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "project_count": <int, total distinct projects found>,\n'
            '  "ai_project_score": <float, between 0.0 and 40.0>,\n'
            '  "project_titles": [<string>, ...],\n'
            '  "strengths": [<string>, ...],\n'
            '  "penalties": [<string>, ...],\n'
            '  "is_tutorial_or_shallow": <boolean>,\n'
            '  "architectural_summary": "<string, 1-2 concise sentences summarizing technical depth>"\n'
            "}"
        )

        user_prompt = (
            f"Candidate Name: {candidate_name}\n"
            f"Skills: {', '.join(skills[:20]) if skills else 'Not specified'}\n\n"
            f"PROJECTS SECTION:\n"
            f"{projects_text[:2500] if projects_text.strip() else 'No separate projects section found.'}\n\n"
            f"WORK / RELEVANT EXPERIENCE:\n"
            f"{experience_text[:1500] if experience_text.strip() else 'None listed.'}"
        )

        source = "groq" if ("groq" in self.base_url.lower() or "groq" in self.model.lower()) else "openai"

        for attempt in range(2):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                            "max_tokens": 500,
                        },
                    )
                    if resp.status_code == 200:
                        raw_content = resp.json()["choices"][0]["message"]["content"].strip()
                        # Strip any markdown code fences if present
                        if raw_content.startswith("```"):
                            lines = raw_content.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            raw_content = "\n".join(lines).strip()

                        data = json.loads(raw_content)

                        # Extract with tolerant key aliasing
                        p_count = data.get("project_count")
                        if p_count is None:
                            p_count = data.get("genuine_project_count", 0)
                        try:
                            p_count = max(0, int(p_count))
                        except (ValueError, TypeError):
                            p_count = 0

                        p_score = data.get("ai_project_score")
                        if p_score is None:
                            p_score = data.get("ai_project_depth_score")
                        if p_score is None:
                            p_score = data.get("ai_score") or data.get("score") or 0.0
                        try:
                            p_score = round(min(40.0, max(0.0, float(p_score))), 1)
                        except (ValueError, TypeError):
                            p_score = 0.0

                        p_titles = data.get("project_titles") or data.get("titles") or []
                        if isinstance(p_titles, str):
                            p_titles = [p_titles]

                        strengths = data.get("strengths") or data.get("architectural_strengths") or []
                        if isinstance(strengths, str):
                            strengths = [strengths]

                        penalties = data.get("penalties") or data.get("penalties_red_flags") or []
                        if isinstance(penalties, str):
                            penalties = [penalties]

                        is_shallow = bool(data.get("is_tutorial_or_shallow") or data.get("mostly_shallow_tutorial_copies") or False)
                        arch_summary = data.get("architectural_summary") or data.get("summary") or ""

                        return ProjectEvaluationResult(
                            project_count=p_count,
                            ai_project_score=p_score,
                            project_titles=[str(t).strip() for t in p_titles if str(t).strip()],
                            strengths=[str(s).strip() for s in strengths if str(s).strip()],
                            penalties=[str(p).strip() for p in penalties if str(p).strip()],
                            is_tutorial_or_shallow=is_shallow,
                            architectural_summary=str(arch_summary).strip(),
                            evaluation_source=source,
                        )
                    elif resp.status_code == 429 and attempt == 0:
                        import time
                        time.sleep(1.5)
                        continue
                    else:
                        logger.warning(f"{source.upper()} API non-200 ({resp.status_code}): {resp.text[:250]}")
                        break
            except Exception as e:
                if attempt == 0:
                    import time
                    time.sleep(1.0)
                    continue
                logger.warning(f"{source.upper()} API project evaluation call failed, falling back to heuristic: {e}")
                break

        return HeuristicAdapter().evaluate_projects(
            candidate_name, projects_text, experience_text, skills, full_text
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

    def evaluate_projects(
        self,
        candidate_name: str,
        projects_text: str,
        experience_text: str,
        skills: List[str],
        full_text: str = "",
    ) -> ProjectEvaluationResult:
        """Analyze candidate projects using Google Gemini with structured JSON output."""
        sys_prompt = (
            "You are a Principal AI Architect screening candidate resumes for an AI Engineering role.\n"
            "Analyze the candidate's actual projects, experience, and technical accomplishments to evaluate project quantity and AI architecture depth.\n\n"
            "SCORING RUBRIC (Max 40 points):\n"
            "- Stateful multi-agent orchestration, LangGraph, CrewAI, AutoGen, tool calling (up to 15 pts)\n"
            "- Production RAG, hybrid search, rerankers, vector databases (ChromaDB, FAISS, Pinecone, Qdrant) (up to 12 pts)\n"
            "- AI evaluation pipelines (Ragas, TruLens, LangSmith), fine-tuning, streaming SSE (up to 8 pts)\n"
            "- Production architecture, caching, guardrails, error recovery (up to 5 pts)\n"
            "- PENALTIES:\n"
            "  * Deduct 10-12 pts if projects are thin LLM wrappers without retrieval or agentic state.\n"
            "  * Deduct 8-10 pts for generic tutorial clones (Iris, Titanic, Chat-with-PDF boilerplate, basic todo app).\n\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "project_count": <int, total distinct projects found>,\n'
            '  "ai_project_score": <float, between 0.0 and 40.0>,\n'
            '  "project_titles": [<string>, ...],\n'
            '  "strengths": [<string>, ...],\n'
            '  "penalties": [<string>, ...],\n'
            '  "is_tutorial_or_shallow": <boolean>,\n'
            '  "architectural_summary": "<string, 1-2 concise sentences summarizing technical depth>"\n'
            "}"
        )

        user_prompt = (
            f"Candidate Name: {candidate_name}\n"
            f"Skills: {', '.join(skills[:20]) if skills else 'Not specified'}\n\n"
            f"PROJECTS SECTION:\n"
            f"{projects_text[:2500] if projects_text.strip() else 'No separate projects section found.'}\n\n"
            f"WORK / RELEVANT EXPERIENCE:\n"
            f"{experience_text[:1500] if experience_text.strip() else 'None listed.'}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    url,
                    json={
                        "system_instruction": {"parts": [{"text": sys_prompt}]},
                        "contents": [{"parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.1,
                        },
                    },
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    raw_content = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    data = json.loads(raw_content)

                    p_count = data.get("project_count", 0)
                    try:
                        p_count = max(0, int(p_count))
                    except (ValueError, TypeError):
                        p_count = 0

                    p_score = data.get("ai_project_score") or data.get("score") or 0.0
                    try:
                        p_score = round(min(40.0, max(0.0, float(p_score))), 1)
                    except (ValueError, TypeError):
                        p_score = 0.0

                    p_titles = data.get("project_titles") or []
                    strengths = data.get("strengths") or []
                    penalties = data.get("penalties") or []
                    is_shallow = bool(data.get("is_tutorial_or_shallow", False))
                    arch_summary = data.get("architectural_summary") or ""

                    return ProjectEvaluationResult(
                        project_count=p_count,
                        ai_project_score=p_score,
                        project_titles=[str(t).strip() for t in p_titles if str(t).strip()],
                        strengths=[str(s).strip() for s in strengths if str(s).strip()],
                        penalties=[str(p).strip() for p in penalties if str(p).strip()],
                        is_tutorial_or_shallow=is_shallow,
                        architectural_summary=arch_summary,
                        evaluation_source="gemini",
                    )
        except Exception as e:
            logger.warning(f"Gemini evaluate_projects call failed, falling back to heuristic: {e}")

        return HeuristicAdapter().evaluate_projects(
            candidate_name, projects_text, experience_text, skills, full_text
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

    def evaluate_projects(
        self,
        candidate_name: str,
        projects_text: str,
        experience_text: str,
        skills: List[str],
        full_text: str = "",
    ) -> ProjectEvaluationResult:
        return HeuristicAdapter().evaluate_projects(
            candidate_name, projects_text, experience_text, skills, full_text
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

    def evaluate_projects(
        self,
        candidate_name: str,
        projects_text: str,
        experience_text: str,
        skills: List[str],
        full_text: str = "",
    ) -> ProjectEvaluationResult:
        """Deterministic heuristic project evaluator counting projects and assessing AI depth."""
        import re

        combined = f"{projects_text}\n{experience_text}\n{full_text}".lower()
        strengths: List[str] = []
        penalties: List[str] = []
        titles: List[str] = []

        # 1. Project Quantity Detection
        if projects_text.strip():
            matches = re.findall(
                r"(?:^|\n)\s*(?:(?:\d+[\.\)]|\#\#\#|\*|\-)\s*([A-Za-z0-9\s\-_]{3,45})|\bproject:\s*([A-Za-z0-9\s\-_]{3,45}))",
                projects_text,
                re.IGNORECASE,
            )
            for m in matches:
                title = (m[0] or m[1]).strip()
                if title and len(title) > 3 and not title.lower().startswith(("http", "github", "demo")):
                    titles.append(title)

            if not titles:
                blocks = [b.strip() for b in projects_text.split("\n\n") if len(b.strip()) > 30]
                project_count = max(1, len(blocks))
            else:
                project_count = max(1, len(titles))
        elif experience_text.strip():
            project_count = 1
        else:
            project_count = 0

        # 2. Rubric-based AI Project Depth scoring (0-40)
        ai_score = 0.0

        if any(k in combined for k in ["langgraph", "multi-agent", "multi agent", "autogen", "crewai"]):
            ai_score += 15.0
            strengths.append("Stateful multi-agent orchestration (LangGraph/CrewAI/AutoGen)")
        elif any(k in combined for k in ["langchain", "tool-calling", "tool calling", "function calling", "adk"]):
            ai_score += 11.0
            strengths.append("Agentic workflow with tool/function calling")
        elif any(k in combined for k in ["agent", "agents"]):
            ai_score += 7.0
            strengths.append("Basic agent implementation")

        if any(k in combined for k in ["hybrid search", "rerank", "reranker", "advanced rag"]):
            ai_score += 12.0
            strengths.append("Advanced RAG with hybrid search and reranking")
        elif any(k in combined for k in ["chromadb", "faiss", "pinecone", "qdrant", "weaviate"]):
            ai_score += 9.0
            strengths.append("Vector database retrieval (ChromaDB/FAISS/Pinecone/Qdrant)")
        elif any(k in combined for k in ["rag", "embeddings", "vector search", "llamaindex"]):
            ai_score += 7.0
            strengths.append("Embeddings-based retrieval system")

        if any(k in combined for k in ["ragas", "trulens", "langsmith", "llm-as-a-judge", "evaluation"]):
            ai_score += 8.0
            strengths.append("AI evaluation pipeline (Ragas/LangSmith/TruLens)")
        elif any(k in combined for k in ["fine-tuning", "lora", "transformers", "prompt engineering"]):
            ai_score += 4.0

        if any(k in combined for k in ["streaming", "sse", "memory", "state", "guardrails"]):
            ai_score += 5.0

        ai_score = min(40.0, ai_score)

        is_shallow = False
        if any(k in combined for k in ["openai", "gemini", "chatgpt"]) and not any(
            k in combined for k in ["rag", "vector", "langgraph", "tool", "agent", "chromadb", "faiss", "pinecone", "retrieval"]
        ):
            penalty = 12.0
            ai_score = max(5.0, ai_score - penalty)
            penalties.append(f"Deducted {penalty:.0f} pts: Thin LLM wrapper without retrieval/state/agentic logic")
            is_shallow = True

        if any(t in combined for t in ["titanic", "chat with pdf", "todo app", "iris dataset"]):
            if "evaluation" not in combined and "production" not in combined:
                penalty = 8.0
                ai_score = max(0.0, ai_score - penalty)
                penalties.append(f"Deducted {penalty:.0f} pts: Tutorial-style project without production ownership")
                is_shallow = True

        ai_score = round(ai_score, 1)

        # Extract candidate's specific technologies mentioned
        detected_techs = []
        tech_keywords = [
            ("LangGraph", ["langgraph"]),
            ("CrewAI", ["crewai"]),
            ("AutoGen", ["autogen"]),
            ("LangChain", ["langchain"]),
            ("LlamaIndex", ["llamaindex"]),
            ("Pinecone", ["pinecone"]),
            ("ChromaDB", ["chromadb"]),
            ("FAISS", ["faiss"]),
            ("Qdrant", ["qdrant"]),
            ("Weaviate", ["weaviate"]),
            ("Redis", ["redis"]),
            ("FastAPI", ["fastapi"]),
            ("Django", ["django"]),
            ("PostgreSQL", ["postgresql", "postgres"]),
            ("Docker", ["docker"]),
            ("Kafka", ["kafka"]),
            ("Celery", ["celery"]),
            ("Azure OpenAI", ["azure openai"]),
            ("Gemini", ["gemini"]),
            ("OpenAI", ["openai"]),
            ("Ragas", ["ragas"]),
            ("LangSmith", ["langsmith"]),
            ("TruLens", ["trulens"]),
        ]
        for display_name, aliases in tech_keywords:
            if any(a in combined for a in aliases):
                detected_techs.append(display_name)

        # Deterministic seed from candidate name
        seed = int(hashlib.md5(candidate_name.encode()).hexdigest(), 16)

        # Build candidate-specific project anchor
        if titles:
            primary_project = f"'{titles[0]}'"
        elif project_count > 1:
            primary_project = f"{project_count} engineering projects"
        elif project_count == 1:
            primary_project = "a core AI application"
        else:
            primary_project = "technical engineering workflows"

        if detected_techs:
            rot_t = seed % len(detected_techs)
            chosen_techs = (detected_techs[rot_t:] + detected_techs[:rot_t])[:3]
            tech_str = ", ".join(chosen_techs)
        else:
            tech_str = "Python services and modern AI tools"

        if strengths:
            rot_s = seed % len(strengths)
            chosen_strengths = (strengths[rot_s:] + strengths[:rot_s])
            s1 = chosen_strengths[0]
            s2 = chosen_strengths[1] if len(chosen_strengths) > 1 else None
        else:
            s1 = "Python backend services"
            s2 = None

        template_variant = seed % 4
        if template_variant == 0:
            arch_summary = (
                f"Built {primary_project} focusing on {s1.lower()}"
                f"{f' alongside {s2.lower()}' if s2 and s2 != s1 else ''}, leveraging {tech_str}."
            )
        elif template_variant == 1:
            arch_summary = (
                f"Engineered {primary_project} utilizing {tech_str} "
                f"to power {s1.lower()}."
            )
        elif template_variant == 2:
            arch_summary = (
                f"Delivered {primary_project} demonstrating {s1.lower()} "
                f"with robust integration of {tech_str}."
            )
        else:
            arch_summary = (
                f"Demonstrates hands-on implementation in {primary_project} "
                f"combining {tech_str}{f' and {s1.lower()}' if s1 else ''}."
            )

        return ProjectEvaluationResult(
            project_count=project_count,
            ai_project_score=ai_score,
            project_titles=titles[:5],
            strengths=strengths,
            penalties=penalties,
            is_tutorial_or_shallow=is_shallow,
            architectural_summary=arch_summary,
            evaluation_source="heuristic",
        )

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
