#!/usr/bin/env python3
"""
UZHAVAN AI — Embedding Pipeline
================================
Reads RAG chunks from rag/chunks/chunks.jsonl (output of normalize_tnau.py)
and embeds them into ChromaDB for semantic retrieval.

Features:
  - Incremental: skips chunks already in ChromaDB (by chunk_id)
  - Batch embedding for speed
  - Crop + category metadata for filtered retrieval
  - Progress reporting

Usage:
  python embed_chunks.py
  python embed_chunks.py --chunks-file ../rag/chunks/chunks.jsonl
  python embed_chunks.py --reset     # wipe ChromaDB and re-embed everything
  python embed_chunks.py --dry-run   # count chunks without embedding

Requirements:
  pip install chromadb sentence-transformers tqdm
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("embed")

CHUNKS_FILE   = Path(__file__).parent.parent / "rag" / "chunks" / "chunks.jsonl"
CHROMA_PATH   = Path(__file__).parent.parent / "rag" / "chroma"
EMBED_MODEL   = "BAAI/bge-m3"
COLLECTION    = "tnau_knowledge"
BATCH_SIZE    = 64


# ─── LOAD ─────────────────────────────────────────────────────────────────────

def load_chunks(path: Path) -> list[dict]:
    if not path.exists():
        log.error(f"Chunks file not found: {path}")
        log.error("Run: python data_pipeline/normalize_tnau.py  first")
        sys.exit(1)

    chunks = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    log.info(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


def filter_new(chunks: list[dict], collection) -> list[dict]:
    if collection.count() == 0:
        return chunks
    existing_ids = set(collection.get(include=[])["ids"])
    new = [c for c in chunks if c["chunk_id"] not in existing_ids]
    log.info(f"{len(existing_ids)} already embedded; {len(new)} new chunks to embed")
    return new


# ─── EMBED ────────────────────────────────────────────────────────────────────

def batch_embed(texts: list[str], model) -> list[list[float]]:
    return model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
    ).tolist()


def embed_and_store(chunks: list[dict], collection, model):
    total = len(chunks)
    if total == 0:
        log.info("Nothing to embed — all chunks already in ChromaDB")
        return

    log.info(f"Embedding {total} chunks with model: {EMBED_MODEL}")

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i: i + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids         = [c["chunk_id"] for c in batch],
            embeddings  = embeddings,
            documents   = texts,
            metadatas   = [
                {
                    "chunk_id":   c["chunk_id"],
                    "source_url": c.get("source_url", ""),
                    "source_file":c.get("source_file", ""),
                    "title":      c.get("title", ""),
                    "category":   c.get("category", "General Agriculture"),
                    "crop":       c.get("crop", "General"),
                    "language":   c.get("language", "English"),
                    "chunk_index":str(c.get("chunk_index", 0)),
                    "word_count": str(c.get("word_count", 0)),
                }
                for c in batch
            ],
        )

        log.info(f"  Stored batch {i // BATCH_SIZE + 1} | "
                 f"{min(i + BATCH_SIZE, total)}/{total} chunks")

    log.info(f"Embedding complete. ChromaDB now has {collection.count()} total chunks.")


# ─── STATS ────────────────────────────────────────────────────────────────────

def print_stats(collection):
    count = collection.count()
    if count == 0:
        log.info("Collection is empty")
        return

    all_data = collection.get(include=["metadatas"])
    metas    = all_data["metadatas"]

    from collections import Counter
    cats   = Counter(m.get("category", "Unknown") for m in metas)
    crops  = Counter(m.get("crop", "Unknown") for m in metas)
    langs  = Counter(m.get("language", "Unknown") for m in metas)

    log.info(f"\n{'='*50}")
    log.info(f"ChromaDB Collection: {COLLECTION}")
    log.info(f"Total chunks: {count}")
    log.info(f"\nTop categories:")
    for cat, n in cats.most_common(10):
        log.info(f"  {n:5d}  {cat}")
    log.info(f"\nTop crops:")
    for crop, n in crops.most_common(10):
        log.info(f"  {n:5d}  {crop}")
    log.info(f"\nLanguages: {dict(langs)}")
    log.info("="*50)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UZHAVAN AI — Embedding Pipeline")
    parser.add_argument("--chunks-file", default=str(CHUNKS_FILE), help="Path to chunks.jsonl")
    parser.add_argument("--chroma-path", default=str(CHROMA_PATH), help="ChromaDB persistence directory")
    parser.add_argument("--model",       default=EMBED_MODEL,      help="Sentence-transformers model name")
    parser.add_argument("--reset",       action="store_true",       help="Delete collection and re-embed all")
    parser.add_argument("--dry-run",     action="store_true",       help="Count chunks only; do not embed")
    parser.add_argument("--stats",       action="store_true",       help="Print ChromaDB stats and exit")
    args = parser.parse_args()

    import chromadb
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(Path(args.chroma_path)))

    if args.reset:
        try:
            client.delete_collection(COLLECTION)
            log.info(f"Deleted collection '{COLLECTION}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name     = COLLECTION,
        metadata = {"hnsw:space": "cosine"},
    )

    if args.stats:
        print_stats(collection)
        return

    chunks = load_chunks(Path(args.chunks_file))

    if args.dry_run:
        new = filter_new(chunks, collection)
        log.info(f"DRY RUN — would embed {len(new)} new chunks ({len(chunks)} total)")
        return

    new_chunks = filter_new(chunks, collection)
    if not new_chunks:
        print_stats(collection)
        return

    log.info(f"Loading embedding model: {args.model}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)

    embed_and_store(new_chunks, collection, model)
    print_stats(collection)


if __name__ == "__main__":
    main()
