# Prompt Debugging Playbook

**Last updated:** 2026-07-01
**Relevant files:** `backend/prompts/`, `backend/decision/prompt_builder.py`, `backend/decision/graph/`

---

## Enable Prompt Logging

By default, the full prompt sent to Qwen3 is not logged (it contains farmer input). Enable it only during debugging.

```bash
# Enable prompt logging (WARNING: logs contain farmer data — use only in dev/staging)
export LOG_PROMPTS=true
export LOG_LEVEL=DEBUG
docker compose restart decision

# Logs will show entries like:
# [PROMPT DEBUG] intent=advisory trace_id=abc123
# [SYSTEM] You are UZHAVAN AI...
# [CONTEXT] RAG chunks: ...
# [USER] நெல்லில் பழுப்பு...

# Disable after debugging
export LOG_PROMPTS=false
docker compose restart decision
```

---

## Inspect Retrieved Chunks for a Query

```bash
# Query ChromaDB directly to see what the RAG tool would return
python3 -c "
from backend.knowledge.rag.engine import retrieve

query = 'BPH in rice treatment'    # or paste the Tamil query
chunks = retrieve(query, top_k=6)
for i, c in enumerate(chunks):
    print(f'--- Chunk {i+1} (score: {c.score:.3f}) ---')
    print(f'Title: {c.title}')
    print(f'Category: {c.category}')
    print(f'URL: {c.source_url}')
    print(f'Content: {c.content[:200]}')
    print()
"

# With crop filter:
python3 -c "
from backend.knowledge.rag.engine import retrieve
chunks = retrieve('irrigation timing', top_k=6, crop_filter='Rice', district='Thanjavur')
for c in chunks:
    print(f'{c.score:.3f} | {c.category} | {c.content[:100]}')
"
```

---

## Test a Prompt Template in Isolation

```bash
# Test PromptBuilder without running the full LangGraph
python3 -c "
from backend.decision.prompt_builder import PromptBuilder
from backend.shared.models import ConversationState

# Minimal state for testing
builder = PromptBuilder()
prompt = builder.build(
    intent='advisory',
    context={
        'farmer_profile': {'name': 'Murugan', 'district': 'Thanjavur', 'primary_crop': 'Rice'},
        'rag_content': 'BPH (brown planthopper) control: apply Buprofezin 25 SC @ 1 ml/L water...',
        'weather_summary': None,
        'language': 'Tamil',
        'entities': {'crop': 'Rice', 'pest': 'BPH'}
    },
    language='Tamil'
)
print('=== SYSTEM PROMPT ===')
print(prompt['system'])
print()
print('=== USER MESSAGE ===')
print(prompt['user'])
"
```

---

## Common Prompt Failures and Fixes

### Failure: Generic response (no personalization)

**Symptom:** AI responds with "Apply fertilizer as recommended" without specifics.

**Diagnosis:**
```bash
# Check if farmer profile is being loaded into context
python3 -c "
from backend.decision.context_builder import ContextBuilder
# Test with a known farmer_id
ctx = ContextBuilder().build_minimal(farmer_id='<test-farmer-id>')
print(ctx)
"
# If farmer_profile is None or empty → DB lookup is failing or farm_id not passed
```

**Fix:** Ensure `farm_id` is passed in the request body. If farmer hasn't registered a farm, context builder falls back to district-only context — acceptable. Verify `ConversationState.farm_id` is populated correctly in `backend/conversation/main.py`.

---

### Failure: Wrong language (English response to Tamil question)

**Symptom:** Tamil input, English output.

**Diagnosis:**
```bash
# Check language detection in IntentGraph
python3 -c "
from backend.decision.graph.intent import detect_language
print(detect_language('நெல்லில் பழுப்பு தாவல் பூச்சி வந்தால் என்ன செய்வது?'))
# Should return 'Tamil'
"

# Check prompt template for language instruction
cat backend/prompts/advisory.md | grep -i 'language\|tamil\|respond'
```

**Fix:** The language instruction in `prompts/system.md` must include:
```
Reply in {language}. If the question is in Tamil, respond entirely in Tamil.
Do not mix English and Tamil unless the farmer uses both.
```
Edit `backend/prompts/system.md` — no redeploy needed, file is read at request time.

---

### Failure: Missing source citations

**Symptom:** AI answer has no source URL or confidence score.

**Diagnosis:**
```bash
# Check if ResponseGraph is populating sources from ConversationState
# Add temporary log in response.py:
# logging.debug(f"Sources in state: {state.sources}")

# Check if VerificationGraph is passing sources through
python3 -c "
from backend.knowledge.rag.engine import retrieve
chunks = retrieve('BPH rice', top_k=6)
print('Scores:', [c.score for c in chunks])
print('Above 0.35:', [c.score for c in chunks if c.score >= 0.35])
"
# If all scores < 0.35 → chunks are being filtered → sources list is empty
```

**Fix:** If retrieval scores are consistently low for valid queries, the embedding model or query phrasing may have drifted. Run `evaluation/rag_eval.py` to quantify. Temporary: lower score threshold to 0.30 in `feature_flags.py` (document this as a workaround, fix retrieval quality).

---

### Failure: Hallucination (LLM inventing agricultural facts)

**Symptom:** Response contains specific numbers, dosages, or product names not present in retrieved chunks.

**Diagnosis:**
```bash
# Verify VerificationGraph ran and chunks_retrieved > 0
docker compose exec postgres psql -U uzhavan -c "
SELECT trace_id, chunks_retrieved, confidence
FROM request_traces
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC LIMIT 5;
"

# If chunks_retrieved > 0 but hallucination occurred:
# The LLM is ignoring retrieved context
# Check system prompt for clear grounding instruction
grep -A5 "ONLY use" backend/prompts/system.md
```

**Fix:** Strengthen grounding instruction in `backend/prompts/system.md`:
```markdown
CRITICAL: Every agricultural fact you state MUST come from the provided knowledge chunks.
If the chunks do not mention a specific dosage, product, or timing — do not state one.
Say: "உங்கள் BAO-ஐ தொடர்பு கொள்ளுங்கள்" instead.
```

---

## Update a Prompt Template

Prompt templates live in `backend/prompts/*.md`. Changes take effect immediately — no redeploy needed.

```bash
# Edit the template
nano backend/prompts/advisory.md

# Test the change immediately (no restart needed)
python3 -c "
from backend.decision.prompt_builder import PromptBuilder
builder = PromptBuilder()
prompt = builder.build('advisory', {...test context...}, 'Tamil')
print(prompt['system'][:500])
"

# Run a manual chat test to verify
curl -s -N -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "நெல்லில் BPH வந்தால் என்ன செய்வது?", "language": "Tamil"}' \
  http://localhost:8002/chat

# Run LLM evaluation to ensure change doesn't regress accuracy
python3 evaluation/llm_eval.py --prompt-version new
```

---

## A/B Testing Prompts

```bash
# 1. Create variant prompt file
cp backend/prompts/advisory.md backend/prompts/advisory_v2.md
nano backend/prompts/advisory_v2.md

# 2. Run evaluation on both
python3 evaluation/llm_eval.py \
  --prompt backend/prompts/advisory.md \
  --output results/advisory_v1.json

python3 evaluation/llm_eval.py \
  --prompt backend/prompts/advisory_v2.md \
  --output results/advisory_v2.json

# 3. Compare results
python3 -c "
import json
v1 = json.load(open('results/advisory_v1.json'))
v2 = json.load(open('results/advisory_v2.json'))
print(f'v1 accuracy: {v1[\"accuracy\"]:.2%}, citation_rate: {v1[\"citation_rate\"]:.2%}')
print(f'v2 accuracy: {v2[\"accuracy\"]:.2%}, citation_rate: {v2[\"citation_rate\"]:.2%}')
"

# 4. If v2 wins on all metrics → replace advisory.md with advisory_v2.md
# Document the change in CHANGELOG.md
```

---

## Evaluate Response Quality with llm_eval.py

```bash
# Run full evaluation suite against ground truth
python3 evaluation/llm_eval.py

# Output includes:
# accuracy:       % of answers matching ground truth intent
# citation_rate:  % of answers with at least one source citation
# groundedness:   % of answers using only retrieved content (no hallucination)
# tool_usage:     % of requests using the correct tool for the intent
# avg_latency_ms: mean total_ms from request_traces

# Run on specific question categories
python3 evaluation/llm_eval.py --category irrigation
python3 evaluation/llm_eval.py --category pest_management
python3 evaluation/llm_eval.py --language Tamil

# Compare against baseline (stored in evaluation/baselines/)
python3 evaluation/llm_eval.py --compare-baseline v0.3
```

---

## Quick Reference: Prompt File → Intent

| File | Used when intent = |
|------|--------------------|
| `prompts/system.md` | Always (base system prompt) |
| `prompts/advisory.md` | advisory (crop guidance, pest, fertilizer) |
| `prompts/weather.md` | weather (irrigation, spray timing) |
| `prompts/disease.md` | disease (after disease tool returns result) |
| `prompts/market.md` | market (price queries) |
| `prompts/crop.md` | crop_recommendation |
| `prompts/scheme.md` | scheme (government schemes) |
