# ADR-001 — Use LangGraph for LLM Orchestration

**Date:** 2026-06-20
**Status:** ACCEPTED
**Deciders:** Master Agent, Solution Architect Agent

---

## Context
UZHAVAN AI requires an LLM that calls multiple tools (knowledge, weather, market, disease) in a conditional sequence based on farmer intent. A simple chain (LangChain Expression Language) would hardcode the tool sequence. A pure LLM with function calling has no retry/branching logic.

## Decision
Use **LangGraph** for multi-step tool orchestration with conditional routing.

## Rationale
LangGraph provides:
- State machine approach — each node is a discrete tool call
- Conditional edges — route to weather tool OR knowledge tool based on intent
- Built-in retry logic per node
- Streaming support
- Directly integrates with LangChain tools

## Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|-----------------|
| LangChain LCEL | Simple, fast | No conditional branching; linear only | Intent routing requires branching |
| CrewAI | Multi-agent framework | Heavy; agents talk to each other; slower; overkill | Our tools don't need peer communication |
| AutoGen | Microsoft; flexible | Complex setup; harder to control tool scope | Less control over when tools are called |
| Raw function calling | Full control | Must implement state machine manually | LangGraph already provides this |

## Consequences

**Positive:**
- Intent-conditional tool routing without custom state machine code
- Nodes are independently testable
- Easy to add new tools (weather, satellite) as new nodes

**Negative:**
- LangGraph learning curve for new contributors
- Additional dependency (langchain + langgraph)
- Graph definition can grow complex

**Risks:**
- LangGraph API changes between minor versions — pin version
- Mitigation: pin `langgraph>=0.1.0,<0.2.0` in requirements

## Review Date
Reconsider if LangGraph adds breaking changes in v0.2 or if a simpler routing pattern emerges in 6 months.
