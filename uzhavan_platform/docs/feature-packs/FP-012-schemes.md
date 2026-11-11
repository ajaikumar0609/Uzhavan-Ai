# FP-012: Government schemes + rule-based eligibility

**Status:** `COMPLETE` (backend, 2026-09-25). Evidence: `scripts/load_schemes.py` loaded **136/136** records into uzhavan_dev (run twice → 136); `tests/api/test_schemes.py` (44 tests: one or more per eligibility rule, rule fidelity vs `schemes.jsonl`, loader, endpoints, the real store); live curl of list, detail and eligibility with a dev-OTP token.
**Sprint:** Sprint-006 · **Milestone:** M-06 · **Owner:** Backend Sub-Agent · **Depends on:** FP-008, FP-009
**Contract:** §0, §6

## 1. Overview
The 136-record catalogue (`uzhavan_data/09_government_schemes/processed/schemes.jsonl`: 123 state, 13 central) is loaded into Postgres and served as-is. Eligibility is checked only by explicit, cited rules.

## 2. Business Goal
Farmers find schemes relevant to them and can see honestly whether the stated criteria fit, without promises.

## 3. User Story
As a cotton farmer in Salem, I see which schemes list my district and crop, and what extra information decides the rest.

## 4. Acceptance Criteria
- [x] Migration 006 **extends** `government_schemes` (the 001 table was empty): `scheme_key` (the public `scheme_id`, unique), `authority`, `level` (CHECK central|state), `active`, `crops` TEXT[] (GIN index), `crop_applicability`, bilingual description/eligibility/documents, `application_method`, `official_url`, `source_documents` JSONB, `date_checked`, `last_updated_on_source`, `components` JSONB, and more. The 001 columns `name`, `tamil_name`, `eligibility`, `benefit` and `documents_required` are reused.
- [x] Loader: upsert on `scheme_key`, and deletes keys no longer in the file (one transaction). Tamil kept where present (117 names, 89 eligibility, 89 description, 84 documents). `active` from `source_active_flag` (51 true, 66 false, 19 null). `crops` are only the meta crop ids explicitly named in `crop_applicability` (4 schemes); otherwise null.
- [x] `GET /api/schemes?q=&level=&crop_id=&active=`, `GET /api/schemes/{id}` (missing → null, never inferred), `GET /api/schemes/{id}/eligibility` 🔒 (optional `farm_id`).
- [x] `eligibility_rules.yaml`: **16 rules**, each quoting the source eligibility text, with `criteria_source_url` = the scheme's `official_url`. 12 decide on district/crop only; 4 (PM-KISAN, PMFBY, PM-KUSUM, the TN electric pumpset scheme) always return `more_information_required` with `missing_fields` for facts the app doesn't collect (land records, exclusions, notified crop/area, owned land, EB connection, diesel pump or off-grid status). No rule → `cannot_determine`. "Preference to SC/ST/women" clauses are not treated as criteria.

## 5. UI Design
Flutter shows the status, the reasons (en; ta null) and missing_fields, and always shows the official link.

## 6. API Contract
As in §6. Additions: `crop_applicability`, `components`, `state` and `source_go_file` in the detail; `reasons` always ends with "Only the criteria stated in the official source were checked…". Crop `other` counts as an unknown crop (→ more information).

## 7. Database Changes
`006_government_schemes.sql` (idempotent, applied twice). Backup: `backups/uzhavan_dev_before_006_20260925_234300.sql`. The load is recorded in `data_sources`.

## 8. AI Changes
None (the cognitive `scheme_agent` is untouched).

## 9. Agent Responsibilities
Backend: the API, loader and rules. An agronomy/policy reviewer extends the rules only from source text. Flutter: the schemes screen.

## 10. Testing
One parametrised case set per rule (eligible, not eligible and missing information where applicable); a test that `requires` never yields eligible; fidelity (each rule's quoted text starts the stored eligibility text, and the URL equals `official_url`); the loader in a throwaway schema; 401 without a token; 404 for an unknown scheme or foreign farm.

## 11. Security
Eligibility reads only the token farmer's profile and farms. SQL is parameterised; `q` is limited to 100 characters.

## 12. Performance
136 rows; ILIKE search is fine at this scale.

## 13. Documentation
This FP; the YAML header states the rule policy; CHANGELOG.

## 14. Demo Checklist
- [x] `/api/schemes` → 136 · `/api/schemes/central_pm_kisan` · eligibility with a dev token

## 15. Release Notes
> **FP-012: Government schemes.** Browse 136 central and Tamil Nadu schemes with the official details, in Tamil where the source has it. For 16 schemes, UZHAVAN checks the published district and crop criteria against your farms. It tells you plainly when it needs information it doesn't have and never assumes eligibility.

**Deviations:** 66 TN catalogue schemes are marked inactive by the source but are still listed (`active:false`); `active=true` filters them out. Many criteria (SC/ST, landholding size, sub-basin, selected village panchayats) can't be checked, so those schemes have no rule (`cannot_determine`).
