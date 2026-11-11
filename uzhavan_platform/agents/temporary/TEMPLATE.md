# Temporary Agent Template

Copy this file and fill in the blanks when spawning a temporary agent.
Delete the agent folder when the task is complete.

---

# [Agent Name] — Temporary Agent

## Task
[One sentence: what this agent must produce]

## Scope
- IN: [what it owns]
- OUT: [what it must NOT touch]

## Inputs
- [file or data it receives]

## Outputs
- [file or data it must produce]

## Acceptance Criteria
- [ ] [verifiable condition 1]
- [ ] [verifiable condition 2]

## Self-Destruct
This agent is retired when all acceptance criteria are met.
Delete `agents/temporary/[agent-name]/` after merge.

---

## Known Temporary Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| Dataset Agent | TNAU crawl + normalization | RETIRED (complete) |
| Migration Agent | Schema upgrades | Active when needed |
| Animation Agent | Flutter UI animations | Not yet created |
| Bug Fix Agent | Debug specific issues | Create as needed |
| Performance Agent | Query optimization | Create as needed |
| Security Agent | Pre-production audit | Create before v1.0 |
