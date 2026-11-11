"""
UZHAVAN AI — Benchmark Dashboard

Reads all result JSON files in evaluation/results/ and renders a terminal
summary of platform intelligence quality.

Tracks:
  - Average latency (P50, P95)
  - Agent usage distribution
  - RAG retrieval hits
  - Hallucination rate
  - Grounding failure rate
  - Safety block rate
  - Top queries (by volume and by failure)
  - Cache hit rate
  - Language distribution
  - Conversation success rate

Usage:
    python evaluation/dashboard.py
    python evaluation/dashboard.py --results-dir evaluation/results
    python evaluation/dashboard.py --live --base-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── KPI targets (Sprint 5 gate) ────────────────────────────────────────────────

TARGETS = {
    "grounded_response_rate": 0.95,     # Flutter gate: must reach 95% before Sprint 6
    "intent_accuracy": 0.90,
    "citation_rate": 0.80,
    "hallucination_rate_max": 0.05,
    "p50_latency_ms": 5000,
    "p95_latency_ms": 15000,
    "error_rate_max": 0.02,
}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_benchmark_results(results_dir: Path) -> list[dict[str, Any]]:
    """Load all benchmark result files, newest first."""
    files = sorted(results_dir.glob("benchmark_*.json"), reverse=True)
    all_results: list[dict[str, Any]] = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            all_results.extend(data.get("results", []))
        except Exception:
            pass
    return all_results


def load_rag_results(results_dir: Path) -> list[dict[str, Any]]:
    files = sorted(results_dir.glob("rag_eval_*.json"), reverse=True)
    all_results: list[dict[str, Any]] = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            all_results.extend(data.get("results", []))
        except Exception:
            pass
    return all_results


def load_live_metrics(base_url: str) -> dict[str, Any] | None:
    """Fetch live metrics from GET /metrics if available."""
    try:
        import httpx
        resp = httpx.get(f"{base_url}/metrics", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ── Metric computation ────────────────────────────────────────────────────────

def compute_benchmark_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {}

    total = len(results)
    errors = [r for r in results if r.get("error")]
    successful = [r for r in results if not r.get("error")]
    latencies = [r["total_ms"] for r in successful if r.get("total_ms")]
    off_topic = [r for r in results if r.get("category") == "off_topic"]
    advisory = [r for r in results if r.get("category") not in ("off_topic",)]

    # Latency
    p50 = int(statistics.median(latencies)) if latencies else None
    p95_idx = max(0, int(len(latencies) * 0.95) - 1)
    p95 = int(sorted(latencies)[p95_idx]) if latencies else None

    # Citation rate (non-off-topic)
    with_sources = sum(1 for r in advisory if r.get("sources"))
    citation_rate = with_sources / len(advisory) if advisory else 0.0

    # Intent accuracy
    intent_matches = [
        r for r in results
        if r.get("intent_detected") and r.get("expected_intent")
        and r["intent_detected"] == r["expected_intent"]
    ]
    intent_total = sum(1 for r in results if r.get("expected_intent"))
    intent_accuracy = len(intent_matches) / intent_total if intent_total else None

    # Hallucination: off-topic that returned an answer without fallback
    hallucinated = [r for r in off_topic if not r.get("used_fallback") and r.get("answer")]
    hallucination_rate = len(hallucinated) / len(off_topic) if off_topic else 0.0

    # Grounded response rate (answers with citations)
    grounded = sum(1 for r in advisory if r.get("sources"))
    grounded_rate = grounded / len(advisory) if advisory else 0.0

    # Language distribution
    lang_dist = Counter(r.get("language", "unknown") for r in results)

    # Agent usage (tools_used across all results)
    agent_counter: Counter = Counter()
    for r in results:
        for tool in r.get("tools_used", []):
            agent_counter[tool] += 1

    # Top failed questions
    top_failures = [r for r in results if r.get("error") or (
        r.get("category") == "off_topic" and not r.get("used_fallback") and r.get("answer")
    )][:5]

    return {
        "total_questions": total,
        "errors": len(errors),
        "error_rate": round(len(errors) / total, 3) if total else 0.0,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "mean_latency_ms": int(statistics.mean(latencies)) if latencies else None,
        "citation_rate": round(citation_rate, 3),
        "intent_accuracy": round(intent_accuracy, 3) if intent_accuracy is not None else None,
        "hallucination_rate": round(hallucination_rate, 3),
        "grounded_response_rate": round(grounded_rate, 3),
        "language_distribution": dict(lang_dist),
        "agent_usage": dict(agent_counter.most_common(10)),
        "top_failures": top_failures,
    }


def compute_rag_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {}

    total = len(results)
    retrieved = [r for r in results if r.get("retrieval_ok")]
    all_scores = [s for r in results for s in r.get("scores", [])]
    latencies = [r["latency_ms"] for r in results if r.get("latency_ms")]
    coverage_rates = [r["coverage_rate"] for r in results if r.get("coverage_rate") is not None]

    return {
        "total_questions": total,
        "retrieval_rate": round(len(retrieved) / total, 3) if total else 0.0,
        "mean_similarity": round(statistics.mean(all_scores), 3) if all_scores else None,
        "mean_coverage_rate": round(statistics.mean(coverage_rates), 3) if coverage_rates else None,
        "mean_latency_ms": int(statistics.mean(latencies)) if latencies else None,
        "zero_retrieval_questions": [
            {"id": r["question_id"], "question": r["question"][:60]}
            for r in results if not r.get("retrieval_ok") and not r.get("error")
        ][:5],
    }


# ── Rendering ─────────────────────────────────────────────────────────────────

def _kpi(name: str, value: float | int | None, target: float | int, unit: str = "%",
         higher_is_better: bool = True, width: int = 28) -> str:
    if value is None:
        return f"  ⚠️   {name:<{width}}  N/A"
    display = f"{value * 100:.1f}" if unit == "%" else str(value)
    target_display = f"{target * 100:.0f}" if unit == "%" else str(target)
    ok = (value >= target) if higher_is_better else (value <= target)
    mark = "✅" if ok else "❌"
    return f"  {mark}  {name:<{width}} {display}{unit}  (target: {target_display}{unit})"


def render(
    bench: dict[str, Any],
    rag: dict[str, Any],
    live: dict[str, Any] | None,
) -> None:
    sep = "═" * 66
    thin = "─" * 66
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"\n{sep}")
    print("  UZHAVAN AI — Intelligence Benchmark Dashboard")
    print(f"  {now}")
    print(sep)

    # ── Sprint 5 Flutter Gate ──────────────────────────────────────────────────
    print("\n  SPRINT 5 GATE  (must pass all ✅ before Flutter)")
    print(thin)
    print(_kpi("Grounded Response Rate", bench.get("grounded_response_rate"),
               TARGETS["grounded_response_rate"]))
    print(_kpi("Intent Accuracy", bench.get("intent_accuracy"),
               TARGETS["intent_accuracy"]))
    print(_kpi("Citation Rate", bench.get("citation_rate"),
               TARGETS["citation_rate"]))
    print(_kpi("Hallucination Rate", bench.get("hallucination_rate"),
               TARGETS["hallucination_rate_max"], higher_is_better=False))
    print(_kpi("Error Rate", bench.get("error_rate"),
               TARGETS["error_rate_max"], higher_is_better=False))

    # ── Latency ───────────────────────────────────────────────────────────────
    if bench:
        print(f"\n  LATENCY")
        print(thin)
        print(_kpi("P50 latency", bench.get("p50_latency_ms"),
                   TARGETS["p50_latency_ms"], unit="ms", higher_is_better=False))
        print(_kpi("P95 latency", bench.get("p95_latency_ms"),
                   TARGETS["p95_latency_ms"], unit="ms", higher_is_better=False))
        if bench.get("mean_latency_ms"):
            print(f"  {'':4}{'Mean latency':<28} {bench['mean_latency_ms']}ms")

    # ── RAG Quality ───────────────────────────────────────────────────────────
    if rag:
        print(f"\n  RAG QUALITY")
        print(thin)
        rr = rag.get("retrieval_rate")
        ms = rag.get("mean_similarity")
        mc = rag.get("mean_coverage_rate")
        ml = rag.get("mean_latency_ms")
        print(f"  {'':4}{'Retrieval rate':<28} {f'{rr*100:.1f}%' if rr is not None else 'N/A'}")
        print(f"  {'':4}{'Mean similarity score':<28} {f'{ms:.3f}' if ms is not None else 'N/A'}")
        print(f"  {'':4}{'Key-fact coverage':<28} {f'{mc*100:.1f}%' if mc is not None else 'N/A'}")
        print(f"  {'':4}{'Mean retrieval latency':<28} {f'{ml}ms' if ml else 'N/A'}")
        zero = rag.get("zero_retrieval_questions", [])
        if zero:
            print(f"\n  Questions with zero retrieval ({len(zero)}):")
            for q in zero:
                print(f"    [{q['id']}] {q['question']}")

    # ── Agent Usage ───────────────────────────────────────────────────────────
    usage = bench.get("agent_usage") or (live or {}).get("agent_usage", {})
    if usage:
        print(f"\n  AGENT USAGE (top tools)")
        print(thin)
        total_calls = sum(usage.values())
        for agent, count in sorted(usage.items(), key=lambda x: -x[1])[:8]:
            pct = count / total_calls * 100 if total_calls else 0
            bar = "█" * min(int(pct / 5), 20)
            print(f"  {'':4}{agent:<30} {count:>4}  {bar} {pct:.0f}%")

    # ── Language Distribution ─────────────────────────────────────────────────
    lang = bench.get("language_distribution", {})
    if lang:
        print(f"\n  LANGUAGE DISTRIBUTION")
        print(thin)
        total_lang = sum(lang.values())
        for language, count in sorted(lang.items(), key=lambda x: -x[1]):
            pct = count / total_lang * 100 if total_lang else 0
            bar = "█" * min(int(pct / 5), 20)
            print(f"  {'':4}{language:<20} {count:>4}  {bar} {pct:.0f}%")

    # ── Live Metrics ──────────────────────────────────────────────────────────
    if live:
        print(f"\n  LIVE PLATFORM METRICS  (from /metrics)")
        print(thin)
        print(f"  {'':4}{'Total requests':<28} {live.get('total_requests', 'N/A')}")
        print(f"  {'':4}{'Avg latency':<28} {live.get('avg_latency_ms', 'N/A')}ms")
        fr = live.get("fallback_rate")
        print(f"  {'':4}{'Fallback rate':<28} {f'{fr*100:.1f}%' if fr is not None else 'N/A'}")
        gb = live.get("grounding_block_rate")
        print(f"  {'':4}{'Grounding block rate':<28} {f'{gb*100:.1f}%' if gb is not None else 'N/A'}")
        sb = live.get("safety_block_rate")
        print(f"  {'':4}{'Safety block rate':<28} {f'{sb*100:.1f}%' if sb is not None else 'N/A'}")
        ac = live.get("avg_confidence")
        print(f"  {'':4}{'Avg confidence':<28} {f'{ac:.3f}' if ac is not None else 'N/A'}")

        intent_dist = live.get("intent_distribution", {})
        if intent_dist:
            print(f"\n  Top intents (live):")
            total_int = sum(intent_dist.values())
            for intent, count in sorted(intent_dist.items(), key=lambda x: -x[1])[:6]:
                pct = count / total_int * 100 if total_int else 0
                print(f"    {intent:<20} {count:>4}  ({pct:.0f}%)")

    # ── Top Failures ──────────────────────────────────────────────────────────
    failures = bench.get("top_failures", [])
    if failures:
        print(f"\n  TOP FAILURES")
        print(thin)
        for r in failures:
            err = r.get("error", "hallucination (off-topic)")
            print(f"  ❌  [{r.get('question_id', '?')}] {r.get('question', '')[:55]}")
            print(f"       Reason: {str(err)[:60]}")

    # ── Summary stats ─────────────────────────────────────────────────────────
    if bench:
        total_q = bench.get("total_questions", 0)
        errors = bench.get("errors", 0)
        print(f"\n  {'Total benchmark questions':<32} {total_q}")
        print(f"  {'Errors':<32} {errors}")

    print(f"\n{sep}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="UZHAVAN AI benchmark dashboard")
    parser.add_argument("--results-dir", default="evaluation/results",
                        help="Directory containing benchmark_*.json and rag_eval_*.json files")
    parser.add_argument("--live", action="store_true",
                        help="Also fetch live metrics from the running server")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Base URL for live metrics fetch")
    parser.add_argument("--watch", action="store_true",
                        help="Refresh every 30 seconds (requires --live)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        sys.exit(f"Results directory not found: {results_dir}\n"
                 "Run evaluation/benchmark.py first to generate results.")

    def refresh() -> None:
        bench_raw = load_benchmark_results(results_dir)
        rag_raw = load_rag_results(results_dir)
        live = load_live_metrics(args.base_url) if args.live else None
        bench = compute_benchmark_metrics(bench_raw)
        rag = compute_rag_metrics(rag_raw)
        render(bench, rag, live)
        if not bench_raw and not rag_raw and not live:
            print("No results found. Run evaluation/benchmark.py or evaluation/rag_eval.py first.\n")

    if args.watch and args.live:
        try:
            while True:
                refresh()
                print("  Refreshing in 30s… (Ctrl-C to stop)\n")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
    else:
        refresh()


if __name__ == "__main__":
    main()
