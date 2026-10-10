"""Configuration management for candidate screening system."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Project directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    INPUT_DIR: Path = Field(default=Path("./resumes"))
    OUTPUT_FILE: Path = Field(default=Path("./output/results.json"))

    # GitHub API
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub PAT for public API rate limits")
    GITHUB_CACHE_FILE: Path = Field(default=Path("./output/.github_cache.json"))

    # LLM Settings
    LLM_PROVIDER: str = Field(default="auto", description="auto, groq, openai, gemini, anthropic, or heuristic")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1")

    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")

    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key (OpenAI-compatible)")
    GROQ_MODEL: str = Field(default="qwen/qwen3.8-27b", description="Groq model ID, e.g. qwen/qwen3.8-27b")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1")

    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-haiku-latest")
    ANTHROPIC_BASE_URL: str = Field(default="https://api.anthropic.com/v1")

    # Concurrency & Performance
    CONCURRENCY_LIMIT: int = Field(default=5, description="Max concurrent worker tasks")
    REQUEST_TIMEOUT: float = Field(default=15.0, description="Network timeout in seconds")

    # Supabase Auth / DB / Storage (supports legacy + new publishable/secret keys)
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL, e.g. https://xyz.supabase.co")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Legacy anon public key (frontend, optional if publishable set)")
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, description="New publishable key sb_publishable_... (frontend)")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, description="Legacy service_role key (backend only, never expose)")
    SUPABASE_SECRET_KEY: Optional[str] = Field(default=None, description="New secret key sb_secret_... (backend only, never expose)")
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None, description="Legacy JWT secret for HS256 local verification")
    SUPABASE_JWKS_URL: Optional[str] = Field(default=None, description="JWKS URL for asymmetric JWT verification (new Supabase Auth)")
    REQUIRE_AUTH: bool = Field(default=False, description="Enforce Supabase JWT on API routes. Set true on Render prod.")

    @property
    def frontend_key(self) -> Optional[str]:
        return self.SUPABASE_PUBLISHABLE_KEY or self.SUPABASE_ANON_KEY

    @property
    def backend_key(self) -> Optional[str]:
        return self.SUPABASE_SECRET_KEY or self.SUPABASE_SERVICE_KEY or self.SUPABASE_PUBLISHABLE_KEY or self.SUPABASE_ANON_KEY

    @property
    def effective_jwks_url(self) -> Optional[str]:
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    # Scoring Weights (Total: 100)
    WEIGHT_AI_PROJECT_DEPTH: int = 40
    WEIGHT_PYTHON_BACKEND: int = 30
    WEIGHT_CLOUD_FULLSTACK: int = 15
    WEIGHT_GITHUB: int = 10
    WEIGHT_ENGINEERING_DEPTH: int = 5

    # Penalties
    PENALTY_SHALLOW_WRAPPER_MIN: int = 5
    PENALTY_SHALLOW_WRAPPER_MAX: int = 15
    PENALTY_TUTORIAL_PROJECT: int = 8

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
