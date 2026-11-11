# ADR-007 — In-Process Event Bus for Tool Execution

**Status:** Proposed
**Date:** 2026-07-01
**Deciders:** Architecture Agent, AI Agent, Master Agent
**Feature Pack:** FP-002 — AI Orchestrator & Conversation Platform

---

## Context

The ToolExecutionGraph must run multiple tools in parallel (RAG, Weather, Disease, Schemes) and collect all results before passing to ContextBuilder. Two approaches exist:

**Direct call:**
```python
rag_result, weather_result = await asyncio.gather(rag_tool(q), weather_tool(d))
```

**Event bus:**
```python
bus.publish(ToolRequestEvent(tool="rag", payload=...))
bus.publish(ToolRequestEvent(tool="weather", payload=...))
results = await bus.wait_all(timeout_s=5)
```

The direct call is simpler now but creates tight coupling: the graph directly imports and calls each tool. When Satellite, IoT, and Drone tools are added in Phase 3+, each addition means editing the graph.

---

## Decision

**Build a lightweight in-process Event Bus for tool execution.**

V0.3: `asyncio.Queue`-based, fully in-process. Interface designed to be swapped for Redis Pub/Sub or RabbitMQ without changing any graph code.

### Interface
```
EventBus:
  publish(event: ToolRequestEvent) → None
  subscribe(tool_name: str, handler: Callable) → None
  wait_all(timeout_s: int) → list[ToolResultEvent]

ToolRequestEvent:
  event_id:   str (uuid4)
  tool_name:  str
  payload:    dict
  trace_id:   str

ToolResultEvent:
  event_id:   str
  tool_name:  str
  result:     dict | None
  error:      str | None
  duration_ms: int
```

### How it works (V0.3)
1. Tools subscribe at startup: `bus.subscribe("rag", rag_tool.run)`
2. PlanningGraph decides which tools to call (from ToolRegistry)
3. ToolExecutionGraph publishes one `ToolRequestEvent` per planned tool
4. Each subscribed handler is called via asyncio.gather
5. `wait_all()` collects all ToolResultEvents with timeout enforcement
6. Results written to `ConversationState.tool_results`

### Future migration path (Phase 3+)
- Swap the asyncio.Queue internals for Redis Pub/Sub
- Satellite Agent and IoT Agent subscribe from their own processes
- `bus.publish()` and `bus.wait_all()` signatures unchanged
- ToolExecutionGraph code unchanged

---

## Alternatives Considered

### Alternative A: Direct asyncio.gather
```python
tasks = [registry.get(name)(payload) for name in state.tools_planned]
results = await asyncio.gather(*tasks, return_exceptions=True)
```
**Partially rejected:** Works for V0.3 and is simpler. However, the graph directly calls tools — adding a tool in Phase 3 requires editing the graph. Event bus preserves the plug-and-play property of the ToolRegistry. Decision: wrap `asyncio.gather` inside the EventBus V0.3 implementation — same performance, future-safe interface.

### Alternative B: Redis Pub/Sub from day one
```python
await redis.publish("tool:rag", json.dumps(payload))
result = await redis.subscribe("result:rag:{trace_id}")
```
**Rejected for V0.3:** Adds Redis round-trip latency (~1–5 ms per tool per message). Requires Redis to be running for every local dev session. Overkill when all tools run in the same process. The V0.3 in-process bus achieves the same interface at zero latency.

### Alternative C: LangGraph parallel nodes
Use LangGraph's built-in fan-out to run nodes in parallel:
```python
workflow.add_node("rag", rag_node)
workflow.add_node("weather", weather_node)
workflow.add_edge(START, ["rag", "weather"])  # parallel fan-out
```
**Partially rejected:** LangGraph supports parallel edges, which is appealing. However, this hardcodes tool nodes into the graph structure — adding a tool means editing the graph's edges, not just the registry. The EventBus keeps the graph's ToolExecutionGraph node generic: it asks the registry what tools to run, publishes events, collects results. New tools never touch the graph.

---

## Consequences

### Positive
- ToolExecutionGraph has no imports of individual tool files — only the registry and bus
- Timeout enforcement per tool (via `wait_all(timeout_s)`) prevents slow tools from blocking
- Error isolation: one tool failure (error in ToolResultEvent) does not crash the graph
- Future migration to distributed bus is transparent to all graph code
- ToolResultEvent carries `duration_ms` — feeds directly into request_traces observability

### Negative
- Subscription setup at startup adds a small initialization step
- Debugging: asyncio event buses can be harder to trace than direct calls
- `wait_all()` with a global timeout means faster tools wait for slower ones

### Mitigations
- `trace_id` propagated through every event — traceable end-to-end in logs
- Per-tool timeout in `ToolDefinition.timeout_s` — individual tool timeouts applied inside handler
- `wait_all()` returns partial results if some tools timeout — VerificationGraph adds warnings

---

## Review

| Reviewer | Status | Notes |
|----------|--------|-------|
| Architecture Agent | Proposed | |
| AI Agent | Pending | Must confirm asyncio event bus pattern compatible with Ollama async streaming |
| Master Agent | Pending | |
