"""Build uzhavan_ml/registry.json + model_registry.md from experiments/*/experiment.json. Append-only: entries are never removed;
an experiment directory is never overwritten (train/eval scripts create new IDs)."""
import json, datetime as dt
from pathlib import Path
ML = Path.home() / "Desktop/agri/uzhavan_ml"
REG = ML / "registry.json"
reg = json.load(open(REG)) if REG.exists() else {"entries": {}}
for f in sorted(ML.glob("experiments/*/experiment.json")):
    e = json.load(open(f)); eid = e["experiment_id"]
    prev = reg["entries"].get(eid, {})
    e["path"] = str(f.parent.relative_to(ML)); e["status"] = prev.get("status", e.get("status"))   # status only changes by explicit decision
    reg["entries"][eid] = {**prev, **e}
reg["updated"] = dt.datetime.now().isoformat(timespec="seconds")
json.dump(reg, open(REG, "w"), indent=1, default=str)
STATUS_ORDER = ["BASELINE", "TRAINED", "VALIDATED", "PRODUCTION-ELIGIBLE", "RESEARCH-ONLY", "BLOCKED", "PLANNED", "smoke", "experiment", "benchmark"]
lines = ["# UZHAVAN model registry", "", f"Generated {reg['updated']} from `uzhavan_ml/registry.json` (append-only).", "",
         "Status legend: **BASELINE** = pre-existing model evaluated, not trained by us · **TRAINED** = trained by us, not independently evaluated · "
         "**VALIDATED** = independently evaluated · **PRODUCTION-ELIGIBLE** = passed its fixed gate · **RESEARCH-ONLY** = failed or cannot meet its gate · "
         "**BLOCKED** = missing data/access · **PLANNED** = not started.", "",
         "| Experiment ID | Model | Status | Dataset / split | Seed | Hardware | Duration | Key metric | Data-use / licence | Notes |", "|---|---|---|---|---|---|---|---|---|---|"]
for eid, e in sorted(reg["entries"].items(), key=lambda kv: (STATUS_ORDER.index(kv[1].get("status")) if kv[1].get("status") in STATUS_ORDER else 99, kv[0])):
    hw = e.get("hardware", {}); hw = hw.get("name") or hw.get("device") if isinstance(hw, dict) else hw
    dur = e.get("training_duration_s"); dur = f"{dur/3600:.1f} h" if isinstance(dur, (int, float)) and dur > 0 else "–"
    lines.append(f"| `{eid}` | {e.get('model')} {e.get('model_version','')} | **{e.get('status')}** | {e.get('dataset_version')} / {e.get('split_version')} | "
                 f"{e.get('seed','–')} | {hw} | {dur} | {str(e.get('key_metric', e.get('best_val_mean_macro_f1','–')))[:80]} | "
                 f"{str(e.get('license_data_use','–'))[:90]} | {str(e.get('notes',''))[:120]} |")
ms = ML / "model_status.json"
if ms.exists():
    st = json.load(open(ms))
    lines = lines[:6] + ["## Model status (decisions)", "", "| Model | Candidate | Status | Evidence | Why |", "|---|---|---|---|---|"] + \
        [f"| {m['model']} | {m['candidate']} | **{m['status']}** | {m['evidence']} | {m['why']} |" for m in st["models"]] + \
        ["", "## Experiments (append-only)", ""] + lines[6:]
(ML / "model_registry.md").write_text("\n".join(lines) + "\n")
print(len(reg["entries"]), "entries")
