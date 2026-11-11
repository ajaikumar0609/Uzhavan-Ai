"""UZHAVAN AI — End-to-end benchmark runner.

Calls /chat for every question in questions.json, measures latency and quality,
and writes a JSON report + terminal summary table.

Usage:
    python evaluation/benchmark.py \\
        --base-url http://localhost:8002 \\
        --questions evaluation/questions.json \\
        --output-dir evaluation/results/ \\
        [--auth-token JWT] \\
        [--max-questions 5]
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


# ── KPI targets ─────────────────────────────────────────────────────────────
TARGETS = {
    "p50_latency_ms": 5000,
    "p95_latency_ms": 8000,
    "citation_rate": 0.80,
    "correct_intent_rate": 0.85,
    "hallucination_rate_max": 0.05,   # off_topic questions that returned an answer
    "fallback_rate_off_topic": 0.95,  # off_topic that correctly used fallback
}


async def call_chat(
    client: httpx.AsyncClient,
    base_url: str,
    question: dict[str, Any],
    token: str | None,
) -> dict[str, Any]:
    """Call /chat endpoint, collect SSE events, return parsed result."""
    headers: dict[str, str] = {"Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = {
        "message": question["question"],
        "language": "Tamil" if question["language"] in ("Tamil", "Tanglish") else "English",
    }

    result: dict[str, Any] = {
        "question_id": question["id"],
        "category": question["category"],
        "language": question["language"],
        "question": question["question"],
        "answer": "",
        "sources": [],
        "intent_detected": None,
        "tools_used": [],
        "confidence": None,
        "used_fallback": False,
        "total_ms": None,
        "error": None,
    }

    start = time.perf_counter()
    try:
        async with client.stream(
            "POST",
            f"{base_url}/chat",
            json=body,
            headers=headers,
            timeout=30.0,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = json.loads(line[6:])
                event_type = payload.get("type")
                if event_type == "delta":
                    result["answer"] += payload.get("content", "")
                elif event_type == "sources":
                    result["sources"] = payload.get("sources", [])
                elif event_type == "meta":
                    result["intent_detected"] = payload.get("intent")
                    result["tools_used"] = payload.get("tools_used", [])
                elif event_type == "done":
                    pass
    except Exception as exc:
        result["error"] = str(exc)

    result["total_ms"] = int((time.perf_counter() - start) * 1000)

    # Detect fallback usage: no answer generated but a Tamil refusal message
    if result["answer"] and not result["sources"]:
        fallback_phrases = ["மன்னிக்கவும்", "BAO", "KVK", "தொடர்பு கொள்", "sorry"]
        if any(p.lower() in result["answer"].lower() for p in fallback_phrases):
            result["used_fallback"] = True

    if result["sources"]:
        scores = [s.get("confidence", 0) for s in result["sources"] if "confidence" in s]
        result["confidence"] = min(scores) if scores else None

    return result


def compute_metrics(
    results: list[dict[str, Any]],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    q_map = {q["id"]: q for q in questions}
    latencies = [r["total_ms"] for r in results if r["total_ms"] and not r["error"]]

    advisory_results = [r for r in results if r["category"] == "advisory"]
    off_topic_results = [r for r in results if r["category"] == "off_topic"]
    all_non_off = [r for r in results if r["category"] != "off_topic"]

    # Citation rate (non-off_topic only)
    with_source = sum(1 for r in all_non_off if r["sources"])
    citation_rate = with_source / len(all_non_off) if all_non_off else 0.0

    # Intent accuracy
    intent_correct = 0
    intent_total = 0
    for r in results:
        q = q_map.get(r["question_id"])
        if q and q.get("expected_intent") and r["intent_detected"]:
            intent_total += 1
            if r["intent_detected"] == q["expected_intent"]:
                intent_correct += 1
    intent_accuracy = intent_correct / intent_total if intent_total else 0.0

    # Hallucination rate (off_topic that did NOT use fallback)
    hallucinated = [r for r in off_topic_results if not r["used_fallback"] and r["answer"]]
    hallucination_rate = len(hallucinated) / len(off_topic_results) if off_topic_results else 0.0

    fallback_rate = 1.0 - hallucination_rate

    return {
        "total_questions": len(results),
        "errors": sum(1 for r in results if r["error"]),
        "p50_latency_ms": int(statistics.median(latencies)) if latencies else None,
        "p95_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.95)]) if latencies else None,
        "mean_latency_ms": int(statistics.mean(latencies)) if latencies else None,
        "citation_rate": round(citation_rate, 3),
        "intent_accuracy": round(intent_accuracy, 3),
        "hallucination_rate": round(hallucination_rate, 3),
        "fallback_rate_off_topic": round(fallback_rate, 3),
        "targets": TARGETS,
    }


def print_summary(metrics: dict[str, Any], results: list[dict[str, Any]]) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print("  UZHAVAN AI Benchmark Summary")
    print(sep)

    checks = [
        ("P50 latency", metrics["p50_latency_ms"], TARGETS["p50_latency_ms"], "ms", False),
        ("P95 latency", metrics["p95_latency_ms"], TARGETS["p95_latency_ms"], "ms", False),
        ("Citation rate", metrics["citation_rate"], TARGETS["citation_rate"], "%", True),
        ("Intent accuracy", metrics["intent_accuracy"], TARGETS["correct_intent_rate"], "%", True),
        ("Hallucination rate", metrics["hallucination_rate"], TARGETS["hallucination_rate_max"], "%", False),
        ("Off-topic fallback", metrics["fallback_rate_off_topic"], TARGETS["fallback_rate_off_topic"], "%", True),
    ]

    for name, value, target, unit, higher_is_better in checks:
        if value is None:
            status = "⚠️  N/A "
        else:
            display = f"{value * 100:.1f}" if unit == "%" else str(value)
            if higher_is_better:
                ok = value >= target
            else:
                ok = value <= target
            status = "✅" if ok else "❌"
            target_display = f"{target * 100:.0f}" if unit == "%" else str(target)
            print(f"  {status}  {name:<25} {display}{unit}  (target: {target_display}{unit})")

    print(f"\n  Total questions: {metrics['total_questions']}")
    print(f"  Errors: {metrics['errors']}")

    if metrics["errors"]:
        print("\n  Errors:")
        for r in results:
            if r["error"]:
                print(f"    [{r['question_id']}] {r['error'][:80]}")
    print(sep)


async def run(args: argparse.Namespace) -> None:
    questions_path = Path(args.questions)
    if not questions_path.exists():
        sys.exit(f"questions file not found: {questions_path}")

    data = json.loads(questions_path.read_text())
    questions: list[dict[str, Any]] = data["questions"]

    if args.max_questions:
        questions = questions[: args.max_questions]

    print(f"Running benchmark: {len(questions)} questions → {args.base_url}/chat")

    async with httpx.AsyncClient() as client:
        tasks = [call_chat(client, args.base_url, q, args.auth_token) for q in questions]
        results: list[dict[str, Any]] = await asyncio.gather(*tasks)

    metrics = compute_metrics(results, questions)
    print_summary(metrics, results)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"benchmark_{ts}.json"
    latest_path = output_dir / "benchmark_latest.json"

    report = {
        "timestamp": ts,
        "base_url": args.base_url,
        "questions_file": str(questions_path),
        "metrics": metrics,
        "results": results,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    latest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n  Report written: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="UZHAVAN AI benchmark runner")
    parser.add_argument("--base-url", default="http://localhost:8002")
    parser.add_argument("--questions", default="evaluation/questions.json")
    parser.add_argument("--output-dir", default="evaluation/results")
    parser.add_argument("--auth-token", default=None)
    parser.add_argument("--max-questions", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
