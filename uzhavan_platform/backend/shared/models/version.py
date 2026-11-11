"""
UZHAVAN AI — Platform version manifest.

Every conversation stores these versions so that six months from now,
when prompts or models change, you know exactly which version produced which response.
"""
from __future__ import annotations

import os

from pydantic import BaseModel

AI_VERSION = os.getenv("AI_VERSION", "0.1.0")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "1.0.0")
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "1")
RAG_VERSION = os.getenv("RAG_VERSION", "1")
EMBEDDING_VERSION = os.getenv("EMBEDDING_VERSION", "1.0")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")


class PlatformVersion(BaseModel):
    ai_version: str = AI_VERSION
    graph_version: str = GRAPH_VERSION
    prompt_version: str = PROMPT_VERSION
    rag_version: str = RAG_VERSION
    embedding_version: str = EMBEDDING_VERSION
    model: str = MODEL_NAME

    @classmethod
    def current(cls) -> "PlatformVersion":
        return cls()
