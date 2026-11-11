# RAG Debugging Playbook

**Last updated:** 2026-07-01
**Relevant files:** `backend/knowledge/rag/engine.py`, `data_pipeline/embed_chunks.py`, `data_pipeline/normalize_tnau.py`

---

## Collection Health Check

```bash
# Quick stats
python3 data_pipeline/embed_chunks.py --stats

# Expected output:
# Collection: tnau_knowledge
# Total chunks: 4,200
# Categories: {'Plant Protection': 1200, 'Crop Management': 900, ...}
# Crops: {'Rice': 800, 'Cotton': 400, ...}
# Languages: {'English': 3800, 'Tamil': 400}
# Embedding model: BAAI/bge-m3

# Direct ChromaDB inspection
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='rag/chroma')
col = client.get_collection('tnau_knowledge')
print('Total chunks:', col.count())

# Sample 5 random chunks
sample = col.get(limit=5, include=['documents', 'metadatas'])
for doc, meta in zip(sample['documents'], sample['metadatas']):
    print(f'  [{meta.get(\"category\")}] [{meta.get(\"crop\")}] {doc[:100]}...')
"
```

---

## Test Retrieval Directly

```bash
# Basic retrieval test
python3 -c "
from backend.knowledge.rag.engine import retrieve

chunks = retrieve('BPH in rice treatment', top_k=6)
for c in chunks:
    print(f'{c.score:.3f} | {c.category} | {c.crop} | {c.content[:120]}')
"

# Tamil query test (critical — bge-m3 should handle this)
python3 -c "
from backend.knowledge.rag.engine import retrieve

chunks = retrieve('நெல்லில் பழுப்பு தாவல் பூச்சி', top_k=6)
print(f'Results for Tamil BPH query: {len(chunks)} chunks')
for c in chunks:
    print(f'  {c.score:.3f} | {c.category} | {c.content[:100]}')
"

# With filters
python3 -c "
from backend.knowledge.rag.engine import retrieve

chunks = retrieve('irrigation timing', top_k=6, crop_filter='Rice', district='Thanjavur')
print(f'Filtered results: {len(chunks)}')
for c in chunks:
    print(f'  {c.score:.3f} | crop:{c.crop} | {c.content[:100]}')
"
```

---

## Check Score Distribution

Low scores on valid queries indicate embedding quality issues or content gaps.

```bash
python3 -c "
from backend.knowledge.rag.engine import retrieve

test_queries = [
    'rice blast fungal disease treatment',
    'BPH brown planthopper control',
    'paddy irrigation schedule tillering',
    'cotton bollworm management',
    'banana leaf spot disease',
    # Tamil queries
    'நெல்லில் இலைத்தீ நோய்',
    'வாழையில் இலைப்புள்ளி நோய்',
]

print('Query → Top Score | Avg Score | Chunks Above 0.35')
print('-' * 65)
for q in test_queries:
    chunks = retrieve(q, top_k=10)
    if chunks:
        scores = [c.score for c in chunks]
        above_threshold = sum(1 for s in scores if s >= 0.35)
        print(f'{q[:40]:40s} | {scores[0]:.3f} | {sum(scores)/len(scores):.3f} | {above_threshold}/10')
    else:
        print(f'{q[:40]:40s} | NO RESULTS')
"
```

---

## Common Issues and Fixes

### Issue: Zero results for valid query

```bash
# Check 1: Is collection populated?
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='rag/chroma')
col = c.get_collection('tnau_knowledge')
print('Count:', col.count())
"

# Check 2: Is the query embedding working?
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
emb = model.encode('rice pest treatment')
print('Embedding shape:', emb.shape)   # Should be (1024,)
print('Embedding sample:', emb[:5])    # Should be non-zero floats
"

# Fix: Re-embed if collection is empty
python3 data_pipeline/embed_chunks.py --reset
```

### Issue: Wrong language chunks returned for Tamil query

```bash
# Test Tamil vs English retrieval
python3 -c "
from backend.knowledge.rag.engine import retrieve

# bge-m3 should return the same content for equivalent Tamil and English queries
en_chunks = retrieve('BPH brown planthopper rice', top_k=3)
ta_chunks = retrieve('நெல்லில் பழுப்பு தாவல் பூச்சி', top_k=3)

print('English query scores:', [c.score for c in en_chunks])
print('Tamil query scores:  ', [c.score for c in ta_chunks])
# Tamil scores should be comparable (within 0.10 of English scores)
# If Tamil scores are much lower, bge-m3 may not have loaded correctly
"

# Verify model is BAAI/bge-m3 (multilingual), not a monolingual model
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
print('Model name:', model._model_card_data.base_model if hasattr(model, '_model_card_data') else 'bge-m3 loaded')
print('Embedding dimension:', model.get_sentence_embedding_dimension())
# Should be 1024
"
```

### Issue: Low scores for valid questions (all below 0.35)

Causes: (1) Content not in knowledge base, (2) Chunk size mismatch, (3) Embedding model changed.

```bash
# Check if TNAU content actually covers the topic
grep -r "BPH\|brown planthopper" data_pipeline/rag/chunks/chunks.jsonl | head -5

# If content exists in chunks.jsonl but scores are low:
# The embeddings may have been created with a different model
# Full re-embed is required
python3 data_pipeline/embed_chunks.py --reset

# If content is NOT in chunks.jsonl:
# Need to add it via the TNAU crawler + normalize pipeline
```

### Issue: Crop filter not working (returns results for wrong crop)

```bash
# Test filter isolation
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='rag/chroma')
col = client.get_collection('tnau_knowledge')

results = col.query(
    query_texts=['pest management'],
    n_results=5,
    where={'crop': 'Cotton'},    # should only return Cotton chunks
    include=['documents', 'metadatas']
)
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f\"Crop: {meta['crop']} | {doc[:100]}\")
# If non-Cotton chunks appear: metadata 'crop' field is not set during embedding
"

# Check chunk metadata in chunks.jsonl
python3 -c "
import json
with open('data_pipeline/rag/chunks/chunks.jsonl') as f:
    for i, line in enumerate(f):
        chunk = json.loads(line)
        if i < 3:
            print('Keys:', list(chunk.keys()))
            print('crop field:', chunk.get('crop', 'MISSING'))
"
```

---

## Re-Embedding Procedure

### When to re-embed

- bge-m3 model version changed
- Significant new TNAU content added (> 100 new documents)
- Score distribution check shows systematic degradation
- Full ChromaDB reset after corruption

### Incremental re-embed (new content only)

```bash
# Add new chunks to chunks.jsonl (via normalize_tnau.py)
python3 data_pipeline/normalize_tnau.py \
  --knowledge-base tnau_crawler/knowledge_base \
  --output-dir data_pipeline/rag/chunks

# Embed only new chunks (filter_new() skips existing IDs)
python3 data_pipeline/embed_chunks.py

# Verify
python3 data_pipeline/embed_chunks.py --stats
```

### Full reset (model change or corruption)

```bash
# Backup first
tar -czf backups/chroma-before-reset-$(date +%Y%m%d).tar.gz rag/chroma/

# Reset and re-embed everything
python3 data_pipeline/embed_chunks.py --reset

# This will:
# 1. Delete the existing ChromaDB collection
# 2. Re-embed all chunks in chunks.jsonl
# 3. Batch size: 64 (configurable via --batch-size)
# Estimated time: ~30 minutes for 4,000 chunks on CPU

# Verify
python3 data_pipeline/embed_chunks.py --stats
```

---

## Adding New TNAU Content

```bash
# 1. Run TNAU crawler to fetch new pages
cd data_pipeline/crawler
python3 crawler.py --category pest_management --output ../tnau_crawler/knowledge_base/

# 2. Normalize crawler output into chunks
python3 data_pipeline/normalize_tnau.py \
  --knowledge-base data_pipeline/tnau_crawler/knowledge_base \
  --output-dir data_pipeline/rag/chunks \
  --export-parquet  # optional: also export as parquet for analysis

# 3. Check what new chunks were generated
python3 -c "
import json
chunks = [json.loads(l) for l in open('data_pipeline/rag/chunks/chunks.jsonl')]
print(f'Total chunks: {len(chunks)}')
# Find newest by checking IDs or timestamps in metadata
"

# 4. Embed new chunks (incremental)
python3 data_pipeline/embed_chunks.py

# 5. Test that new content is retrievable
python3 -c "
from backend.knowledge.rag.engine import retrieve
# Test a query that should hit the new content
chunks = retrieve('new topic from added content', top_k=3)
for c in chunks:
    print(c.score, c.content[:100])
"
```

---

## ChromaDB Collection Inspect Commands

```bash
# List all collections
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='rag/chroma')
print('Collections:', [col.name for col in c.list_collections()])
"

# Get all unique categories in collection
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='rag/chroma')
col = c.get_collection('tnau_knowledge')
all_meta = col.get(include=['metadatas'])
categories = {}
for m in all_meta['metadatas']:
    cat = m.get('category', 'unknown')
    categories[cat] = categories.get(cat, 0) + 1
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'{count:6d}  {cat}')
"

# Get all unique crops
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='rag/chroma')
col = c.get_collection('tnau_knowledge')
all_meta = col.get(include=['metadatas'])
crops = {}
for m in all_meta['metadatas']:
    crop = m.get('crop', 'general')
    crops[crop] = crops.get(crop, 0) + 1
for crop, count in sorted(crops.items(), key=lambda x: -x[1])[:20]:
    print(f'{count:6d}  {crop}')
"

# Find chunks by source URL
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='rag/chroma')
col = c.get_collection('tnau_knowledge')
results = col.get(
    where={'source_url': {'\\$contains': 'pest'}},
    include=['documents', 'metadatas'],
    limit=5
)
for doc, meta in zip(results['documents'], results['metadatas']):
    print(meta['source_url'])
    print(doc[:100])
    print()
"
```
