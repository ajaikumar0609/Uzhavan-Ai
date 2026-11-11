"""
LLMService - local Ollama wrapper.

The Cognitive Engine calls LLMService.generate().

LOCAL-ONLY: the sole supported provider is ollama (local Qwen2.5). Zero-paid-API policy:
there is no Anthropic/OpenAI/Gemini or any other external-AI code path, and no fallback to
one. If Ollama is unavailable the caller gets an error response (never a cloud call).
"""
from __future__ import annotations

import os
import time

import httpx
from pydantic import BaseModel

_OLLAMA_URL = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
_LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))
_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    success: bool = True
    error: str | None = None


class LLMService:
    """
    Single generate() call. No tool use, no streaming, no multi-turn.
    Qwen3 is the reasoning component; it never retrieves data.
    """

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self._provider = provider or _LLM_PROVIDER
        self._model = model or _OLLAMA_MODEL

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Generate a response. Returns a fallback LLMResponse if the provider is unavailable."""
        if self._provider == "ollama":
            return await self._generate_ollama(system_prompt, user_prompt)
        return LLMResponse(
            content="",
            model=self._model,
            provider=self._provider,
            latency_ms=0,
            success=False,
            error=f"Unsupported provider: {self._provider}. Only LLM_PROVIDER=ollama (local) is supported",
        )

    async def _generate_ollama(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        start_ns = time.monotonic_ns()
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                # 1.2 produced near-gibberish Tamil with qwen2.5:7b; 1.05 is readable (checked
                # against local Ollama, 2026-11-08). Tamil grounding quality is still limited.
                "repeat_penalty": 1.05,
                "num_predict": 256,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=_LLM_TIMEOUT_S) as client:
                resp = await client.post(f"{_OLLAMA_URL}/api/chat", json=payload)
                resp.raise_for_status()
                body = resp.json()
                content = body.get("message", {}).get("content", "")
                usage = body.get("usage", {})
                return LLMResponse(
                    content=content,
                    model=self._model,
                    provider="ollama",
                    latency_ms=int((time.monotonic_ns() - start_ns) / 1_000_000),
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    success=bool(content),
                )
        except httpx.ConnectError:
            return LLMResponse(
                content="",
                model=self._model,
                provider="ollama",
                latency_ms=int((time.monotonic_ns() - start_ns) / 1_000_000),
                success=False,
                error="Ollama not running. Start with: ollama serve",
            )
        except Exception as exc:
            return LLMResponse(
                content="",
                model=self._model,
                provider="ollama",
                latency_ms=int((time.monotonic_ns() - start_ns) / 1_000_000),
                success=False,
                error=str(exc),
            )

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{_OLLAMA_URL}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return self._provider
