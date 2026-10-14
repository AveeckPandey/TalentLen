"""Hard rule-based eligibility filtering and dynamic filter criteria."""

import re
from typing import List, Tuple, Optional
from src.models import ParsedResume, EligibilityResult, FilterPreferences


# Python Stack Patterns
PYTHON_CORE_PATTERNS = [
    r'\bpython(?:3)?\b',
    r'\bfastapi\b',
    r'\bdjango\b',
    r'\bflask\b',
    r'\bpydantic\b',
    r'\bsqlalchemy\b',
    r'\bcelery\b',
    r'\bpytest\b',
    r'\basyncio\b',
]

# AI / Agentic / RAG Patterns
AI_AGENTIC_PATTERNS = [
    # Agentic Frameworks
    r'\blanggraph\b',
    r'\blangchain\b',
    r'\bllamaindex\b',
    r'\bllama_index\b',
    r'\bautogen\b',
    r'\bcrewai\b',
    r'\bhaystack\b',
    r'\badk\b',  # Google Agent Development Kit
    r'\bgoogle\s+adk\b',
    # Agent concepts
    r'\b(?:multi[- ]?)?agent(?:ic)?\b',
    r'\btool[- ]calling\b',
    r'\bfunction[- ]calling\b',
    r'\breact\s+framework\b',  # ReAct prompting / reasoning
    r'\bautonomous\s+agent\b',
    # RAG & Retrieval
    r'\brag\b',
    r'\bretrieval[- ]augmented\b',
    r'\bhybrid\s+search\b',
    r'\brerank(?:ing)?\b',
    r'\bvector\s+(?:search|database|store|index)\b',
    r'\bembeddings?\b',
    r'\bchromadb\b',
    r'\bfaiss\b',
    r'\bpinecone\b',
    r'\bqdrant\b',
    r'\bweaviate\b',
    # LLM & Evaluation
    r'\bllm(?:s)?\b',
    r'\blarge\s+language\s+models?\b',
    r'\bprompt\s+engineering\b',
    r'\bfine[- ]tun(?:ing|ed)\b',
    r'\b(?:lora|qlora|peft)\b',
    r'\bhugging\s*face\b',
    r'\btransformers\b',
    r'\bevaluation\s+pipeline\b',
    r'\bragas\b',
    r'\blangsmith\b',
    r'\btrulens\b',
    r'\bllm[- ]as[- ]a[- ]judge\b',
    r'\bgenai\b',
    r'\bgenerative\s+ai\b',
]


class EligibilityFilter:
    """Enforces strict rule-based screening and optional user criteria."""

    @classmethod
    def evaluate(
        cls,
        resume: ParsedResume,
        preferences: Optional[FilterPreferences] = None
    ) -> EligibilityResult:
        """
        Evaluate candidate eligibility against baseline hard requirements
        and optional dynamic preferences.
        """
        text = resume.full_text.lower()
        rejection_reasons: List[str] = []

        # 1. Python Evidence Check
        python_evidence = cls._find_evidence(text, PYTHON_CORE_PATTERNS)
        if not python_evidence:
            rejection_reasons.append("No evidence of Python stack")

        # 2. AI / Agentic Evidence Check
        ai_evidence = cls._find_evidence(text, AI_AGENTIC_PATTERNS)
        if not ai_evidence:
            rejection_reasons.append("No AI/agentic project evidence")

        # 3. Dynamic User Filters (if enabled)
        if preferences:
            # CGPA Dial Filter
            if preferences.min_cgpa is not None:
                if resume.cgpa is not None:
                    if resume.cgpa < preferences.min_cgpa:
                        rejection_reasons.append(
                            f"CGPA {resume.cgpa:.1f} below minimum threshold of {preferences.min_cgpa:.1f}"
                        )
                else:
                    # No stated CGPA: the threshold cannot be verified, so the
                    # candidate is excluded (otherwise CGPA-less resumes silently
                    # bypass the dial entirely).
                    rejection_reasons.append(
                        f"No stated CGPA (minimum threshold of {preferences.min_cgpa:.1f} required)"
                    )

            # Related Experience Filter
            if preferences.require_experience and not resume.has_related_experience:
                rejection_reasons.append("No verified industry/internship experience in related area")

            # GitHub Link Required Filter
            if preferences.require_github_link and not resume.github_url:
                rejection_reasons.append("No public GitHub profile link provided")

        is_eligible = len(rejection_reasons) == 0

        return EligibilityResult(
            candidate=resume.candidate_name,
            eligible=is_eligible,
            rejection_reasons=rejection_reasons,
            matched_skills=resume.skills,
            python_evidence=python_evidence,
            ai_evidence=ai_evidence,
        )

    @staticmethod
    def _find_evidence(text: str, patterns: List[str]) -> List[str]:
        """Collect matching regex patterns in text with matched substrings."""
        found = []
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                term = match.group(0).strip()
                if term and term not in found:
                    found.append(term)
        return found
