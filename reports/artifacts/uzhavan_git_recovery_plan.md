# UZHAVAN AI: Git Recovery Plan (Sprint 1)

Status: **plan only. Nothing was staged, committed, or pushed.** Existing history (root `ef50615`, one commit) is untouched.

## 1. Repositories found
| Path | Branch | HEAD | Uncommitted | Remote |
|---|---|---|---|---|
| `.` (root) | main | `ef50615` | 28 status entries (all untracked) | github.com/ajaikumar0609/Uzhavan-Ai |
| `frontend/` | main | `c09fa82` | 32 | github.com/ajaikumar0609/uzhavan-chelvi-seyal |
| `external/SICKLE/` | main | `c496cee` | 0 | third-party (Depanshu-Sani/SICKLE): do not push or vendor |

`frontend/` and `external/SICKLE/` are nested repos. `git add .` at the root would record them as embedded gitlinks, not content.

## 2. Biggest risk
**All application code is untracked**: `uzhavan_platform/` (backend, tests, docs), `uzhavan_flutter/`, `rag/`, `tnau_crawler/` code, plus my Sprint 1 edits. The single commit contains only `uzhavan_ml/`, `reports/` and a few top-level files. Nothing is protected by Git today. The local tarball is the only copy and it sits on the same disk.

## 3. What a blind `git add .` would stage (5,775 files). Do NOT do this
- `tnau_crawler/knowledge_base/**`: 4,765 files, ~1.1 GB crawled PDFs/HTML. Several PDFs are 20-55 MB. Also raises copyright/redistribution questions.
- `mini project/AI-Powered-Personal-Farming-Assistant (1).pptx`: 98 MB, just under GitHub's 100 MB hard limit. The `.key` files there are Keynote decks, not credentials.
- `rag/chunks/**`: 521 derived chunk files from the crawl.
- Secrets: `uzhavan_platform/.env` and `frontend/.env.local` are **already ignored** by their sub-repo `.gitignore` files, so they would not be staged. The root `.gitignore` itself has no `.env` rule, so that protection depends on the sub-`.gitignore` staying in place.

## 4. Proposed additions to root `.gitignore` (not applied)
```
.env
.env.*
!.env.example
*.key
*.pptx
mini project/
tnau_crawler/knowledge_base/
rag/chunks/
rag/chroma/
scratch_*.json
reports/*.png
*.jks
*.keystore
key.properties
local.properties
```
Decide separately whether `rag/chunks` and `reports/*.png` belong in Git. Large corpora belong in DVC / Git LFS / object storage, not plain Git.

## 5. Staging order (run only after review; each step is a separate, reviewable commit)
1. Apply the `.gitignore` change above. Commit alone.
2. `git add uzhavan_platform/` then `git status` and check that no `.env`, `.venv`, `rag/chroma` or `__pycache__` is staged. Commit: "Add platform backend, tests, docs".
3. `git add uzhavan_flutter/` after confirming `build/`, `.dart_tool/`, `local.properties` are ignored. Commit.
4. `git add tnau_crawler/crawler.py tnau_crawler/requirements.txt tnau_crawler/CRAWL_REPORT.md rag/` (code only). Commit.
5. `git add reports/` (text/CSV only). Commit.
6. Add SRS/SDD under `uzhavan_platform/docs/` (see report section 9) as their own commit.
7. Before each commit: `git diff --cached --stat`, and run a secret scan (`git diff --cached | grep -nEi 'api[_-]?key|secret|token|password'`) and review hits.
For `frontend/` (its own repo, 32 pending changes): review `git -C frontend status`, commit within that repo.

## 6. Safest private backup remote
1. Create a **private** repo (GitHub/GitLab) under your own account. Confirm visibility = Private before adding the remote. The existing `origin` URLs point to github.com/ajaikumar0609/*: check that those repos are private, since this is unverified.
2. Authenticate with a fine-grained token or SSH deploy key, not a password in the URL.
3. Add it as a *second* remote (`git remote add backup <url>`), not by replacing `origin`; push only after step 5 review.
4. Back up non-Git assets (M4/SICKLE checkpoints ~4.4 GB, `uzhavan_data` 6.3 GB) separately: encrypted external disk or private object storage, with checksums.
5. Keep one copy of the Sprint 1 tarball off this machine.
