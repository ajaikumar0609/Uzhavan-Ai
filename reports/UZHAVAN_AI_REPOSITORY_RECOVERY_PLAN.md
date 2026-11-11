# UZHAVAN AI: Repository Recovery Plan (Phase 1)

**Date:** 2026-11-08. **Status: plan complete. Nothing staged, committed or pushed.**
This supersedes the draft `reports/artifacts/uzhavan_git_recovery_plan.md` from Sprint 1.

## 0. What was done this phase, and what was not
| Done | Not done (not authorized) |
|---|---|
| Applied one additive `.gitignore` block (32 lines, 0 deletions) | No `git add`, commit or push |
| File-level SHA256 manifest of the source backup (1,748 files) | No PostgreSQL / Redis / Ollama started |
| Tracking allowlist (459) and hold list (532) | No tests run (none would touch Chroma) |
| Created empty `docs/srs/` and `docs/architecture/` | No source-code changes beyond `.gitignore` |
| Addendum archive of Sprint 1 + Phase 1 changes | No M4 / satellite checkpoint touched |
| Dataset and checkpoint backup inventory | Original backup not modified |

Staged files now: **0**. Root history: still the single commit `ef50615`. All existing uncommitted source is intact on disk.

## 1. The `.gitignore` change (exact)
File: `/Users/ajaikumarn/Desktop/agri/.gitignore`. `git diff --stat`: **32 insertions, 0 deletions**. The 21 original lines are unchanged; the pre-change copy is kept at `~/Desktop/uzhavan_backups_sprint1/gitignore_before_phase1_20261108` (byte-identical to `HEAD`).

```
+# --- Phase 1 repository safety additions (2026-11-08) ---
+.env   .env.*   !.env.example   *.jks   *.keystore   key.properties   local.properties
+.dart_tool/   .flutter-plugins   .flutter-plugins-dependencies   build/   dist/   *.log
+*.pth   *.pth.tar   *.onnx   *.ckpt
+chroma_db/   **/rag/chroma/
+tnau_crawler/knowledge_base/   mini project/
```
(One entry per line in the file; condensed here.) Adapted from your proposed list to the real repo:

| Your example | Applied as | Note |
|---|---|---|
| `.venv/`, `__pycache__/`, `.pytest_cache/` | already present (`.venv*`, etc.) | not duplicated |
| `uzhavan_data/`, `*.pt` | already present | not duplicated |
| `chroma_db/` | `chroma_db/` **plus** `**/rag/chroma/` | the real stores are `rag/chroma` and `uzhavan_platform/rag/chroma`, which `chroma_db/` would never match |
| `*.pth`, `*.onnx` | applied, plus `*.pth.tar` and `*.ckpt` | SICKLE checkpoints are `*.pth.tar` |
| not in your list | added `tnau_crawler/knowledge_base/`, `mini project/`, signing files | 1.1 GB crawled PDFs (licence-sensitive), 128 MB presentations, keystores |

**Verified effects** (`git check-ignore -v`):
- Ignored as intended: `uzhavan_platform/.env`, `frontend/.env.local`, both Chroma stores, `knowledge_base/*`, `mini project/*`, `android/local.properties`.
- Still trackable: `uzhavan_platform/.env.example`, `frontend/.env.example`, all of `backend/`, `tests/`, `database/`, `requirements*.txt`, `lib/`.
- Candidate (untracked, non-ignored) files fell from **5,775 to 993**.
- 9 already-tracked files (logs under `reports/production_build/` and an M4 `run.log`) match `*.log`. Ignore rules never untrack, so they stay tracked; only *new* `.log` files are hidden. If you want new report logs tracked, add `!reports/**/*.log`.
- `build/` is unanchored, which is safe here: the only source-tree directory called `build` is `uzhavan_flutter/build`.

## 2. Files proposed for Git tracking
- **Allowlist (459 files, 2.8 MB): `reports/artifacts/uzhavan_git_tracking_allowlist.txt`.** Composition: `uzhavan_platform/backend` 124, `uzhavan_flutter/lib` 100, `uzhavan_platform/docs` 44, `tests` 29, `agents` 22, `database` 21 (migrations and SQL), `uzhavan_flutter/test` 21, `android` 19, `api` 14, `reports/artifacts` 14, plus `evaluation`, `playbooks`, `docker`, `scripts`, requirements and config templates, `tnau_crawler/{crawler.py,requirements.txt,CRAWL_REPORT.md}`, `uzhavan_ml/scripts/verify_v2_2_repro_data.py`.
- Scans of the 993 candidates: largest file 1.3 MB; no private keys or real tokens. The only secret-pattern hits are 4 files with documented placeholder or test values (`change_me…`, `test-secret…`) in `NEXT_ACTIONS.md` and three auth/settings tests. Values not reproduced here.
- **Hold for your decision (532): `reports/artifacts/uzhavan_git_hold_for_decision.txt`:**
  - `rag/chunks/` (521 files, 1.3 MB): derived from the TNAU crawl, so a redistribution question and regenerable.
  - `uzhavan_platform/database/data/uzhavan_normalized.json`: contains 9 public TNAU office phone numbers. Decide the PII policy.
  - `uzhavan_platform/docs/audit/NEXT_ACTIONS.md`: contains a placeholder secret line; read it before tracking.
  - `scratch_*.json`, `inspect_s2_assets.py`, `test_copernicus.py`: scratch files in the repo root (the last one touches Copernicus; no credential pattern found).
  - `reports/samsung_*.png` (5 device screenshots): check they show no personal data.
- **Excluded from the root allowlist on purpose:** `frontend/` (own repo, `c09fa82`, 32 pending changes) and `external/SICKLE/` (third-party clone). At root they would become embedded-repo gitlinks. Commit `frontend` inside its own repo.

## 3. Files that must never be tracked
| Class | Paths |
|---|---|
| Secrets | `uzhavan_platform/.env`, `frontend/.env.local`, any `.env.*` except `.env.example`; `*.jks`, `*.keystore`, `key.properties`; Google service credentials (`GOOGLE_APPLICATION_CREDENTIALS` targets) |
| Datasets | `uzhavan_data/`, `sickle_dataset/`, `sickle_toy_dataset/`, `datasets/` (19 of 46 catalogued datasets have **UNVERIFIED** licences) |
| Checkpoints | `runs/` (156 SICKLE), `uzhavan_ml/runs_m4/` (8), `*.pt *.pth *.pth.tar *.onnx *.ckpt` |
| Vector stores | `uzhavan_platform/rag/chroma/`, `rag/chroma/` |
| Crawled corpora | `tnau_crawler/knowledge_base/` (4,765 files, 1.1 GB) |
| Generated | `.venv*`, `node_modules/`, `uzhavan_flutter/build/`, `.dart_tool/`, `frontend/.output`, `__pycache__`, `.pytest_cache`, `all_files.txt`, `dataset_structure.txt` (367 MB and 327 MB listings) |
| Large binaries | `mini project/*.pptx` (98 MB, near GitHub's 100 MB hard limit), `.apk` / `.aab` builds |
| Local backups | `backups/` (old SQL dumps may contain real data) |

## 4. Proposed staging order (for later; not authorized yet)
Each step is a separate local commit, reviewed with `git diff --cached --stat` and a file-name-only secret scan before committing.
1. `git add .gitignore` (alone).
2. Allowlist files for `uzhavan_platform/` (by explicit path list, never `git add .`).
3. `uzhavan_flutter/` allowlist.
4. `tnau_crawler` code files, `uzhavan_ml/scripts/…`, `reports/`.
5. Hold-list items, one by one, after your decision.
6. SRS and SDD (section 6).
Staging mechanism for the review step: `git add --pathspec-from-file=reports/artifacts/uzhavan_git_tracking_allowlist.txt`, which only takes the listed paths. Not run.

## 5. Backups still required
### A. Off-machine source backup (encrypted external SSD)
Files in `~/Desktop/uzhavan_backups_sprint1/`:
| File | SHA256 |
|---|---|
| `uzhavan_source_backup_20261108_121229.tar.gz` (unchanged) | `19a13ac9fd39868c233a69d5d748560be2a5c2c49621cea2e2b71395bf0bd127` |
| `uzhavan_source_backup_20261108_121229.files.sha256` (per-file manifest, 1,748 files) | `1658eaa7c4cd3b38d0c26c7af2e16c889f7233bea7f1073d9481687b23f270d1` |
| `uzhavan_phase1_addendum_20261108.tar.gz` (11 entries: Sprint 1 code edits, the new tests, `.gitignore`, Sprint 1 reports) | `4d6cd8a841a86732098583e38a965c4b78479ad2da39e50a74ce94281412cf1d` |
| `gitignore_before_phase1_20261108` | original `.gitignore` |

Why an addendum: the original archive predates the Sprint 1 edits (`settings.py`, `disease_scan.py`, the two new test files) and the `.gitignore` change. Those live only on this disk and in the addendum.

Manifest drift check (live vs. archive): exactly 4 differences: `.gitignore`, `settings.py`, `disease_scan.py` (all intentional) and `rag/chroma/chroma.sqlite3` (timestamp-level change from the Sprint 1 test run; the 520 rows were identical). 0 files missing.

**Verification procedure after copying to the SSD:**
```
cd /Volumes/<SSD>/uzhavan_backups_sprint1
shasum -a 256 -c uzhavan_source_backup_20261108_121229.tar.gz.sha256      # expect OK
shasum -a 256 -c uzhavan_phase1_addendum_20261108.tar.gz.sha256            # expect OK
mkdir /tmp/uz_verify && tar -xzf uzhavan_source_backup_20261108_121229.tar.gz -C /tmp/uz_verify
cd /tmp/uz_verify && shasum -a 256 -c /Volumes/<SSD>/uzhavan_backups_sprint1/uzhavan_source_backup_20261108_121229.files.sha256   # expect 1748 OK
git -C /tmp/uz_verify fsck --no-dangling                                  # Git objects intact
```
The per-file manifest closes the gap you raised: `git fsck` only covers Git objects, while the manifest covers every untracked source file's bytes. Keep the SSD copy encrypted (FileVault-formatted APFS volume) and keep a second copy of the SHA256 values somewhere else (e.g. this report).

### B. Data and model backups (separate, none done yet)
| Asset | Path | Size | Notes |
|---|---|---|---|
| Agricultural dataset collection | `uzhavan_data/` (46 datasets) | 6.3 GB (06_disease_pest 4.7 GB, 03_weather 861 MB, 04_soil 330 MB, 02_satellite 202 MB, 09_schemes 134 MB, …) | Per-dataset checksum files already exist under each `metadata/`. Verify them after copy. |
| SICKLE dataset | `sickle_dataset/` (+ toy 1.0 GB) | 15 GB (+1.0 GB). With `uzhavan_data` this is the ~22 GB total, more than the "14 GB" figure in your note, so size the SSD for the full set | Licence **UNVERIFIED**: access is granted on request. `01_sickle/checksums.txt` exists. |
| SICKLE checkpoints | `runs/wacv_2024/` | 3.3 GB, 156 files / 78 runs | |
| M4 checkpoints + eval artifacts | `uzhavan_ml/runs_m4/`, `uzhavan_ml/packages/`, `uzhavan_ml/registry.json`, `model_status.json`, `model_registry.md` | 1.1 GB + 1.1 GB, 8 checkpoint files | M4 is HOLD / NO-GO; this backup is read-only copy, no hashing of checkpoints has been run yet (hash on the destination and compare). |
| ChromaDB index | `uzhavan_platform/rag/chroma/` (12 MB, 520 embeddings), `rag/chroma/` (184 KB) | 12 MB | The original archive holds only `chroma.sqlite3`. Back up the whole directory **while no process has it open**. |
| TNAU crawl corpus | `tnau_crawler/knowledge_base/` | 1.1 GB | |
| Metadata and licence records | `uzhavan_data/00_metadata/` (`master_catalog.json`, `source_registry*.json`, scripts) | <1 MB | Already inside `uzhavan_data/`; also copy separately to be safe. |
| Older DB dumps | `backups/` (5 SQL dumps, 1 tgz, 7.5 MB) | 7.5 MB | Contains real data: encrypted destination only. |

**Licence rule:** 19 of the 46 catalogued datasets have `license` = UNVERIFIED (SICKLE, IMD rainfall/temperature, NASA POWER, ICAR-NBSS soil maps, Soil Health Card, SLUSI, TNAU resources/crawl/guides, NHB, Season & Crop Report, Agmarknet, e-NAM, scheme PDFs, and others). **Use the encrypted external SSD only; no cloud upload for any of those** until the licence is resolved. Roughly 4.7 GB (`06_disease_pest`) is a separate licence set; check its `source_registry.json` before any cloud use.

Suggested method (not run): `rsync -a --checksum` to the SSD, then regenerate checksums at the destination and compare against the per-dataset checksum files and against a fresh `shasum -a 256` list of the source.

## 6. Documentation destinations (SRS and SDD)
Confirmed and prepared (empty directories only; no document copied or invented):
```
/Users/ajaikumarn/Desktop/agri/docs/srs/            <- UZHAVAN_AI_SRS.docx
/Users/ajaikumarn/Desktop/agri/docs/architecture/   <- UZHAVAN_AI_Software_Design_Document.docx
```
One thing for you to decide: these are **repo-root** `docs/`, as you wrote. The existing documentation lives in `uzhavan_platform/docs/` (PRD.md, PROJECT_BIBLE.md, `architecture/CONVERSATION-SERVICE.md`, ADRs, roadmap, sprints). That would leave docs in two places. Options: (a) keep as created and later move the existing platform docs up, or (b) use `uzhavan_platform/docs/srs` and `uzhavan_platform/docs/architecture`. I recommend (a) only if you intend `docs/` to cover the whole project, including Flutter and ML; otherwise (b). Git does not track empty directories, so they appear in `git status` only after the `.docx` files are copied in.
**Note:** `.docx` is binary, so diffs are unreadable. Consider also keeping a Markdown export of each. The files must be copied by you from the ChatGPT workspace; I cannot access them.

## 7. Open items and risks
1. Everything is still on one disk. **Until the SSD copy is made and verified, the project has no protection against disk loss.**
2. The existing GitHub remotes (`ajaikumar0609/Uzhavan-Ai`, `…/uzhavan-chelvi-seyal`) are of **unconfirmed privacy**. Check in the GitHub settings or via `gh repo view --json visibility`. I have not queried, because that is a network call to an external service.
3. The Chroma stores were last modified by the Sprint 1 test run. Before any future test run, set a temp `CHROMA_PATH` (Phase 2 work, requires code or test-fixture changes).
4. Decisions needed from you: the hold list (section 2), the `!reports/**/*.log` exception, the `docs/` location (section 6).
5. Release APK still signed with the debug key; authentication demo default OTP in source: see Sprint 1 report.
6. Completion percentages stay provisional until the SRS is imported and the denominator reconciled.

## 8. Confirmation of constraints
No staging; no commit; no push; no service started; no test run; no application code changed (the only edit this phase is `.gitignore`); authentication untouched; M4 and satellite checkpoints untouched (not even hashed); existing backup preserved and re-verified (`OK`); all pre-existing uncommitted source preserved.

Stopping here. Phase 2 (infrastructure) has not been started.
