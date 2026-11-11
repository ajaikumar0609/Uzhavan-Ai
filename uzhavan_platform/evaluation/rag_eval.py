"""UZHAVAN AI — RAG retrieval quality evaluator.

Bypasses the LLM and queries ChromaDB directly to measure retrieval quality:
- Retrieval rate (% questions with ≥ 1 chunk above 0.35 threshold)
- Mean similarity score
- Key-fact coverage (% ground truth facts found in retrieved chunks)

Usage:
    python evaluation/rag_eval.py \\
        --chroma-path ./rag/chroma \\
        --questions evaluation/questions.json \\
        --ground-truth evaluation/ground_truth.json \\
        [--embed-model BAAI/bge-m3] \\
        [--threshold 0.35] \\
        [--top-k 6]
"""

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCORE_THRESHOLD = 0.35
COLLECTION_NAME = "tnau_knowledge"


def load_json(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        sys.exit(f"File not found: {p}")
    return json.loads(p.read_text())


def fact_covered(fact: str, chunks: list[str]) -> bool:
    """Check if any chunk contains the key terms of a fact (case-insensitive)."""
    fact_lower = fact.lower()
    # Use the first 4 significant words as a presence signal
    words = [w for w in fact_lower.split() if len(w) > 3][:4]
    combined = " ".join(chunk.lower() for chunk in chunks)
    return all(w in combined for w in words) if words else False


def evaluate_question(
    question: dict[str, Any],
    gt_map: dict[str, dict[str, Any]],
    collection: Any,
    embed_fn: Any,
    threshold: float,
    top_k: int,
) -> dict[str, Any]:
    qid = question["id"]
    result: dict[str, Any] = {
        "question_id": qid,
        "category": question["category"],
        "question": question["question"],
        "chunks_retrieved": 0,
        "chunks_above_threshold": 0,
        "scores": [],
        "mean_score": None,
        "retrieval_ok": False,
        "key_facts_found": [],
        "key_facts_missed": [],
        "coverage_rate": None,
        "latency_ms": None,
        "error": None,
    }

    try:
        t0 = time.perf_counter()
        query_embedding = embed_fn(question["question"])
        query_result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances"],
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        result["latency_ms"] = latency_ms

        docs: list[str] = query_result["documents"][0] if query_result["documents"] else []
        dists: list[float] = query_result["distances"][0] if query_result["distances"] else []

        # ChromaDB returns L2 distances when using cosine space; convert to similarity
        # For cosine distance: similarity = 1 - distance
        scores = [max(0.0, 1.0 - d) for d in dists]
        above = [s for s in scores if s >= threshold]

        result["chunks_retrieved"] = len(docs)
        result["chunks_above_threshold"] = len(above)
        result["scores"] = [round(s, 4) for s in scores]
        result["mean_score"] = round(statistics.mean(scores), 4) if scores else None
        result["retrieval_ok"] = len(above) > 0

        # Key-fact coverage (advisory questions only, if ground truth exists)
        gt = gt_map.get(qid)
        if gt and question["category"] == "advisory":
            key_facts: list[str] = gt.get("key_facts", [])
            above_docs = [docs[i] for i, s in enumerate(scores) if s >= threshold]
            for fact in key_facts:
                if fact_covered(fact, above_docs):
                    result["key_facts_found"].append(fact)
                else:
                    result["key_facts_missed"].append(fact)
            total_facts = len(key_facts)
            result["coverage_rate"] = (
                round(len(result["key_facts_found"]) / total_facts, 3)
                if total_facts
                else None
            )
    except Exception as exc:
        result["error"] = str(exc)

    return result


def print_summary(
    results: list[dict[str, Any]], threshold: float, embed_model: str
) -> None:
    sep = "─" * 60
    advisory = [r for r in results if r["category"] == "advisory" and not r["error"]]
    retrieved = [r for r in results if r["retrieval_ok"]]
    all_scores = [s for r in results for s in r["scores"]]
    latencies = [r["latency_ms"] for r in results if r["latency_ms"]]

    retrieval_rate = len(retrieved) / len(results) if results else 0.0
    mean_score = statistics.mean(all_scores) if all_scores else 0.0
    coverage_rates = [r["coverage_rate"] for r in advisory if r["coverage_rate"] is not None]
    mean_coverage = statistics.mean(coverage_rates) if coverage_rates else None
    mean_latency = int(statistics.mean(latencies)) if latencies else None

    print(f"\n{sep}")
    print("  UZHAVAN AI RAG Evaluation Summary")
    print(f"  Embed model: {embed_model}   Threshold: {threshold}")
    print(sep)
    print(f"  Questions evaluated:  {len(results)}")
    print(f"  Retrieval rate:       {retrieval_rate * 100:.1f}%  (≥1 chunk above {threshold})")
    print(f"  Mean similarity:      {mean_score:.3f}")
    if mean_coverage is not None:
        print(f"  Key-fact coverage:    {mean_coverage * 100:.1f}%  (advisory Qs only)")
    if mean_latency:
        print(f"  Mean latency:         {mean_latency} ms")

    errors = [r for r in results if r["error"]]
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for r in errors:
            print(f"    [{r['question_id']}] {r['error'][:80]}")

    # Show any question with zero chunks above threshold
    zero = [r for r in results if not r["retrieval_ok"] and not r["error"]]
    if zero:
        print(f"\n  Questions with no chunks above threshold ({len(zero)}):")
        for r in zero:
            print(f"    [{r['question_id']}] {r['question'][:70]}")
    print(sep)


def main() -> None:
    parser = argparse.ArgumentParser(description="UZHAVAN AI RAG evaluator")
    parser.add_argument("--chroma-path", default="./rag/chroma")
    parser.add_argument("--questions", default="evaluation/questions.json")
    parser.add_argument("--ground-truth", default="evaluation/ground_truth.json")
    parser.add_argument("--embed-model", default="BAAI/bge-m3")
    parser.add_argument("--threshold", type=float, default=SCORE_THRESHOLD)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--output-dir", default="evaluation/results")
    args = parser.parse_args()

    # Lazy import so the script is parseable without dependencies installed
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit(
            "Missing dependencies. Install: pip install chromadb sentence-transformers"
        )

    print(f"Loading embed model {args.embed_model} …")
    model = SentenceTransformer(args.embed_model)

    def embed_fn(text: str) -> list[float]:
        return model.encode(text, normalize_embeddings=True).tolist()

    print(f"Connecting to ChromaDB at {args.chroma_path} …")
    client = chromadb.PersistentClient(path=args.chroma_path)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        sys.exit(f"Collection '{COLLECTION_NAME}' not found in {args.chroma_path}")

    questions_data = load_json(args.questions)
    gt_data = load_json(args.ground_truth)
    gt_map: dict[str, dict[str, Any]] = {
        item["question_id"]: item for item in gt_data["ground_truth"]
    }

    questions = questions_data["questions"]
    print(f"Evaluating {len(questions)} questions …\n")

    results = [
        evaluate_question(q, gt_map, collection, embed_fn, args.threshold, args.top_k)
        for q in questions
    ]

    print_summary(results, args.threshold, args.embed_model)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = output_dir / f"rag_eval_{ts}.json"
    out_path.write_text(json.dumps(
        {"timestamp": ts, "embed_model": args.embed_model,
         "threshold": args.threshold, "results": results},
        ensure_ascii=False, indent=2,
    ))
    print(f"\n  Report written: {out_path}")


if __name__ == "__main__":
    main()
