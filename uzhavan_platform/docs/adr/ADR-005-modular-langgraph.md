# ADR-005 — Modular LangGraph Architecture

**Status:** Proposed
**Date:** 2026-07-01
**Deciders:** Architecture Agent, AI Agent, Master Agent
**Feature Pack:** FP-002 — AI Orchestrator & Conversation Platform

---

## Context

The initial FP-002 planning document specified a single LangGraph graph with sequential nodes:
```
intent → rag_tool → guardrail → qwen3 → response_format
```

This works for a chat MVP but creates problems for a service intended to run for 3+ years and support 10+ tools, multiple interfaces, and multi-agent orchestration:

1. A monolithic graph grows in one file — adding a tool means modifying the graph itself
2. Intent classification, tool selection, context aggregation, and response formatting are distinct concerns that should be independently testable and replaceable
3. Future interfaces (voice, WhatsApp) need the same orchestration logic without the chat-specific parts
4. A single graph cannot easily support parallel tool execution that scales to 10+ tools

---

## Decision

**Build the LangGraph orchestration as 7 independent subgraphs, each in its own file, composed by a root ConversationGraph.**

```
backend/advisory/graph/
  conversation.py    ← ConversationGraph (root — wires subgraphs)
  intent.py          ← IntentGraph
  planner.py         ← PlanningGraph
  retrieval.py       ← RetrievalGraph (used by RAGTool)
  tools.py           ← ToolExecutionGraph
  verification.py    ← VerificationGraph
  response.py        ← ResponseGraph
```

Each subgraph:
- Takes `ConversationState` as input
- Returns updated `ConversationState`
- Has no knowledge of other subgraphs
- Is independently testable with a minimal state fixture

---

## Alternatives Considered

### Alternative A: Single monolithic graph
```python
# graph.py
workflow = StateGraph(ConversationState)
workflow.add_node("intent", classify_intent)
workflow.add_node("rag", run_rag)
workflow.add_node("weather", run_weather)
workflow.add_node("verify", verify)
workflow.add_node("llm", run_llm)
workflow.add_node("response", format_response)
```
**Rejected:** Violates single responsibility. Adding a tool means editing the graph. Cannot test verification in isolation. Grows to 500+ lines.

### Alternative B: Function calls without LangGraph
```python
async def orchestrate(message, state):
    intent = classify(message)
    chunks = await rag(message)
    answer = await llm(chunks)
    return format(answer)
```
**Rejected:** No built-in state management, no conditional routing, no retry logic, no graph visualization. LangGraph ADR-001 already decided in favour of LangGraph — reopening this would require a new ADR.

### Alternative C: Separate LangGraph agents (multi-agent)
Each tool as a separate LangGraph agent communicating via messages.
**Rejected for V0.3:** Too much overhead for current scale. Event bus (ADR-007) achieves parallel execution with simpler design. Multi-agent architecture is Phase 3+ consideration.

### Alternative D: LangChain LCEL pipeline (not LangGraph)
```python
chain = intent_runnable | rag_runnable | llm_runnable
```
**Rejected:** No state object, no conditional branching (verification gate), no parallel execution support. ADR-001 already chose LangGraph for exactly these reasons.

---

## Consequences

### Positive
- Each subgraph is independently testable: `test_verification_graph.py` tests only verification
- Adding a new tool requires no changes to existing graphs — only PlanningGraph's tool selection logic
- Future interface (voice, WhatsApp): reuse IntentGraph + VerificationGraph + ResponseGraph; swap ToolExecutionGraph
- LangGraph's built-in graph visualization works per-subgraph, making debugging tractable
- Smaller files: each graph file targets ~100–150 lines

### Negative
- More files to navigate: 7 files instead of 1
- State object must be passed through all subgraphs — adds boilerplate
- Subgraph composition in LangGraph requires careful wiring in conversation.py

### Mitigations
- `graph/__init__.py` exports a single `ConversationGraph` — callers import one object
- `CONVERSATION-SERVICE.md` documents the full flow — developers know where to look
- `ConversationState` dataclass in `state.py` is the single source of truth for state shape

---

## Review

| Reviewer | Status | Notes |
|----------|--------|-------|
| Architecture Agent | Proposed | |
| AI Agent | Pending | Must confirm LangGraph subgraph composition is supported |
| Master Agent | Pending | |
