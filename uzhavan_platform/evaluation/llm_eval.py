"""UZHAVAN AI — LLM response quality evaluator.

Reads a benchmark results file and evaluates:
- Citation rate: does every non-off-topic answer have a source URL?
- Hallucination rate: do off-topic questions return an answer instead of a fallback?
- Language accuracy: are Tamil questions answered in Tamil?
- Actionability: does the answer contain an actionable next step?

Usage:
    python evaluation/llm_eval.py \\
        --results evaluation/results/benchmark_latest.json \\
        --ground-truth evaluation/ground_truth.json \\
        [--citation-domains agritech.tnau.ac.in,tnau.ac.in]
"""

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


# KPI targets
CITATION_RATE_TARGET = 0.80
HALLUCINATION_RATE_MAX = 0.05
LANGUAGE_ACCURACY_TARGET = 0.85
ACTIONABILITY_TARGET = 0.75

DEFAULT_CITATION_DOMAINS = ["agritech.tnau.ac.in", "tnau.ac.in", "pmfby.gov.in"]

# Tamil Unicode block: U+0B80–U+0BFF
TAMIL_RANGE = range(0x0B80, 0x0C00)

# Action keywords in Tamil and English
TAMIL_ACTION_VERBS = [
    "தெளிக்க", "போடவும்", "வடிகட்ட", "கண்காணிக்க", "நீக்கவும்",
    "வெளியிடவும்", "பயன்படுத்தவும்", "பதிவு", "விண்ணப்பிக்க",
    "தொடர்பு கொள்", "செய்யவும்", "கொடுக்கவும்", "வையுங்கள்",
]
ENGLISH_ACTION_VERBS = [
    "apply", "spray", "use", "irrigate", "harvest", "plant", "sow",
    "contact", "register", "submit", "avoid", "ensure", "add", "remove",
]


def is_tamil_char(ch: str) -> bool:
    return ord(ch) in TAMIL_RANGE


def tamil_ratio(text: str) -> float:
    """Fraction of alphabetic characters that are Tamil Unicode."""
    alpha = [c for c in text if unicodedata.category(c).startswith("L")]
    if not alpha:
        return 0.0
    tamil = [c for c in alpha if is_tamil_char(c)]
    return len(tamil) / len(alpha)


def has_citation(answer: str, sources: list[dict], domains: list[str]) -> bool:
    """Check if any domain appears in the answer text or in source URLs."""
    answer_lower = answer.lower()
    for domain in domains:
        if domain in answer_lower:
            return True
    for src in sources:
        url = src.get("url", "").lower()
        if any(d in url for d in domains):
            return True
    return False


def is_fallback(answer: str) -> bool:
    """Heuristic: Tamil or English fallback phrases present, no structured content."""
    fallback_phrases = [
        "மன்னிக்கவும்", "bao", "kvk", "தொடர்பு கொள்",
        "sorry", "i cannot", "i'm unable", "not in my knowledge",
        "இதற்கு பதில் கிடைக்கவில்லை",
    ]
    lower = answer.lower()
    return any(p in lower for p in fallback_phrases)


def is_actionable(answer: str) -> bool:
    """Check first 100 words for a known action verb."""
    words = answer.lower().split()[:100]
    text_fragment = " ".join(words)
    for verb in TAMIL_ACTION_VERBS + ENGLISH_ACTION_VERBS:
        if verb in text_fragment:
            return True
    return False


def evaluate_result(
    result: dict[str, Any],
    gt_map: dict[str, dict[str, Any]],
    citation_domains: list[str],
) -> dict[str, Any]:
    qid = result["question_id"]
    category = result.get("category", "")
    language = result.get("language", "English")
    answer = result.get("answer", "")
    sources = result.get("sources", [])

    eval_result: dict[str, Any] = {
        "question_id": qid,
        "category": category,
        "language": language,
        "answer_length": len(answer),
        "citation_ok": None,
        "hallucination": None,
        "language_ok": None,
        "actionable": None,
        "ground_truth_facts_covered": None,
    }

    if result.get("error"):
        eval_result["error"] = result["error"]
        return eval_result

    is_off_topic = category == "off_topic"

    # Citation check (non-off-topic only)
    if not is_off_topic:
        eval_result["citation_ok"] = has_citation(answer, sources, citation_domains)

    # Hallucination check (off-topic only)
    if is_off_topic:
        used_fallback = result.get("used_fallback", is_fallback(answer))
        eval_result["hallucination"] = not used_fallback  # True = hallucinated

    # Language accuracy (Tamil questions only)
    if language in ("Tamil", "Tanglish"):
        ratio = tamil_ratio(answer)
        eval_result["tamil_ratio"] = round(ratio, 3)
        eval_result["language_ok"] = ratio >= 0.30

    # Actionability (non-off-topic only)
    if not is_off_topic:
        eval_result["actionable"] = is_actionable(answer)

    # Ground truth fact coverage (advisory only, if GT exists)
    gt = gt_map.get(qid)
    if gt and category == "advisory":
        key_facts: list[str] = gt.get("key_facts", [])
        answer_lower = answer.lower()
        covered = [
            f for f in key_facts
            if any(w in answer_lower for w in f.lower().split() if len(w) > 4)
        ]
        eval_result["ground_truth_facts_covered"] = (
            round(len(covered) / len(key_facts), 3) if key_facts else None
        )

    return eval_result


def print_summary(
    evals: list[dict[str, Any]],
    citation_domains: list[str],
) -> None:
    sep = "─" * 60
    non_off = [e for e in evals if e["category"] != "off_topic" and not e.get("error")]
    off_topic = [e for e in evals if e["category"] == "off_topic" and not e.get("error")]
    tamil_qs = [e for e in non_off if e["language"] in ("Tamil", "Tanglish") and e.get("language_ok") is not None]

    citation_rate = (
        sum(1 for e in non_off if e.get("citation_ok")) / len(non_off)
        if non_off else 0.0
    )
    hallucination_rate = (
        sum(1 for e in off_topic if e.get("hallucination")) / len(off_topic)
        if off_topic else 0.0
    )
    lang_accuracy = (
        sum(1 for e in tamil_qs if e.get("language_ok")) / len(tamil_qs)
        if tamil_qs else 0.0
    )
    actionability = (
        sum(1 for e in non_off if e.get("actionable")) / len(non_off)
        if non_off else 0.0
    )
    gt_evals = [e for e in evals if e.get("ground_truth_facts_covered") is not None]
    mean_gt_coverage = (
        sum(e["ground_truth_facts_covered"] for e in gt_evals) / len(gt_evals)
        if gt_evals else None
    )

    checks = [
        ("Citation rate", citation_rate, CITATION_RATE_TARGET, True),
        ("Hallucination rate", hallucination_rate, HALLUCINATION_RATE_MAX, False),
        ("Language accuracy", lang_accuracy, LANGUAGE_ACCURACY_TARGET, True),
        ("Actionability", actionability, ACTIONABILITY_TARGET, True),
    ]

    print(f"\n{sep}")
    print("  UZHAVAN AI LLM Response Quality")
    print(f"  Citation domains: {', '.join(citation_domains)}")
    print(sep)

    for name, value, target, higher_is_better in checks:
        ok = value >= target if higher_is_better else value <= target
        status = "✅" if ok else "❌"
        dir_label = "≥" if higher_is_better else "≤"
        print(f"  {status}  {name:<25} {value * 100:.1f}%  (target: {dir_label}{target * 100:.0f}%)")

    if mean_gt_coverage is not None:
        print(f"\n  Ground truth coverage: {mean_gt_coverage * 100:.1f}%  (advisory Qs)")

    errors = [e for e in evals if e.get("error")]
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors:
            print(f"    [{e['question_id']}] {e['error'][:80]}")
    print(sep)

    # Detail for hallucinated off-topic responses
    hallucinated = [e for e in off_topic if e.get("hallucination")]
    if hallucinated:
        print("\n  ⚠️  Hallucinated off-topic responses:")
        for e in hallucinated:
            print(f"    [{e['question_id']}] — answer was generated instead of fallback")


def main() -> None:
    parser = argparse.ArgumentParser(description="UZHAVAN AI LLM response evaluator")
    parser.add_argument("--results", default="evaluation/results/benchmark_latest.json")
    parser.add_argument("--ground-truth", default="evaluation/ground_truth.json")
    parser.add_argument(
        "--citation-domains",
        default=",".join(DEFAULT_CITATION_DOMAINS),
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        sys.exit(f"Results file not found: {results_path}")

    gt_path = Path(args.ground_truth)
    if not gt_path.exists():
        sys.exit(f"Ground truth file not found: {gt_path}")

    report = json.loads(results_path.read_text())
    gt_data = json.loads(gt_path.read_text())
    gt_map: dict[str, dict[str, Any]] = {
        item["question_id"]: item for item in gt_data["ground_truth"]
    }

    citation_domains = [d.strip() for d in args.citation_domains.split(",") if d.strip()]
    raw_results: list[dict[str, Any]] = report.get("results", [])

    print(f"Evaluating {len(raw_results)} responses from {results_path.name} …")
    evals = [evaluate_result(r, gt_map, citation_domains) for r in raw_results]
    print_summary(evals, citation_domains)


if __name__ == "__main__":
    main()
