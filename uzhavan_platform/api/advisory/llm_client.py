"""
UZHAVAN AI — LLM Client
========================
Unified interface for:
  - Claude API (Anthropic)  — production / cloud
  - Ollama / Qwen3          — local / on-device

Selected by LLM_PROVIDER env variable: "claude" | "ollama"
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger("llm_client")

LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "claude")   # "claude" or "ollama"
CLAUDE_MODEL   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# System prompt — injected into every advisory conversation
SYSTEM_PROMPT = """You are UZHAVAN AI, an agricultural advisory assistant for Tamil Nadu farmers.

You answer in the farmer's preferred language (Tamil or English).

Rules:
1. NEVER guess crop recommendations, fertilizer doses, or pesticide schedules from your training data.
2. ONLY use information from the provided TNAU knowledge sources (shown in <context>).
3. If the context does not contain enough information, say so clearly and suggest the farmer contact their Block Agriculture Officer (BAO).
4. Always cite the source URL when giving specific recommendations.
5. Keep responses practical and actionable — farmers need to act on this advice.
6. For Tamil responses, use simple spoken Tamil (not formal literary Tamil).
7. When mentioning chemicals, always include the dose, dilution, and safety note to wear gloves.

Format: Short paragraphs. Bullet points for step-by-step advice. End with one practical next action."""


def _format_context(chunks: list[Any]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}] {chunk.title or chunk.source_url}\n"
            f"Category: {chunk.category} | Crop: {chunk.crop}\n"
            f"{chunk.content}\n"
            f"URL: {chunk.source_url}"
        )
    return "\n\n---\n\n".join(parts)


async def generate_advisory(
    question: str,
    chunks: list[Any],
    language: str = "English",
    conversation_history: list[dict] | None = None,
) -> tuple[str, list[str]]:
    """
    Returns (answer_text, sources_used).
    """
    context    = _format_context(chunks)
    sources    = [c.source_url for c in chunks if c.source_url]
    lang_note  = f"Respond in {language}." if language != "English" else ""

    user_message = (
        f"{lang_note}\n\n"
        f"<context>\n{context}\n</context>\n\n"
        f"Farmer's question: {question}"
    )

    if LLM_PROVIDER == "ollama":
        answer = await _ollama_generate(user_message, conversation_history or [])
    else:
        answer = await _claude_generate(user_message, conversation_history or [])

    return answer, list(dict.fromkeys(sources))   # deduplicated, order-preserved


async def _claude_generate(
    user_message: str,
    history: list[dict],
) -> str:
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        messages = history + [{"role": "user", "content": user_message}]

        response = await client.messages.create(
            model      = CLAUDE_MODEL,
            max_tokens = 1024,
            system     = SYSTEM_PROMPT,
            messages   = messages,
        )
        return response.content[0].text
    except Exception as exc:
        log.exception("Claude API error")
        return f"Advisory service error: {exc}"


async def _ollama_generate(
    user_message: str,
    history: list[dict],
) -> str:
    try:
        import httpx

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model":    OLLAMA_MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  {"temperature": 0.3, "num_predict": 1024},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except Exception as exc:
        log.exception("Ollama API error")
        return f"Local LLM error: {exc}. Is Ollama running? Try: ollama serve"
