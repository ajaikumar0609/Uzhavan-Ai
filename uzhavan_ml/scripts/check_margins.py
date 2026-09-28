import torch
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'scripts')
import train_m4 as tm
import json
from pathlib import Path

root = Path('.')
manifest_path = root / 'm4_v2/manifests/groundnut_v2.csv'
pkg = root / 'm4_v1'
with open('m4_v2/classes.json') as f:
    classes = json.load(f)

man = pd.read_csv(manifest_path)
h_df = man[(man.crop == 'groundnut') & (man.split == 'external_test') & (man.canonical_id == 'groundnut__healthy_or_abiotic')].copy().reset_index(drop=True)

ds = tm.DS(h_df, pkg, classes, False)
loader = DataLoader(ds, batch_size=64, shuffle=False)

for sname, ck_path in [
    ('Seed_42', 'runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust/checkpoint_best.pt'),
    ('Seed_1337', 'runs_m4_v2_2/UZ-M4-v2.2-groundnut-s2-wce-balanced-rust/checkpoint_best.pt'),
    ('Seed_2024', 'runs_m4_v2_2/UZ-M4-v2.2-groundnut-s3-wce-balanced-rust/checkpoint_best.pt')
]:
    ck = torch.load(ck_path, map_location='cpu', weights_only=False)
    model = tm.Model(ck['classes'])
    model.load_state_dict(ck['model'])
    model.eval()

    head_weight = model.heads['groundnut'].weight.data
    head_bias = model.heads['groundnut'].bias.data
    print(f'=== {sname} Head Parameters (Groundnut) ===', flush=True)
    print('  Weights L2 Norm per class (Healthy, Rust, Tikka):', [round(float(torch.norm(head_weight[i]).item()), 4) for i in range(3)], flush=True)
    print('  Biases per class (Healthy, Rust, Tikka)          :', [round(float(b.item()), 4) for b in head_bias], flush=True)

    logits_list = []
    with torch.no_grad():
        for x, cr, _ in loader:
            lg = model(x, cr)
            for l in lg:
                logits_list.append(l.cpu().numpy())
    L = np.stack(logits_list)
    print('  Mean Logits on Healthy (N=600):', flush=True)
    print('    Healthy:', round(float(L[:, 0].mean()), 4), 'Rust:', round(float(L[:, 1].mean()), 4), 'Tikka:', round(float(L[:, 2].mean()), 4), flush=True)
    print('    Margin (Logit[Healthy] - Logit[Tikka]): mean =', round(float((L[:, 0] - L[:, 2]).mean()), 4), 'median =', round(float(np.median(L[:, 0] - L[:, 2])), 4), flush=True)
