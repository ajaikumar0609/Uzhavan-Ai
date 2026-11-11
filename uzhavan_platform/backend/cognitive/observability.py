"""
Node observability for the Cognitive Engine.

Every graph node calls observe(node_name, state) to record its execution.
Produces NodeTrace entries appended to ConversationState["trace"].
All logging goes to stderr with structured fields so the trace is machine-parseable.
"""
from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

from backend.cognitive.models.node_context import NodeTrace

logger = logging.getLogger("uzhavan.cognitive")

if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@contextmanager
def observe(node_name: str, state: dict[str, Any]) -> Generator[None, None, None]:
    """
    Context manager that records node execution as a NodeTrace entry.

    Usage in every node:
        with observe("intent_router", state) as patch:
            ...
        return {**patch, "intent": ...}
    """
    start_ns = time.monotonic_ns()
    started_at = datetime.now(timezone.utc)
    trace: list[NodeTrace] = list(state.get("trace") or [])
    entry = NodeTrace(node=node_name, started_at=started_at)
    logger.info("NODE_START node=%s trace_id=%s", node_name, _trace_id(state))

    try:
        yield
        duration_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)
        entry.finished_at = datetime.now(timezone.utc)
        entry.duration_ms = duration_ms
        entry.success = True
        trace.append(entry)
        state["trace"] = trace
        logger.info("NODE_DONE  node=%s duration_ms=%d", node_name, duration_ms)
    except Exception as exc:
        duration_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)
        entry.finished_at = datetime.now(timezone.utc)
        entry.duration_ms = duration_ms
        entry.success = False
        entry.error = str(exc)
        trace.append(entry)
        state["trace"] = trace
        logger.error("NODE_ERROR node=%s duration_ms=%d error=%s", node_name, duration_ms, exc)
        raise


def _trace_id(state: dict[str, Any]) -> str:
    ctx = state.get("context")
    if ctx and hasattr(ctx, "system"):
        return ctx.system.trace_id
    return "unknown"


def build_trace_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Extract a compact trace summary from state, useful for response metadata."""
    traces: list[NodeTrace] = state.get("trace") or []
    return {
        "nodes": [
            {"node": t.node, "duration_ms": t.duration_ms, "success": t.success}
            for t in traces
        ],
        "total_ms": sum(t.duration_ms for t in traces),
        "failed_nodes": [t.node for t in traces if not t.success],
    }
