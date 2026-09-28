"""M4 v1 training: EfficientNetV2-S shared backbone + one classification head per crop (crop is supplied by the farmer/UI).
Spec: training_specification.md §3 M4 + §7 sign-off. Runs on CUDA (cloud) or MPS/CPU (smoke tests only).

usage: python train_m4.py --pkg /path/to/m4_v1 --out runs/ --seed 1 [--epochs 30] [--resume auto|none|PATH] [--smoke]
Writes <out>/<experiment_id>/{experiment.json, history.json, checkpoint_last.pt, checkpoint_best.pt, classes.json}.
v1.1 (2026-09-25): epoch-level resume. Training protocol identical to v1.0 (data, split, classes, model, bs, epochs, optimizer,
augmentation, loss); only checkpointing/resume changed. The experiment dir is stable per seed (no date), so a disconnect resumes
in place from checkpoint_last.pt; completed experiments are never overwritten.
"""
import argparse, json, math, os, platform, random, signal, time, hashlib, subprocess
from pathlib import Path
import numpy as np, pandas as pd, torch, torch.nn as nn, torchvision
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms as T
from PIL import Image

CROPS = ["banana", "coconut", "groundnut", "sugarcane", "black_gram", "chilli"]
IMNET = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])


def seed_all(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


class DS(Dataset):
    def __init__(self, df, root, classes, train):
        self.df, self.root, self.train = df.reset_index(drop=True), Path(root), train
        self.cidx = {c: i for i, c in enumerate(CROPS)}
        self.lidx = {c: {k: i for i, k in enumerate(v)} for c, v in classes.items()}
        self.tf = T.Compose([T.RandomResizedCrop(224, scale=(0.6, 1.0)), T.RandomHorizontalFlip(), T.RandomVerticalFlip(),
                             T.RandomRotation(20), T.ColorJitter(0.2, 0.2, 0.0, 0.02), T.RandomApply([T.GaussianBlur(5)], p=0.1),
                             T.ToTensor(), T.Normalize(*IMNET)]) if train else \
                  T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), T.Normalize(*IMNET)])
    def __len__(self): return len(self.df)
    def __getitem__(self, i):
        r = self.df.iloc[i]
        x = self.tf(Image.open(self.root / r.pkg_path).convert("RGB"))
        return x, self.cidx[r.crop], self.lidx[r.crop][r.canonical_id]


class Model(nn.Module):
    def __init__(self, classes):
        super().__init__()
        bb = torchvision.models.efficientnet_v2_s(weights=torchvision.models.EfficientNet_V2_S_Weights.IMAGENET1K_V1)
        nf = bb.classifier[1].in_features; bb.classifier = nn.Identity(); self.backbone = bb
        self.drop = nn.Dropout(0.3)
        self.heads = nn.ModuleDict({c: nn.Linear(nf, len(classes[c])) for c in CROPS})
    def forward(self, x, crops):
        f = self.drop(self.backbone(x))
        return [self.heads[CROPS[c]](f[i:i + 1])[0] for i, c in enumerate(crops.tolist())]


def per_crop_loss(logits, crops, labels, weights, ls):
    loss = 0.0
    for lg, c, y in zip(logits, crops.tolist(), labels):
        loss = loss + nn.functional.cross_entropy(lg[None], y[None], weight=weights[CROPS[c]], label_smoothing=ls)
    return loss / len(logits)


@torch.no_grad()
def evaluate(model, loader, dev, classes):
    model.eval(); out = {c: {"y": [], "p": []} for c in CROPS}
    for x, cr, y in loader:
        lg = model(x.to(dev), cr)
        for l, c, t in zip(lg, cr.tolist(), y.tolist()):
            out[CROPS[c]]["y"].append(t); out[CROPS[c]]["p"].append(torch.softmax(l.float(), 0).cpu().numpy())
    res = {}
    for c, d in out.items():
        if not d["y"]: continue
        y = np.array(d["y"]); p = np.stack(d["p"]); yh = p.argmax(1); k = len(classes[c])
        f1s = []
        for j in range(k):
            tp = ((yh == j) & (y == j)).sum(); fp = ((yh == j) & (y != j)).sum(); fn = ((yh != j) & (y == j)).sum()
            if (y == j).sum() == 0: continue
            f1s.append(2 * tp / max(2 * tp + fp + fn, 1))
        res[c] = {"macro_f1": float(np.mean(f1s)), "acc": float((yh == y).mean()), "n": int(len(y))}
    res["mean_macro_f1"] = float(np.mean([v["macro_f1"] for v in res.values()]))
    return res


def atomic_json(obj, path):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w") as f: json.dump(obj, f, indent=1, default=str); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_torch(obj, path):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "wb") as f: torch.save(obj, f); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def rng_state():
    st = {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state()}
    if torch.cuda.is_available(): st["cuda"] = torch.cuda.get_rng_state_all()
    return st


def set_rng_state(st):
    random.setstate(st["python"]); np.random.set_state(st["numpy"]); torch.set_rng_state(st["torch"])
    if "cuda" in st and torch.cuda.is_available(): torch.cuda.set_rng_state_all(st["cuda"])


def state_sha(sd):
    """Order-stable hash of every tensor/number in a (nested) state dict: proves an exact restore."""
    h = hashlib.sha256()
    def walk(o):
        if isinstance(o, torch.Tensor): h.update(o.detach().cpu().contiguous().numpy().tobytes())
        elif isinstance(o, dict): [walk(o[k]) for k in sorted(o, key=str)]
        elif isinstance(o, (list, tuple)): [walk(x) for x in o]
        else: h.update(repr(o).encode())
    walk(sd); return h.hexdigest()[:16]


class Interrupted(Exception):
    pass


def make_opt(model, hp, epochs, phase_start_ep, steps_per_epoch):
    """Optimizer/scheduler exactly as in v1.0: created at epoch 0 (head warm-up) and again at warmup_head_epochs (full fine-tune)."""
    frozen = phase_start_ep < hp["warmup_head_epochs"]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=hp["lr_head"] if frozen else hp["lr_full"], weight_decay=hp["wd"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, (epochs - phase_start_ep)) * steps_per_epoch)
    return opt, sched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=30); ap.add_argument("--bs", type=int, default=32); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true", help="tiny subset, 2 batches per epoch; pipeline checks only")
    ap.add_argument("--resume", default="auto", help="auto (default) | none | /path/to/checkpoint_last.pt")
    ap.add_argument("--_test_hard_exit_after_epoch", type=int, default=None, help=argparse.SUPPRESS)  # resume tests only: simulates runtime loss
    a = ap.parse_args()
    seed_all(a.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    if os.environ.get("UZ_FORCE_CPU") == "1": dev = torch.device("cpu")      # resume tests only (exact reproducibility)
    pkg = Path(a.pkg); man = pd.read_csv(pkg / "manifest.csv")
    man = man[man.crop.isin(CROPS)]
    # taxonomy = TRAIN split only: external-test-only classes (e.g. WB alternaria/rosette/tikka) must not become output heads
    classes = {c: sorted(man[(man.crop == c) & (man.split == "train")].canonical_id.unique()) for c in CROPS}
    tr, va = man[man.split == "train"], man[man.split == "val"]
    if a.smoke: tr, va = tr.groupby("crop").head(8), va.groupby("crop").head(4)
    hp = dict(backbone="efficientnet_v2_s", weights="IMAGENET1K_V1", img=224, bs=a.bs, epochs=a.epochs, warmup_head_epochs=2,
              lr_head=3e-4, lr_full=1e-4, wd=0.05, label_smoothing=0.1, sampler="class-balanced (inverse sqrt freq)",
              early_stop="val mean macro-F1, patience 5", dropout=0.3)
    cfg_hash = hashlib.sha256(json.dumps(hp, sort_keys=True).encode()).hexdigest()[:8]

    # ---- stable experiment directory (no date): a resumed seed continues in the SAME directory
    if a.resume not in ("auto", "none"):
        resume_path = Path(a.resume); od = resume_path.parent; exp_id = od.name
    else:
        exp_id = f"UZ-M4-v1.0-{cfg_hash}-s{a.seed}" + ("-SMOKE" if a.smoke else "")
        od = Path(a.out) / exp_id; resume_path = od / "checkpoint_last.pt"
    od.mkdir(parents=True, exist_ok=True)
    ej = od / "experiment.json"
    prev = json.load(open(ej)) if ej.exists() else {}
    if prev.get("status") in ("completed", "experiment"):
        print(f"[resume] {exp_id} is already COMPLETED; nothing to do (never overwritten)."); return
    have_ckpt = resume_path.exists()
    if a.resume == "none" and have_ckpt:
        raise SystemExit(f"[resume] {resume_path} exists; refusing to restart from epoch 0 over it. Use --resume auto.")
    if a.resume not in ("auto", "none") and not have_ckpt:
        raise SystemExit(f"[resume] checkpoint not found: {resume_path}")

    # class-balanced sampling: weight ~ 1/sqrt(class freq)
    freq = tr.groupby("canonical_id").size(); w = tr.canonical_id.map(lambda k: 1 / math.sqrt(freq[k])).to_numpy()
    sampler = WeightedRandomSampler(torch.tensor(w, dtype=torch.double), num_samples=len(tr), replacement=True)
    kw = dict(num_workers=0 if a.smoke else a.workers, pin_memory=dev.type == "cuda")
    tl = DataLoader(DS(tr, pkg, classes, True), batch_size=a.bs, sampler=sampler, drop_last=True, **kw)
    vl = DataLoader(DS(va, pkg, classes, False), batch_size=a.bs, shuffle=False, **kw)
    steps = len(tl) if not a.smoke else min(len(tl), 2)
    cw = {c: None for c in CROPS}   # balancing via the sampler only (not also via loss weights: that would double-count)
    model = Model(classes).to(dev)
    amp = dev.type == "cuda"; scaler = torch.amp.GradScaler("cuda", enabled=amp)
    W = hp["warmup_head_epochs"]
    hist, best, bad, start_ep, opt, sched = [], -1.0, 0, 0, None, None
    gpu = torch.cuda.get_device_name(0) if dev.type == "cuda" else platform.processor() or platform.machine()
    started = prev.get("start_time", time.strftime("%Y-%m-%dT%H:%M:%S"))
    prior_train_s = float(prev.get("training_duration_s", 0) or 0)

    if have_ckpt:
        ck = torch.load(resume_path, map_location="cpu", weights_only=False)
        assert ck["classes"] == classes and ck["seed"] == a.seed and ck["config"]["hp"] == hp, "[resume] checkpoint does not match this configuration"
        model.load_state_dict(ck["model_state_dict"])
        start_ep = ck["last_completed_epoch"] + 1
        hist, best, bad = ck["history"], ck["best_val_mean_macro_f1"], ck["epochs_without_improvement"]
        for p in model.backbone.parameters(): p.requires_grad = not (start_ep < W)
        if start_ep not in (0, W) and start_ep < a.epochs:      # mid-phase: rebuild this phase's optimizer, then restore its state
            opt, sched = make_opt(model, hp, a.epochs, 0 if start_ep < W else W, steps)
            opt.load_state_dict(ck["optimizer_state_dict"])
            if ck.get("scheduler_state_dict") is not None: sched.load_state_dict(ck["scheduler_state_dict"])
        if ck.get("scaler_state_dict"): scaler.load_state_dict(ck["scaler_state_dict"])
        set_rng_state(ck["rng_state"])
        print(f"[resume] found checkpoint: {resume_path}\n[resume] last completed epoch {ck['last_completed_epoch']}, "
              f"best val macro-F1 {best:.4f}; resuming from epoch {start_ep}", flush=True)
        json.dump({"resumed_from": str(resume_path), "start_epoch": start_ep, "history_len": len(hist),
                   "model_state_sha": state_sha(model.state_dict()), "checkpoint_model_sha": state_sha(ck["model_state_dict"]),
                   "optimizer_state_sha": state_sha(opt.state_dict()) if opt is not None else None,
                   "checkpoint_optimizer_sha": state_sha(ck["optimizer_state_dict"]),
                   "optimizer_state_loaded": opt is not None, "phase_boundary_new_optimizer": start_ep in (0, W),
                   "time": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(od / f"resume_audit_{int(time.time())}.json", "w"), indent=1)
    else:
        print(f"[resume] no checkpoint in {od}; starting at epoch 0", flush=True)

    def write_experiment(status, last_ep, t_run):
        atomic_json({"experiment_id": exp_id, "model": "M4", "model_version": "v1.0", "dataset_version": "m4_v1",
                     "split_version": "m4_v1_split_seed20260925", "seed": a.seed, "hyperparameters": hp,
                     "status": status, "last_completed_epoch": last_ep, "best_val_mean_macro_f1": best,
                     "start_time": started, "last_checkpoint_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "training_duration_s": round(prior_train_s + t_run, 1),
                     "hardware": {"device": dev.type, "name": gpu, "torch": torch.__version__},
                     "checkpoint": "checkpoint_best.pt", "resume_checkpoint": "checkpoint_last.pt", "classes": classes,
                     "package_manifest_sha256": hashlib.sha256((pkg / "manifest.csv").read_bytes()).hexdigest(),
                     "license_data_use": "Trained on 5 CC BY 4.0 sources (see package ATTRIBUTION.md); ImageNet-pretrained torchvision weights",
                     "smoke": a.smoke, "notes": "test/external_test NOT evaluated here; independent evaluation on the Mac (eval_m4.py)"}, ej)

    def on_sigterm(signum, frame): raise Interrupted(f"signal {signum}")
    signal.signal(signal.SIGTERM, on_sigterm)
    t0 = time.time(); last_done = start_ep - 1
    write_experiment("running", last_done, 0)
    atomic_json(classes, od / "classes.json")
    try:
        for ep in range(start_ep, a.epochs):
            if bad >= 5: break                                   # early stop already reached before a disconnect
            frozen = ep < W
            for p in model.backbone.parameters(): p.requires_grad = not frozen
            if ep in (0, W):
                opt, sched = make_opt(model, hp, a.epochs, ep, steps)
            model.train(); tl_loss, n = 0.0, 0
            for i, (x, cr, y) in enumerate(tl):
                with torch.autocast("cuda", enabled=amp):
                    loss = per_crop_loss(model(x.to(dev), cr), cr, y.to(dev), cw, hp["label_smoothing"])
                opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
                tl_loss += loss.item(); n += 1
                if a.smoke and i >= 1: break
            v = evaluate(model, vl, dev, classes)
            hist.append({"epoch": ep, "train_loss": tl_loss / max(n, 1), "val": v, "elapsed_s": prior_train_s + time.time() - t0})
            print(json.dumps({"epoch": ep, "loss": round(tl_loss / max(n, 1), 4), "val_mean_macro_f1": round(v["mean_macro_f1"], 4)}), flush=True)
            if v["mean_macro_f1"] > best:
                best, bad = v["mean_macro_f1"], 0
                atomic_torch({"model": model.state_dict(), "classes": classes, "crops": CROPS, "epoch": ep, "hp": hp}, od / "checkpoint_best.pt")
            else:
                bad += 1
            # ---- epoch fully done: persist resume state atomically, then history, then status
            atomic_torch({"model_state_dict": model.state_dict(), "optimizer_state_dict": opt.state_dict(),
                          "scheduler_state_dict": sched.state_dict() if sched is not None else None,
                          "scaler_state_dict": scaler.state_dict() if amp else None,
                          "last_completed_epoch": ep, "best_val_mean_macro_f1": best, "epochs_without_improvement": bad,
                          "history": hist, "seed": a.seed, "classes": classes, "rng_state": rng_state(),
                          "config": {"hp": hp, "args": {k: v for k, v in vars(a).items() if not k.startswith("_")}}},
                         od / "checkpoint_last.pt")
            atomic_json(hist, od / "history.json")
            last_done = ep
            write_experiment("running", last_done, time.time() - t0)
            print(f"[checkpoint] epoch {ep} saved -> {od / 'checkpoint_last.pt'}", flush=True)
            if a._test_hard_exit_after_epoch is not None and ep == a._test_hard_exit_after_epoch:
                os._exit(137)                                    # simulate Colab runtime loss: no cleanup, status stays 'running'
            if bad >= 5: break
    except (KeyboardInterrupt, Interrupted) as e:
        write_experiment("interrupted", last_done, time.time() - t0)
        print(f"[resume] INTERRUPTED ({e}). Last completed epoch {last_done}. Resume with the same command "
              f"(--resume auto) or --resume {od / 'checkpoint_last.pt'}", flush=True)
        raise SystemExit(130)
    except Exception:
        write_experiment("failed", last_done, time.time() - t0)
        print(f"[resume] FAILED after epoch {last_done}. checkpoint_last.pt is preserved in {od}; fix the error and rerun with --resume auto", flush=True)
        raise
    write_experiment("completed", last_done, time.time() - t0)
    print("done", exp_id)


if __name__ == "__main__":
    main()
