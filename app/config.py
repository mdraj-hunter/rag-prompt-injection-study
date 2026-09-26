"""
Central configuration loader.
All settings come from environment variables (via .env), never hardcoded.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val else default


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    return float(val) if val else default


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")

    # Groq (primary — free tier, no billing account required)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "")

    # Gemini (optional)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "")

    # OpenAI (optional)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")

    # Embeddings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Experiment controls
    max_cases: int = _get_int("MAX_CASES", 10)
    request_delay_seconds: float = _get_float("REQUEST_DELAY_SECONDS", 1.0)
    max_retries: int = _get_int("MAX_RETRIES", 5)
    cache_dir: str = os.getenv("CACHE_DIR", "results/cache")

    def validate(self) -> None:
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("LLM_PROVIDER=groq but GROQ_API_KEY is not set.")
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set.")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set.")
        if self.llm_provider not in ("groq", "gemini", "openai"):
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{self.llm_provider}'. Use 'groq', 'gemini', or 'openai'."
            )


settings = Settings()