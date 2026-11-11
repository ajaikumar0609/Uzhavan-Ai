#!/bin/zsh
# Warm the LOCAL stack before a demo. Ops only: no app code, no data written.
#  1. loads qwen2.5:7b-instruct into Ollama and keeps it resident for 60 minutes
#  2. sends one throwaway English question through the backend so the bge-m3 embedder
#     and the Chroma index are loaded (the first real question is otherwise ~6 s slower)
# Note: each real answer resets Ollama's idle timer to its 5-minute default, so re-run this
# if the phone has been idle for more than ~5 minutes.
set -e
OLLAMA=${OLLAMA_URL:-http://127.0.0.1:11434}
API=${API_URL:-http://127.0.0.1:8000}
echo "Ollama: loading model..."
curl -s -m 120 "$OLLAMA/api/generate" -d '{"model":"qwen2.5:7b-instruct","prompt":"ok","stream":false,"keep_alive":"60m","options":{"num_predict":1}}' >/dev/null
ollama ps
echo "Backend: warming RAG + embedder..."
curl -s -m 180 -N "$API/conversation" -H 'Content-Type: application/json' \
  -d '{"question":"What is NPK fertilizer?","language":"English"}' | grep -c '^event: completed' | sed 's/^/completed events: /'
echo "Warm."
