"""Throughput/memory benchmark for EfficientNetV2-S on this machine. NOT a training run: synthetic steps only, no weights saved."""
import time, json, os, sys, platform
import torch, torchvision
from PIL import Image
import pandas as pd

dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
w = torchvision.models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
model = torchvision.models.efficientnet_v2_s(weights=w)
model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 46)
model.to(dev).train()
opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
res = {"device": str(dev), "torch": torch.__version__, "machine": platform.machine(), "weights": "IMAGENET1K_V1 (torchvision)"}
for bs in (16, 32):
    x = torch.randn(bs, 3, 224, 224, device=dev); y = torch.randint(0, 46, (bs,), device=dev)
    try:
        for i in range(13):
            if i == 3:
                (torch.mps.synchronize() if dev.type == "mps" else None); t = time.time()
            opt.zero_grad(); loss = torch.nn.functional.cross_entropy(model(x), y); loss.backward(); opt.step()
        (torch.mps.synchronize() if dev.type == "mps" else None)
        ips = 10 * bs / (time.time() - t)
        res[f"train_img_per_s_bs{bs}"] = round(ips, 1)
        res[f"mps_driver_mem_gb_bs{bs}"] = round(torch.mps.driver_allocated_memory() / 1e9, 2) if dev.type == "mps" else None
    except RuntimeError as e:
        res[f"bs{bs}_error"] = str(e)[:200]
# JPEG decode + resize cost on real images (CPU, single process)
m = pd.read_csv(os.path.expanduser("~/Desktop/agri/uzhavan_data/06_disease_pest/processed/m4_v1/m4_v1_manifest.csv"))
m = m[m.quarantine.isna() | (m.quarantine == "")]
for src, g in m.groupby("source"):
    s = g.sample(min(40, len(g)), random_state=0); t = time.time()
    for p in s.abs_path: Image.open(p).convert("RGB").resize((256, 256))
    res[f"decode_img_per_s_{src}"] = round(len(s) / (time.time() - t), 1)
n_train = int((m.split == "train").sum())
best = max(v for k, v in res.items() if k.startswith("train_img_per_s"))
res["train_images"] = n_train
res["est_minutes_per_epoch_compute_only"] = round(n_train / best / 60, 1)
res["est_hours_3seeds_x30epochs_compute_only"] = round(3 * 30 * n_train / best / 3600, 1)
print(json.dumps(res, indent=1))
json.dump(res, open(sys.argv[1], "w"), indent=1)
