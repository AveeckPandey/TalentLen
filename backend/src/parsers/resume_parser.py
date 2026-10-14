"""Multi-format resume parser supporting PDF, DOCX, and TXT files with hyperlink extraction."""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
import fitz  # PyMuPDF
import pypdf
import docx

from src.models import ParsedResume
from src.parsers.entity_extractor import (
    extract_email,
    extract_phone,
    extract_github,
    extract_linkedin,
    extract_cgpa,
    extract_candidate_name,
    segment_sections,
    detect_related_experience,
)


class ResumeParser:
    """Robust parser for candidate resumes supporting PDF, DOCX, and TXT formats."""

    @classmethod
    def parse_file(cls, file_path: str | Path) -> ParsedResume:
        """Parse a single resume file with automatic format detection and fallback."""
        path = Path(file_path)
        file_name = path.name
        suffix = path.suffix.lower()

        try:
            author_meta = None
            if suffix == ".pdf":
                text, links, author_meta = cls._extract_from_pdf(path)
            elif suffix in [".docx", ".doc"]:
                text, links = cls._extract_from_docx(path)
            elif suffix in [".txt", ".md"]:
                text, links = cls._extract_from_txt(path)
            else:
                return ParsedResume(
                    file_name=file_name,
                    file_path=str(path),
                    candidate_name=path.stem.replace("_", " ").title(),
                    parsing_status=f"unsupported_format: {suffix}",
                )

            # Check if text is completely empty or unreadable
            cleaned_text = text.strip()
            if not cleaned_text:
                return ParsedResume(
                    file_name=file_name,
                    file_path=str(path),
                    candidate_name=path.stem.replace("_", " ").title(),
                    parsing_status="empty_text",
                )

            # Extract entities
            email = extract_email(cleaned_text)
            phone = extract_phone(cleaned_text)
            github_url, github_user = extract_github(cleaned_text, links)
            linkedin_url = extract_linkedin(cleaned_text, links)
            cgpa, cgpa_raw = extract_cgpa(cleaned_text)
            name = extract_candidate_name(cleaned_text, file_name, author_meta)

            sections = segment_sections(cleaned_text)
            has_experience, exp_years = detect_related_experience(
                cleaned_text, sections.get("experience", "")
            )

            return ParsedResume(
                file_name=file_name,
                file_path=str(path),
                candidate_name=name,
                email=email,
                phone=phone,
                github_url=github_url,
                github_username=github_user,
                linkedin_url=linkedin_url,
                cgpa=cgpa,
                cgpa_raw=cgpa_raw,
                skills=cls._extract_skills(cleaned_text),
                projects_text=sections.get("projects", ""),
                experience_text=sections.get("experience", ""),
                has_related_experience=has_experience,
                estimated_experience_years=exp_years,
                full_text=cleaned_text,
                parsing_status="success",
            )

        except Exception as exc:
            # Never crash batch on malformed resume
            return ParsedResume(
                file_name=file_name,
                file_path=str(path),
                candidate_name=path.stem.replace("_", " ").title(),
                parsing_status=f"error: {str(exc)[:100]}",
            )

    @classmethod
    def _extract_from_pdf(cls, path: Path) -> Tuple[str, List[str], Optional[str]]:
        """Extract text, clickable URI links, and author metadata from PDF using PyMuPDF with pypdf fallback."""
        text_pages: List[str] = []
        links: List[str] = []
        author: Optional[str] = None

        try:
            # Primary: PyMuPDF (fast, extracts link annotations accurately)
            doc = fitz.open(str(path))
            author = doc.metadata.get("author") if doc.metadata else None
            for page in doc:
                text_pages.append(page.get_text("text"))
                for link in page.get_links():
                    if "uri" in link and link["uri"]:
                        links.append(link["uri"])
            doc.close()
            full_text = "\n".join(text_pages)
            if full_text.strip():
                return full_text, links, author
        except Exception:
            pass

        # Fallback: pypdf
        try:
            reader = pypdf.PdfReader(str(path))
            if reader.metadata and reader.metadata.author:
                author = reader.metadata.author
            pdf_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pdf_text.append(extracted)
            return "\n".join(pdf_text), links, author
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF with both PyMuPDF and pypdf: {e}")

    @classmethod
    def _extract_from_docx(cls, path: Path) -> Tuple[str, List[str]]:
        """Extract text and hyperlinks from DOCX file."""
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        for table in doc.tables:
            for row in table.rows:
                paragraphs.append(" ".join([c.text for c in row.cells if c.text]))
        return "\n".join(paragraphs), []

    @classmethod
    def _extract_from_txt(cls, path: Path) -> Tuple[str, List[str]]:
        """Extract text from plain text or markdown file."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), []

    @classmethod
    def _extract_skills(cls, text: str) -> List[str]:
        """Identify recognized programming languages, frameworks, and tools."""
        known_keywords = [
            "python", "fastapi", "django", "flask", "postgresql", "postgres", "redis",
            "docker", "kubernetes", "k8s", "gcp", "google cloud", "aws", "azure",
            "langchain", "langgraph", "llamaindex", "rag", "chromadb", "faiss", "pinecone",
            "qdrant", "weaviate", "embeddings", "vector search", "tool calling",
            "openai", "gemini", "anthropic", "claude", "ollama", "transformers", "pytorch",
            "tensorflow", "react", "next.js", "typescript", "javascript", "node.js",
            "graphql", "rest api", "celery", "rabbitmq", "kafka", "pytest", "git",
            "ci/cd", "linux", "sql", "mongodb", "java", "spring boot", "c++"
        ]

        lower = text.lower()
        matched = []
        for kw in known_keywords:
            # Word boundary search
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, lower):
                # Standard casing
                canonical = kw.title() if len(kw) > 3 else kw.upper()
                if kw in ["fastapi", "next.js", "postgresql", "langchain", "langgraph", "llamaindex", "chromadb"]:
                    canonical = {"fastapi": "FastAPI", "next.js": "Next.js", "postgresql": "PostgreSQL",
                                 "langchain": "LangChain", "langgraph": "LangGraph", "llamaindex": "LlamaIndex",
                                 "chromadb": "ChromaDB"}.get(kw, kw)
                matched.append(canonical)
        return list(dict.fromkeys(matched))
