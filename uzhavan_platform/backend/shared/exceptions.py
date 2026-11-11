from __future__ import annotations


class UzhavanError(Exception):
    """Base exception for all UZHAVAN AI errors."""


class RAGError(UzhavanError):
    """ChromaDB retrieval failure or empty collection."""


class WeatherError(UzhavanError):
    """Open-Meteo API failure or district coordinates not found."""


class VerificationError(UzhavanError):
    """Grounding validator triggered — insufficient evidence to generate a response."""


class SafetyError(UzhavanError):
    """Safety validator triggered — LLM output failed language or content checks."""


class ToolNotFoundError(UzhavanError):
    """Capability Resolver could not find an agent for the requested capability."""


class AgentError(UzhavanError):
    """A domain agent raised an unexpected internal error."""


class SessionError(UzhavanError):
    """Session not found or session isolation violation."""


class AuthError(UzhavanError):
    """JWT validation failed or token expired."""


class RateLimitError(UzhavanError):
    """Per-farmer request rate limit exceeded."""
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds}s.")
