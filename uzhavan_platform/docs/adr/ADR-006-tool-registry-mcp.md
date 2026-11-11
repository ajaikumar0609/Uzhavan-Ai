# ADR-006 — Dynamic Tool Registry with MCP Compatibility

**Status:** Proposed
**Date:** 2026-07-01
**Deciders:** Architecture Agent, AI Agent, Master Agent
**Feature Pack:** FP-002 — AI Orchestrator & Conversation Platform

---

## Context

The UZHAVAN AI platform will eventually support 10+ tools: RAG, Weather, Disease, Market, Schemes, Satellite, Memory, IoT, Drone, GIS. The initial FP-002 draft hardcoded tools inside the LangGraph graph:

```python
tools = [rag_tool, weather_tool, disease_tool]
workflow.add_node("tools", run_tools)
```

This creates problems:
1. Adding a new tool requires editing the graph, the node, and the tool list
2. Feature-flagging a tool requires conditional imports scattered across files
3. No single place to see what tools exist and their capabilities
4. Future MCP integration (government APIs, IoT gateways) would require redesigning the orchestration layer

Additionally, the Model Context Protocol (MCP) is becoming the emerging standard for AI tool interoperability. Not designing for it now means a costly rewrite when government agencies or third-party providers offer MCP-compatible services.

---

## Decision

**Build a dynamic Tool Registry at `backend/tools/registry.py` that:**

1. Accepts tool registration at startup (or import time)
2. Exposes `list_enabled()` filtered by feature flags
3. Stores rich `ToolDefinition` metadata per tool
4. Exposes `as_mcp_manifest()` returning MCP-compatible JSON
5. Makes adding a new tool a 3-step process: create file, register, add flag

### ToolDefinition schema
```
name:            str           # "weather"
display_name:    str           # "Weather Tool"
description:     str           # used by PlanningGraph for selection reasoning
version:         str           # semver: "1.0.0"
permissions:     list[str]     # [] | ["location", "farmer_data", "financial"]
timeout_s:       int           # seconds before tool is considered failed
retry:           int           # automatic retries on timeout/error
input_schema:    dict          # JSON Schema for tool input
output_schema:   dict          # JSON Schema for tool output
mcp_compatible:  bool          # can this tool be exposed via MCP
enabled:         bool          # read from feature_flags at registration
```

### Registration pattern
```
# In backend/tools/weather.py:
TOOL_DEFINITION = ToolDefinition(
    name="weather",
    description="Get current weather and 7-day forecast for a Tamil Nadu district",
    version="1.0.0",
    timeout_s=5,
    retry=2,
    mcp_compatible=True,
    ...
)

async def run(payload: dict) -> dict:
    ...

# In backend/tools/registry.py:
from backend.tools import weather
registry.register(weather.TOOL_DEFINITION, weather.run)
```

### Adding a new tool (plug-and-play)
1. Create `backend/tools/new_tool.py` with `TOOL_DEFINITION` and `async def run()`
2. Add `registry.register(new_tool.TOOL_DEFINITION, new_tool.run)` to registry.py
3. Add `ENABLE_NEWTOOL=False` to feature_flags.py

**No changes to any graph file.**

### MCP compatibility
When `ENABLE_MCP=True` (Phase 4):
- `GET /mcp/manifest` returns `registry.as_mcp_manifest()`
- Any MCP-compatible client (government portal, third-party AI) can discover and call tools
- Incoming MCP tool requests are routed through the same registry

---

## Alternatives Considered

### Alternative A: LangChain tool decorators
```python
@tool
def weather_tool(district: str) -> str:
    ...
```
**Rejected:** LangChain tools lack versioning, permissions, timeout metadata, and MCP compatibility surface. Tying tool definitions to LangChain primitives makes future migration harder.

### Alternative B: Hardcoded tool list in graph
```python
TOOLS = [weather_tool, rag_tool, disease_tool]
```
**Rejected:** Rejected in context above. Every new tool requires graph edits.

### Alternative C: Tool discovery via Python package entry points
Tools register themselves via `setup.cfg` `[options.entry_points]`.
**Rejected:** Overcomplicated for a monorepo. Entry points are designed for separately-installed packages. The registry pattern achieves the same discovery with less infrastructure.

### Alternative D: Full MCP server from day one
Build UZHAVAN as an MCP server: every tool exposed over SSE from the start.
**Rejected:** MCP adds network hop and protocol overhead for internal tools. Better to design the interface for MCP compatibility without the protocol overhead until external consumers exist. `as_mcp_manifest()` is the bridge.

---

## MCP Compatibility Design

### Why design for MCP now
- MCP is the emerging standard for AI tool interoperability (Anthropic, OpenAI, Google adopting)
- Tamil Nadu government systems will increasingly expose APIs as MCP servers
- ICAR (Indian Council of Agricultural Research) and NIC (National Informatics Centre) may expose crop and soil data via MCP
- Designing ToolDefinition to match MCP's tool descriptor now costs nothing; retrofitting later is expensive

### Compatibility surface
```
ToolDefinition fields → MCP tool descriptor mapping:
  name         → name
  description  → description
  input_schema → inputSchema (JSON Schema)
```

`as_mcp_manifest()` iterates `list_enabled()` and produces:
```json
{
  "tools": [
    {
      "name": "rag",
      "description": "...",
      "inputSchema": { ... }
    }
  ]
}
```

### Consuming external MCP servers (Phase 4+)
The registry also supports external tools:
```
registry.register_mcp_server(
    url="https://agridata.tnau.ac.in/mcp",
    tools=["soil_data", "crop_calendar"]
)
```
These appear in `list_enabled()` exactly like internal tools — the graph never knows the difference.

---

## Consequences

### Positive
- New tool = 3 steps, zero graph changes
- Feature flags centralized: `feature_flags.py` is the single source of truth for what's active
- MCP manifest available without any additional work when needed
- Tool metadata (timeout, retry, permissions) enforced consistently
- PlanningGraph can use tool descriptions for intelligent selection (future: LLM-based tool selection)

### Negative
- Additional indirection: tool calls go through registry rather than direct import
- Tool registration must happen at startup — import order matters
- `as_mcp_manifest()` must be kept in sync with actual tool capabilities

### Mitigations
- `backend/tools/registry.py` is the single import; all tool files import there
- `test_tool_registry.py` validates registration and MCP manifest schema at test time
- ToolDefinition's `input_schema` and `output_schema` are JSON Schema — can be validated programmatically

---

## Review

| Reviewer | Status | Notes |
|----------|--------|-------|
| Architecture Agent | Proposed | |
| AI Agent | Pending | Must confirm registry pattern compatible with LangGraph PlanningGraph |
| Master Agent | Pending | |
