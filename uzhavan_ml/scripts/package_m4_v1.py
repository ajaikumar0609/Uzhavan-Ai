"""Build the cloud training package for M4 v1: resized copies (shorter side 288 px, JPEG q95) of NON-quarantined images only.
All five sources are CC BY 4.0 (verified in their metadata JSONs), which permits copying/adaptation with attribution.
Raw data is untouched. Output: uzhavan_ml/packages/m4_v1/{images/,manifest.csv,ATTRIBUTION.md,package.json}"""
import json, hashlib, sys
from pathlib import Path
from multiprocessing import Pool
import pandas as pd
from PIL import Image, ImageOps

D = Path.home() / "Desktop/agri/uzhavan_data/06_disease_pest"
PKG = Path.home() / "Desktop/agri/uzhavan_ml/packages/m4_v1"; (PKG / "images").mkdir(parents=True, exist_ok=True)
SHORT = 288
man = pd.read_csv(D / "processed/m4_v1/m4_v1_manifest.csv")
man = man[man.quarantine.isna()].copy()
man["pkg_path"] = "images/" + man.sha256 + ".jpg"

def work(args):
    src, dst = args
    out = PKG / dst
    if out.exists(): return dst, None
    try:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        w, h = im.size; s = SHORT / min(w, h)
        if s < 1: im = im.resize((round(w * s), round(h * s)), Image.BICUBIC)
        im.save(out, "JPEG", quality=95); return dst, None
    except Exception as e:
        return dst, str(e)

if __name__ == "__main__":
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as p:
        errs = [r for r in p.imap_unordered(work, zip(man.abs_path, man.pkg_path), chunksize=64) if r[1]]
    cols = ["pkg_path", "source", "crop", "canonical_id", "original_label", "split", "group_id", "sha256"]
    man[cols].to_csv(PKG / "manifest.csv", index=False)
    lic = {}
    for s in man.source.unique():
        m = json.load(open(D / f"metadata/{s}.json"))
        lic[s] = {"name": m.get("dataset_name"), "license": m.get("license"), "source_url": m.get("source_url"), "version": m.get("version")}
        assert "CC BY 4.0" in str(m.get("license")), f"licence not CC BY 4.0 for {s}: stop"
    (PKG / "ATTRIBUTION.md").write_text("# M4 v1 training package: data attribution\n\nImages are resized copies (shorter side 288 px). All sources are CC BY 4.0.\n\n" +
        "\n".join(f"- **{v['name']}** ({s}), {v['version']}. Licence: {v['license']}. Source: {v['source_url']}" for s, v in lic.items()) + "\n")
    size = sum(f.stat().st_size for f in (PKG / "images").glob("*.jpg"))
    json.dump({"package": "m4_v1", "dataset_version": "m4_v1", "images": int(len(man)), "errors": errs, "bytes": size, "short_side_px": SHORT,
               "manifest_sha256": hashlib.sha256((PKG / "manifest.csv").read_bytes()).hexdigest(), "licences": lic},
              open(PKG / "package.json", "w"), indent=1)
    print(len(man), "images", round(size / 1e9, 2), "GB", "errors", len(errs))
