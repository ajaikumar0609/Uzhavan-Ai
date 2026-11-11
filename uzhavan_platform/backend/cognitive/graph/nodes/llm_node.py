"""
LLM Node — Qwen3 via Ollama

Input:  system_prompt, user_prompt
Output: raw_llm_response, llm_provider, llm_latency_ms

One job: call LLMService and return the raw response.
Qwen3 reasons only. It never retrieves data, checks weather, or performs calculations.
If Ollama is unavailable → graceful degradation with is_fallback=True.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.cognitive.llm.service import LLMService
from backend.cognitive.observability import observe

TAMIL_FALLBACK = (
    "மன்னிக்கவும். இந்த கேள்விக்கு தேவையான தகவல்கள் என்னிடம் இல்லை. "
    "TNAU உதவி மையத்தை தொடர்பு கொள்ளவும்: 0431-2371622"
)

ENGLISH_FALLBACK = (
    "Sorry, the information needed to answer this is not available right now. "
    "Please contact the TNAU help centre: 0431-2371622"
)


def fallback_for(language: str | None) -> str:
    """The safe "information not available" answer in the requested language."""
    return ENGLISH_FALLBACK if (language or "").lower() == "english" else TAMIL_FALLBACK


_THINK_BLOCK = re.compile(r"<think>.*?(</think>|$)", re.DOTALL | re.IGNORECASE)


def clean_llm_output(content: Any) -> str:
    """FP-015: tolerate malformed provider output. Non-text → "", reasoning blocks removed."""
    if not isinstance(content, str):
        return ""
    return _THINK_BLOCK.sub("", content).strip()


_TERMINATORS = ".!?।"


def trim_incomplete_tail(text: str) -> str:
    """The model is capped at 256 tokens and Tamil uses many tokens per word, so answers were cut
    mid-sentence ("...விதை வழங்குதல் பண்ப"). Drop the unfinished tail so the farmer (and TTS) never
    gets half a sentence. Text with no complete sentence at all is returned unchanged."""
    t = (text or "").rstrip()
    if not t or t[-1] in _TERMINATORS + ")\"'”":
        return t
    cut = max(t.rfind(c) for c in _TERMINATORS)
    return t[: cut + 1].rstrip() if cut >= 10 else t


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def llm_node(state: dict[str, Any]) -> dict[str, Any]:
    with observe("llm_node", state):
        system_prompt: str = state.get("system_prompt", "")
        user_prompt: str = state.get("user_prompt", "")

        if not system_prompt or not user_prompt:
            output: dict[str, Any] = {
                "raw_llm_response": TAMIL_FALLBACK,
                "llm_provider": "fallback",
                "llm_latency_ms": 0,
                "is_fallback": True,
            }
        else:
            content, success, provider, latency = "", False, "fallback", 0
            try:
                response = await get_llm_service().generate(system_prompt, user_prompt)
                content = trim_incomplete_tail(clean_llm_output(getattr(response, "content", None)))
                success = bool(getattr(response, "success", False))
                provider = getattr(response, "provider", "") or "unknown"
                latency = int(getattr(response, "latency_ms", 0) or 0)
            except Exception as exc:   # provider crash → safe fallback, never a stack trace
                logging.getLogger("uzhavan.llm").warning("LLM call failed: %s", type(exc).__name__)

            if not success or not content:
                ctx = state.get("context")
                lang = ctx.system.language if ctx and ctx.system else None
                output = {
                    "raw_llm_response": fallback_for(lang),
                    "llm_provider": "fallback",
                    "llm_latency_ms": latency,
                    "is_fallback": True,
                }
            else:
                output = {
                    "raw_llm_response": content,
                    "llm_provider": provider,
                    "llm_latency_ms": latency,
                    "is_fallback": False,
                }
    output["trace"] = state.get("trace", [])
    return output
