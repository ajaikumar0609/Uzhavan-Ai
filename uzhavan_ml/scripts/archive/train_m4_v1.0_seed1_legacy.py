"""M4 v1 training: EfficientNetV2-S shared backbone + one classification head per crop (crop is supplied by the farmer/UI).
Spec: training_specification.md §3 M4 + §7 sign-off. Runs on CUDA (cloud) or MPS/CPU (smoke tests only).

usage: python train_m4.py --pkg /path/to/m4_v1 --out runs/ --seed 1 [--epochs 30] [--smoke]
Writes <out>/<experiment_id>/{experiment.json, history.json, checkpoint_best.pt, classes.json}. Never overwrites an existing experiment dir.
"""
import argparse, json, math, os, platform, random, time, hashlib, subprocess
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=30); ap.add_argument("--bs", type=int, default=32); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true", help="2 batches, tiny subset; for pipeline checks only")
    a = ap.parse_args()
    seed_all(a.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
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
    exp_id = f"UZ-M4-v1.0-{time.strftime('%Y%m%d')}-{cfg_hash}-s{a.seed}" + ("-SMOKE" if a.smoke else "")
    od = Path(a.out) / exp_id; od.mkdir(parents=True, exist_ok=False)   # never overwrite
    # class-balanced sampling: weight ~ 1/sqrt(class freq)
    freq = tr.groupby("canonical_id").size(); w = tr.canonical_id.map(lambda k: 1 / math.sqrt(freq[k])).to_numpy()
    sampler = WeightedRandomSampler(torch.tensor(w, dtype=torch.double), num_samples=len(tr), replacement=True)
    kw = dict(num_workers=0 if a.smoke else a.workers, pin_memory=dev.type == "cuda")
    tl = DataLoader(DS(tr, pkg, classes, True), batch_size=a.bs, sampler=sampler, drop_last=True, **kw)
    vl = DataLoader(DS(va, pkg, classes, False), batch_size=a.bs, shuffle=False, **kw)
    cw = {c: None for c in CROPS}   # balancing via the sampler only (not also via loss weights: that would double-count)
    model = Model(classes).to(dev)
    amp = dev.type == "cuda"; scaler = torch.amp.GradScaler("cuda", enabled=amp)
    hist, best, bad, t0 = [], -1, 0, time.time()
    for ep in range(a.epochs):
        frozen = ep < hp["warmup_head_epochs"]
        for p in model.backbone.parameters(): p.requires_grad = not frozen
        if ep in (0, hp["warmup_head_epochs"]):
            opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=hp["lr_head"] if frozen else hp["lr_full"], weight_decay=hp["wd"])
            sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, (a.epochs - ep)) * len(tl))
        model.train(); tl_loss, n = 0.0, 0
        for i, (x, cr, y) in enumerate(tl):
            with torch.autocast("cuda", enabled=amp):
                loss = per_crop_loss(model(x.to(dev), cr), cr, y.to(dev), cw, hp["label_smoothing"])
            opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            tl_loss += loss.item(); n += 1
            if a.smoke and i >= 1: break
        v = evaluate(model, vl, dev, classes)
        hist.append({"epoch": ep, "train_loss": tl_loss / max(n, 1), "val": v, "elapsed_s": time.time() - t0})
        print(json.dumps({"epoch": ep, "loss": round(tl_loss / max(n, 1), 4), "val_mean_macro_f1": round(v["mean_macro_f1"], 4)}), flush=True)
        if v["mean_macro_f1"] > best:
            best, bad = v["mean_macro_f1"], 0
            torch.save({"model": model.state_dict(), "classes": classes, "crops": CROPS, "epoch": ep, "hp": hp}, od / "checkpoint_best.pt")
        else:
            bad += 1
        json.dump(hist, open(od / "history.json", "w"), indent=1)
        if bad >= 5 or (a.smoke and ep >= 0): break
    gpu = torch.cuda.get_device_name(0) if dev.type == "cuda" else platform.processor() or platform.machine()
    json.dump({"experiment_id": exp_id, "model": "M4", "model_version": "v1.0", "dataset_version": "m4_v1",
               "split_version": "m4_v1_split_seed20260925", "seed": a.seed, "hyperparameters": hp,
               "training_duration_s": round(time.time() - t0, 1), "hardware": {"device": dev.type, "name": gpu, "torch": torch.__version__},
               "best_val_mean_macro_f1": best, "checkpoint": "checkpoint_best.pt", "classes": classes,
               "package_manifest_sha256": hashlib.sha256((pkg / "manifest.csv").read_bytes()).hexdigest(),
               "license_data_use": "Trained on 5 CC BY 4.0 sources (see package ATTRIBUTION.md); ImageNet-pretrained torchvision weights",
               "status": "smoke" if a.smoke else "experiment", "notes": "test/external_test NOT evaluated here; independent evaluation on the Mac (eval_m4.py)"},
              open(od / "experiment.json", "w"), indent=1)
    json.dump(classes, open(od / "classes.json", "w"), indent=1)
    print("done", exp_id)


if __name__ == "__main__":
    main()
