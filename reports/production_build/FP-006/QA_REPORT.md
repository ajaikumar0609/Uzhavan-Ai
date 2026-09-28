# FP-006 QA report (2026-09-25)

**Result: PASS.** Status → COMPLETE.

## Automated (re-run by the Master Agent, not taken from the sub-agent's report)
| Check | Result | Log |
|---|---|---|
| `tsc --noEmit` | 0 errors | `tsc.log` |
| `vite build` | pass | `build.log` |
| `npm run check:no-fabrication` | OK: 14 blocked strings, 0 hits | `no_fabrication.log` |
| `vitest run` | 37/37 pass (6 outcomes × 5 hooks + extras) | `vitest.log` |
| backend `pytest` | 70 pass / 10 errors, **unchanged from baseline** (no backend change) | `pytest.log` |

## Manual (backend down, which is the current real state)
| Scenario | Device | Result | Evidence |
|---|---|---|---|
| Upload a groundnut-rust photo (previously gave "Rice Leaf Blast 94%") | desktop 390×844 | ✅ own photo + "Validated disease model unavailable", no diagnosis, dose or officer | `fp006_scan_after_upload.png` |
| Ask the assistant with the backend down | desktop 390×844 | ✅ bilingual "Can't reach the UZHAVAN server", no Listen button | `fp006_assistant_error.png` |
| Home / Market / Weather / Diary / Profile | Android emulator Pixel 6 (Chrome 109) | ✅ UNAVAILABLE + Retry; neutral greeting; no fake values | `emulator/*.png` |
| QA defect Q1: Retry button crushing the text | emulator | found → fixed → re-verified | `emulator/home_after_fix.png` |
| QA defect Q2: profile "Not set" ×4 + overflow | emulator | found → fixed → re-verified | `emulator/profile_after_fix.png` |

## Files (29)
Modified (21): `components/app/AppShell.tsx`; hooks `useConversation, useDiary, useDisease, useFarmerProfile, useMarket, useSchemes, useWeather`; `lib/api/client.ts, conversation.ts, disease.ts, types.ts`; `lib/prototype.ts`; routes `assistant, diary, index, market, onboarding, profile, scan, weather`.
Added (4 in src): `components/app/DataState.tsx`, `lib/dataStatus.ts`, `lib/uiStates.ts`, `hooks/__tests__/dataHooks.test.tsx`.
Other (4): `scripts/check-no-fabrication.mjs`, `vitest.config.ts`, `package.json`, `package-lock.json`.
Rollback: `backups/pre_production_build_20260925_1556.tgz`.

## Deferred (tracked)
Chrome < 111 icon and chip colours → FP-016 · the Thanjavur query parameter → FP-007/008 · inert Profile rows → FP-020 · `bun.lock` stale.
