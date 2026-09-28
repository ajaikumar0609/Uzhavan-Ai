"""Local resume tests for train_m4.py (v1.1). Tiny smoke configuration, CPU, no real training. Writes only to a temp dir.
T1 (required) 3 epochs, runtime lost after epoch 1 -> resume starts at epoch 2, history kept, same dir, completes.
T2 4 epochs, lost after epoch 2 (full fine-tune phase) -> resume at 3; model+optimizer+scheduler state restored exactly.
T3 3 epochs, lost after epoch 0 (head warm-up phase) -> resume at 1; head-phase optimizer restored exactly.
T4 SIGTERM during training -> status 'interrupted', checkpoint preserved, resume completes.
T5 re-running a completed experiment -> skipped, nothing overwritten.
T6 interrupted+resumed run == uninterrupted run (identical per-epoch train loss and val F1) -> resume is exact, not approximate.
"""
import json, os, signal, subprocess, sys, tempfile, time, glob, hashlib
from pathlib import Path

HERE = Path(__file__).parent; PY = sys.executable
PKG = HERE.parent / "packages/m4_v1"
ENV = {**os.environ, "UZ_FORCE_CPU": "1", "PYTHONWARNINGS": "ignore"}
ROOT = Path(tempfile.mkdtemp(prefix="m4_resume_tests_"))
results = []


def run(out, epochs, extra=(), check=None):
    cmd = [PY, str(HERE / "train_m4.py"), "--pkg", str(PKG), "--out", str(out), "--seed", "1", "--epochs", str(epochs), "--bs", "8", "--smoke", *extra]
    p = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
    log = p.stdout + p.stderr
    if check is not None: assert p.returncode == check, f"exit {p.returncode} != {check}\n{log[-3000:]}"
    return p.returncode, log


def expdirs(out): return sorted(d for d in Path(out).iterdir() if d.is_dir())
def ej(d): return json.load(open(d / "experiment.json"))
def ck(d):
    import torch; return torch.load(d / "checkpoint_last.pt", map_location="cpu", weights_only=False)
def audit(d): return json.load(open(sorted(d.glob("resume_audit_*.json"))[-1]))
def ok(name, cond, detail): results.append((name, bool(cond), detail)); print(("PASS " if cond else "FAIL ") + name + " :: " + detail, flush=True)


# ---------------- T1 (required)
o = ROOT / "t1"
rc, log = run(o, 3, ["--_test_hard_exit_after_epoch", "1"])
d = expdirs(o); ok("T1 runtime loss exit code", rc == 137, f"exit {rc}")
ok("T1 one experiment dir", len(d) == 1, str([x.name for x in d])); d = d[0]
c = ck(d); ok("T1 checkpoint_last after kill", c["last_completed_epoch"] == 1, f"last_completed_epoch={c['last_completed_epoch']}")
ok("T1 status left 'running' (hard kill, like a Colab disconnect)", ej(d)["status"] == "running", ej(d)["status"])
hist_before = json.load(open(d / "history.json"))
ok("T1 no .tmp files left", not list(d.glob("*.tmp")), str(list(d.glob("*.tmp"))))
rc, log2 = run(o, 3, check=0)
resume_line = [l for l in log2.splitlines() if l.startswith("[resume]")]
a = audit(d); ok("T1 resumed at epoch 2", a["start_epoch"] == 2 and "resuming from epoch 2" in log2, " | ".join(resume_line))
ok("T1 epochs executed after resume = [2] only", [json.loads(l)["epoch"] for l in log2.splitlines() if l.startswith('{"epoch"')] == [2], "no epoch 0/1 re-run")
ok("T1 model state restored exactly", a["model_state_sha"] == a["checkpoint_model_sha"], f"{a['model_state_sha']} == {a['checkpoint_model_sha']}")
ok("T1 phase boundary: epoch 2 starts the full fine-tune with a NEW optimizer (as in v1.0)", a["phase_boundary_new_optimizer"] is True, str(a["phase_boundary_new_optimizer"]))
h = json.load(open(d / "history.json"))
ok("T1 history preserved + extended", h[:2] == hist_before and [e["epoch"] for e in h] == [0, 1, 2], f"epochs {[e['epoch'] for e in h]}")
ok("T1 still one dir; status completed", len(expdirs(o)) == 1 and ej(d)["status"] == "completed" and ej(d)["last_completed_epoch"] == 2, ej(d)["status"])
T1_LOG = "\n".join(resume_line + [l for l in log2.splitlines() if l.startswith(("{", "[checkpoint]", "done"))])

# ---------------- T2 full-phase optimizer restore
o = ROOT / "t2"; run(o, 4, ["--_test_hard_exit_after_epoch", "2"]); d = expdirs(o)[0]
run(o, 4, check=0); a = audit(d)
ok("T2 resumed at epoch 3", a["start_epoch"] == 3, str(a["start_epoch"]))
ok("T2 optimizer loaded (mid-phase) and exact", a["optimizer_state_loaded"] and a["optimizer_state_sha"] == a["checkpoint_optimizer_sha"], f"{a['optimizer_state_sha']} == {a['checkpoint_optimizer_sha']}")
ok("T2 model exact", a["model_state_sha"] == a["checkpoint_model_sha"], "")

# ---------------- T3 head-phase optimizer restore
o = ROOT / "t3"; run(o, 3, ["--_test_hard_exit_after_epoch", "0"]); d = expdirs(o)[0]
run(o, 3, check=0); a = audit(d)
ok("T3 resumed at epoch 1 with head-phase optimizer restored exactly", a["start_epoch"] == 1 and a["optimizer_state_loaded"] and a["optimizer_state_sha"] == a["checkpoint_optimizer_sha"], str(a))

# ---------------- T4 SIGTERM
o = ROOT / "t4"; o.mkdir()
cmd = [PY, str(HERE / "train_m4.py"), "--pkg", str(PKG), "--out", str(o), "--seed", "1", "--epochs", "3", "--bs", "8", "--smoke"]
p = subprocess.Popen(cmd, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
t = time.time()
while time.time() - t < 600:
    ds = expdirs(o)
    if ds and (ds[0] / "checkpoint_last.pt").exists(): break
    time.sleep(0.5)
p.send_signal(signal.SIGTERM); out, _ = p.communicate(timeout=300); d = expdirs(o)[0]
ok("T4 SIGTERM -> exit 130, status interrupted", p.returncode == 130 and ej(d)["status"] == "interrupted", f"exit {p.returncode}, status {ej(d)['status']}")
ok("T4 prints where to resume", "--resume" in out and "checkpoint_last.pt" in out, [l for l in out.splitlines() if "INTERRUPTED" in l][0][:200] if "INTERRUPTED" in out else "missing")
ok("T4 checkpoint preserved", (d / "checkpoint_last.pt").exists(), "")
run(o, 3, check=0); ok("T4 resume completes", ej(d)["status"] == "completed", ej(d)["status"])

# ---------------- T5 completed experiment is skipped, untouched
d = expdirs(ROOT / "t1")[0]
before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in d.iterdir() if f.is_file()}
rc, log = run(ROOT / "t1", 3, check=0)
after = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in d.iterdir() if f.is_file()}
ok("T5 completed run skipped, no file changed", "already COMPLETED" in log and before == after, [l for l in log.splitlines() if "COMPLETED" in l][0] if "COMPLETED" in log else log[-300:])

# ---------------- T6 exactness: uninterrupted == interrupted+resumed
o = ROOT / "t6_straight"; run(o, 3, check=0); hs = json.load(open(expdirs(o)[0] / "history.json"))
hr = json.load(open(expdirs(ROOT / "t1")[0] / "history.json"))
key = lambda h: [(e["epoch"], round(e["train_loss"], 6), round(e["val"]["mean_macro_f1"], 6)) for e in h]
ok("T6 resumed run identical to uninterrupted run", key(hs) == key(hr), f"straight {key(hs)} | resumed {key(hr)}")

print("\n==== RESUME LOG (T1, after simulated runtime loss) ====\n" + T1_LOG)
n_fail = sum(not r[1] for r in results)
json.dump({"root": str(ROOT), "results": [{"test": n, "pass": p, "detail": d} for n, p, d in results], "t1_resume_log": T1_LOG},
          open(HERE.parent / "experiments/resume_tests_train_m4_v1.1.json", "w"), indent=1)
print(f"\n{len(results) - n_fail}/{len(results)} checks passed; artefacts in {ROOT}")
sys.exit(1 if n_fail else 0)
