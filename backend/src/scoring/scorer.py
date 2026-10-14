"""100-Point Candidate Scoring Engine with explainable evidence and quality penalties."""

import re
from typing import Tuple, List, Dict, Any
from src.models import ParsedResume, ScoreBreakdown, GitHubMetrics
from src.config import settings


class CandidateScorer:
    """Calculates explainable candidate scores across 5 categories with penalty detection."""

    @classmethod
    def score_candidate(
        cls,
        resume: ParsedResume,
        github_metrics: GitHubMetrics,
        github_score: float,
    ) -> Tuple[float, ScoreBreakdown, List[str], List[str], List[str], str]:
        """
        Compute total score and breakdown.
        Returns:
            (total_score, breakdown, strengths, concerns, penalties_applied, project_summary)
        """
        full_text = resume.full_text.lower()
        projects = resume.projects_text.lower()
        experience = resume.experience_text.lower()
        skills = " ".join(resume.skills).lower()

        # Combine projects, experience, and full text for comprehensive evidence analysis
        project_context = f"{projects}\n{experience}\n{full_text}"

        strengths: List[str] = []
        concerns: List[str] = []
        penalties_applied: List[str] = []

        # -------------------------------------------------------------
        # 1. AI / Agentic / RAG Project Depth (Max 40 points)
        # -------------------------------------------------------------
        ai_score = 0.0

        # Multi-agent / State / Orchestration (up to 15 pts)
        if any(k in project_context for k in ["langgraph", "multi-agent", "multi agent", "autogen", "crewai"]):
            ai_score += 15.0
            strengths.append("Stateful multi-agent orchestration (LangGraph/CrewAI/AutoGen)")
        elif any(k in project_context for k in ["langchain", "tool-calling", "tool calling", "function calling", "adk"]):
            ai_score += 11.0
            strengths.append("Agentic workflow with tool/function calling")
        elif any(k in project_context for k in ["agent", "agents"]):
            ai_score += 7.0
            strengths.append("Basic agent implementation")

        # RAG / Vector Retrieval / Embeddings (up to 12 pts)
        if any(k in project_context for k in ["hybrid search", "rerank", "reranker", "advanced rag"]):
            ai_score += 12.0
            strengths.append("Advanced RAG with hybrid search and reranking")
        elif any(k in project_context for k in ["chromadb", "faiss", "pinecone", "qdrant", "weaviate"]):
            ai_score += 9.0
            strengths.append("Vector database retrieval (ChromaDB/FAISS/Pinecone/Qdrant)")
        elif any(k in project_context for k in ["rag", "embeddings", "vector search", "llamaindex"]):
            ai_score += 7.0
            strengths.append("Embeddings-based retrieval system")

        # Evaluation & Advanced Production Signals (up to 8 pts)
        if any(k in project_context for k in ["ragas", "trulens", "langsmith", "llm-as-a-judge", "evaluation"]):
            ai_score += 8.0
            strengths.append("AI evaluation pipeline (Ragas/LangSmith/TruLens)")
        elif any(k in project_context for k in ["fine-tuning", "lora", "transformers", "prompt engineering"]):
            ai_score += 4.0

        # Practical Integration / Business Logic (up to 5 pts)
        if any(k in project_context for k in ["streaming", "sse", "memory", "state", "guardrails"]):
            ai_score += 5.0

        # Cap base AI score at 40
        ai_score = min(40.0, ai_score)

        # PENALTIES FOR SHALLOW WRAPPERS & TUTORIALS
        # Thin wrapper check: Mentioned OpenAI/Gemini/API call, but zero retrieval, zero state, zero tools
        is_thin_wrapper = False
        if any(k in project_context for k in ["openai", "gemini", "chatgpt"]) and not any(
            k in project_context for k in ["rag", "vector", "langgraph", "tool", "agent", "chromadb", "faiss", "pinecone", "retrieval"]
        ):
            is_thin_wrapper = True
            penalty = 12.0
            ai_score = max(5.0, ai_score - penalty)
            penalties_applied.append(f"Deducted {penalty:.0f} pts: Thin LLM wrapper without retrieval/state/agentic logic")
            concerns.append("AI project appears to be a thin API wrapper without state or retrieval")

        # Tutorial project penalty
        if any(t in project_context for t in ["titanic", "chat with pdf", "todo app", "iris dataset"]):
            if "evaluation" not in project_context and "production" not in project_context:
                penalty = 8.0
                ai_score = max(0.0, ai_score - penalty)
                penalties_applied.append(f"Deducted {penalty:.0f} pts: Tutorial-style project without production ownership")
                concerns.append("Contains tutorial-style projects without evidence of deeper ownership")

        # -------------------------------------------------------------
        # 2. Python & Backend Engineering (Max 30 points)
        # -------------------------------------------------------------
        py_score = 0.0

        # FastAPI & Async (up to 10 pts)
        if "fastapi" in project_context and ("async" in project_context or "asyncio" in project_context):
            py_score += 10.0
            strengths.append("Async FastAPI backend architecture")
        elif "fastapi" in project_context or "django" in project_context or "flask" in project_context:
            py_score += 8.0
            strengths.append("Modern Python backend framework (FastAPI/Django)")
        elif "python" in project_context:
            py_score += 5.0
        elif "python" in skills:
            # Keyword-only in skills list
            py_score += 3.0
            concerns.append("Python listed in skills but lacks detailed project/work elaboration")

        # PostgreSQL / Relational DB / ORM (up to 8 pts)
        if any(k in project_context for k in ["postgresql", "postgres", "sqlalchemy", "alembic"]):
            py_score += 8.0
            strengths.append("PostgreSQL with ORM / schema migrations")
        elif any(k in project_context for k in ["sql", "mysql", "sqlite", "mongodb"]):
            py_score += 5.0

        # Redis & Caching (up to 5 pts)
        if any(k in project_context for k in ["redis", "caching", "in-memory"]):
            py_score += 5.0
            strengths.append("Redis caching / in-memory store")
        else:
            concerns.append("Limited Redis or backend caching evidence")

        # Python Engineering & Clean Architecture (up to 7 pts)
        if any(k in project_context for k in ["pydantic", "clean architecture", "oop", "dependency injection"]):
            py_score += 7.0
        elif "python" in project_context:
            py_score += 4.0

        py_score = min(30.0, py_score)

        # -------------------------------------------------------------
        # 3. Cloud / Deployment / Full Stack (Max 15 points)
        # -------------------------------------------------------------
        cloud_score = 0.0

        # Docker & Containerization (up to 6 pts)
        if any(k in project_context for k in ["docker", "docker-compose", "container", "kubernetes", "k8s"]):
            cloud_score += 6.0
            strengths.append("Docker containerization & deployment")

        # Cloud Platform: GCP / AWS (up to 5 pts)
        if any(k in project_context for k in ["gcp", "google cloud"]):
            cloud_score += 5.0
            strengths.append("GCP cloud deployment experience")
        elif any(k in project_context for k in ["aws", "azure", "ec2", "s3", "lambda"]):
            cloud_score += 4.0
            strengths.append("Cloud infrastructure (AWS/Azure)")

        # Full Stack / Supporting Frontend (up to 4 pts)
        if any(k in project_context for k in ["react", "next.js", "nextjs", "typescript"]):
            cloud_score += 4.0
            strengths.append("Full stack capability (React/Next.js/TypeScript)")

        cloud_score = min(15.0, cloud_score)

        # -------------------------------------------------------------
        # 4. GitHub Activity (Max 10 points)
        # -------------------------------------------------------------
        gh_score = min(10.0, float(github_score))
        if gh_score >= 7.0:
            strengths.append(f"Strong public GitHub footprint ({github_metrics.cohort})")
        elif gh_score == 0.0 and github_metrics.status != "unlinked":
            concerns.append("Low or dormant public GitHub activity")

        # -------------------------------------------------------------
        # 5. Engineering Depth Signals (Max 5 points)
        # -------------------------------------------------------------
        eng_score = 0.0

        # Testing & CI/CD (up to 2 pts)
        if any(k in project_context for k in ["pytest", "unit test", "integration test", "ci/cd", "github actions"]):
            eng_score += 2.0
            strengths.append("Automated testing / CI/CD pipeline")
        else:
            concerns.append("No explicit testing (pytest/unit tests) mentioned")

        # Queues & Background Workers (up to 1.5 pts)
        if any(k in project_context for k in ["celery", "rabbitmq", "kafka", "background worker", "pub/sub"]):
            eng_score += 1.5
            strengths.append("Distributed task queues (Celery/RabbitMQ/Kafka)")

        # Observability & Concurrency (up to 1.5 pts)
        if any(k in project_context for k in ["opentelemetry", "prometheus", "logging", "concurrency", "multithreading"]):
            eng_score += 1.5
            strengths.append("Observability and concurrency handling")

        eng_score = min(5.0, eng_score)

        # Total Calculation
        total = round(ai_score + py_score + cloud_score + gh_score + eng_score, 1)

        breakdown = ScoreBreakdown(
            ai_project_depth=round(ai_score, 1),
            python_backend=round(py_score, 1),
            cloud_fullstack=round(cloud_score, 1),
            github=round(gh_score, 1),
            engineering_depth=round(eng_score, 1),
        )

        # Generate summary of candidate's technical profile
        project_summary = cls._generate_project_summary(resume, strengths, penalties_applied)

        return total, breakdown, strengths, concerns, penalties_applied, project_summary

    @staticmethod
    def _generate_project_summary(
        resume: ParsedResume, strengths: List[str], penalties: List[str]
    ) -> str:
        """Create a compact project summary describing candidate's main technical accomplishments."""
        if strengths:
            top_strengths = strengths[:3]
            summary = f"Built systems utilizing {', '.join(top_strengths)}."
        else:
            summary = f"Projects focused on {', '.join(resume.skills[:4]) if resume.skills else 'software development'}."

        if penalties:
            summary += f" Note: {penalties[0]}."

        return summary
