# Feature Pack Template (Framework v1.0)

Copy this file → rename to `FP-XXX-feature-name.md` → fill all 15 sections.
No implementation code until Planning gate passes. No merge until all 10 gates pass.

See `docs/FRAMEWORK.md` for the full engineering workflow.

---

# FP-XXX — [Feature Name]

**Status:** `PLANNING` | `IN PROGRESS` | `IN REVIEW` | `COMPLETE`
**Sprint:** Sprint-00X
**Milestone:** M-0X — [Milestone Name]
**Owner:** [Agent responsible for coordination]

---

## 1. Requirement
*What does this feature do? One paragraph, plain language.*

---

## 2. User Story
```
As a [Tamil Nadu farmer / agronomist / admin]
I want to [action]
So that [benefit to farmer]
```

---

## 3. Acceptance Criteria
All criteria must be binary (pass/fail). No "mostly works".

```
Given [context]
When  [action]
Then  [outcome]
```

- [ ] AC-1: ...
- [ ] AC-2: ...
- [ ] AC-3: ...

**Out of Scope (v1):**
- [explicitly deferred item]

---

## 4. API Contract
*Filled by Solution Architect Agent before implementation starts.*

```
POST /endpoint
Request:  { ... }
Response: { ... }
Errors:   400 / 422 / 503
```

---

## 5. Database Changes
*Filled by Database Agent.*

```
New tables:   [none / table names]
New columns:  [none / column names]
Migration:    00X_migration_name.sql
```

---

## 6. AI / RAG Changes
*Filled by AI Agent and/or RAG Agent.*

```
New tools:       [none / tool name]
Prompt changes:  [none / description]
Model changes:   [none / description]
ChromaDB:        [no change / re-embed needed / new collection]
```

---

## 7. Flutter Screens
*Filled by Flutter Agent.*

```
New screens:     [screen names]
Modified:        [screen names]
State changes:   [Riverpod providers]
Navigation:      [route changes]
```

---

## 8. Tests
*Filled by Testing Agent.*

```
Unit tests:       [file paths]
Integration:      [file paths]
Coverage target:  [X%]
```

---

## 9. Security Review
*Filled by Security Agent.*

```
Auth required:    [yes/no]
File upload:      [yes/no — validated?]
SQL queries:      [parameterized? yes/no]
Prompt injection: [checked? yes/no]
Verdict:          APPROVED / BLOCKED
```

---

## 10. Documentation
*Filled by Documentation Agent.*

```
README updated:        [yes/no]
API docs updated:      [yes/no]
Data dictionary:       [yes/no — if new table]
Changelog entry:       [yes/no]
```

---

## 11. Demo Checklist
*Validated by PM Agent and Product Agent.*

```
[ ] Feature works end-to-end on device
[ ] Tamil UI renders correctly
[ ] Works on low-end Android (2 GB RAM)
[ ] Offline scenario tested
[ ] Response time < 5 seconds (main flow)
[ ] Tamil farmer persona walkthrough complete (Murugan test)
```

---

## 12. Release Notes
*Written by Documentation Agent. Reviewed by PM Agent.*

```
## FP-XXX — [Feature Name]

What farmers can now do:
- [plain language benefit 1]
- [plain language benefit 2]

How to use:
- [one-line instruction in English, Tamil in app]
```

---

## Sign-offs Required Before Status → COMPLETE

| Agent | Sign-off | Date |
|-------|----------|------|
| PM Agent | [ ] | |
| SA Agent | [ ] | |
| Testing Agent | [ ] | |
| Security Agent | [ ] | |
| Documentation Agent | [ ] | |
| Standards Agent | [ ] | |
| **Master Agent** | [ ] | |
