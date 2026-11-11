# UZHAVAN AI: External SSD Backup Plan

**Date:** 2026-11-08. **Status: BLOCKED, no external SSD is mounted. No copy was performed.**

## 1. Drive detection (task 1-3)
| Check | Result |
|---|---|
| `ls /Volumes` | only `Macintosh HD -> /` |
| `diskutil list external` | no external disks |
| `mount` | only internal APFS system volumes |
| Internal disk free space | 104 GiB of 460 GiB (not a substitute: same disk) |

Nothing was formatted, erased, mounted or written. Per your rule, I stopped at the copy step. Tasks 4-6 (manifest, licence check, procedure) are read-only preparation and are finished below. Tasks 7-9 wait for a drive **and your go-ahead**.

## 2. Drive requirements
- **Capacity:** the selected categories total about **31 GB** (28.9 GiB). Get at least 64 GB free; 256 GB or more leaves room for later backups and a second generation.
- **Filesystem:** APFS (Encrypted), or APFS with a password set in Disk Utility. This is macOS-only but keeps permissions, symlinks and file names. Avoid exFAT or FAT32 for this backup: they cannot encrypt and mangle some metadata. FAT32 also caps files at 4 GB.
- **Encryption is mandatory** because the backup holds `backups/` SQL dumps with real data and licence-restricted datasets. Do not format the drive from here. If it needs formatting, do it yourself in Disk Utility; I will not run any erase command.
- Disk Utility: choose a name like `UZHAVAN_BACKUP`; I will target `/Volumes/UZHAVAN_BACKUP` only after you confirm the name.

## 3. Backup manifest (task 4)
Full machine-readable list: `reports/artifacts/uzhavan_external_backup_manifest.csv` (13 category rows + 46 dataset licence rows).

| ID | Category | Approx size | Licence | Cloud | Priority |
|---|---|---|---|---|---|
| C01 | Original source archive (`…121229.tar.gz`) | 47.5 MB | own code | n/a | 1 |
| C02 | Per-file manifest (1,748 files) | 0.2 MB | own | n/a | 1 |
| C03 | Addendum archive (Sprint 1 + Phase 1) | small | own code | n/a | 1 |
| C04 | Documentation (`uzhavan_platform/docs`, `reports`) | ~3 MB | own | n/a | 1 |
| C05 | ChromaDB persistent index (`rag/chroma`, `uzhavan_platform/rag/chroma`) | 12.5 MB | derived from TNAU crawl | no | 2 |
| C06 | M4 checkpoints + packages + registry files | 2.2 GB | own, derives from SICKLE | no | 2 |
| C07 | SICKLE checkpoints (`runs/`, 156 files) | 3.3 GB | derives from SICKLE | no | 2 |
| C08 | SICKLE dataset | 14.9 GB | UNVERIFIED | no | 3 |
| C09 | SICKLE toy dataset | 1.0 GB | UNVERIFIED | no | 3 |
| C10 | `uzhavan_data` (46 datasets + metadata + licence records) | 6.3 GB | mixed, 19 UNVERIFIED | no | 2 |
| C11 | `datasets/` | 14 MB | unknown | no | 3 |
| C12 | TNAU crawl corpus | 1.1 GB | UNVERIFIED | no | 3 |
| C13 | `backups/` older DB dumps | 7 MB | real data | NEVER | 2 |

**Gap to fix first:** `docs/srs/` and `docs/architecture/` are still empty. The SRS and SDD `.docx` files have not been copied in, so they are in no backup. Copy them in, then refresh C01-C03 before the SSD run (or add them as C14).

Not included (regenerable): `.venv*`, `node_modules`, `uzhavan_flutter/build`, `.dart_tool`, the two 300+ MB listing text files, `mini project/` (128 MB of presentations; add it if you want it, it is not on this list because it was excluded from the first archive).

## 4. Licence check (task 5)
Source: `uzhavan_data/00_metadata/master_catalog.json`. 46 datasets; **19 are UNVERIFIED** (the catalogue itself says so): SICKLE (access on request), IMD rainfall and temperature grids, NASA POWER, ICAR-NBSS and SLUSI soil maps, Soil Health Card, Tamil Mannvalam, TNAU resources/crawl/guides, NHB, Season & Crop Report, Agmarknet, e-NAM, DMI/TNAU bulletins, scheme pages.
Others are CC BY 4.0 (7), Copernicus open terms (2), USGS public domain, CDS CC-BY, Open-Meteo CC BY 4.0 (attribution required).

Rules applied:
1. A private, encrypted copy on your own drive for backup is not redistribution, so it is acceptable for all categories. **No cloud upload** for any category (also what you required).
2. Do not hand the SSD or its dataset folders to third parties until each UNVERIFIED licence is resolved.
3. Keep `uzhavan_data/00_metadata/` (catalog, source registries) with the data; it is the licence record.
4. CC-BY datasets need attribution if ever shared; see each row in the CSV.
I have not contacted any data owner and did not verify any licence online.

## 5. Copy procedure (task 6): to run only after approval
Replace `$DST` with the confirmed mount (e.g. `/Volumes/UZHAVAN_BACKUP/uzhavan_backup_20261108`). `rsync` on macOS may be the old 2.6.9 or `openrsync`; run `rsync --version` first and drop any flag it rejects. All sources are read-only for this procedure. No `--delete` flag is ever used.

```
# 0. Preconditions
diskutil info "/Volumes/UZHAVAN_BACKUP" | grep -E "File System|Encrypted|Free|Total"   # expect APFS, Encrypted Yes, >=64 GB free
mkdir -p "$DST"/{source,docs,chroma,m4,sickle_checkpoints,sickle_data,uzhavan_data,crawl,db_dumps,manifests}

# 1. Priority 1: source archives (copy, then compare hashes)
SRC=~/Desktop/uzhavan_backups_sprint1
cp -p "$SRC"/* "$DST/source/"
cd "$DST/source" && shasum -a 256 -c *.sha256     # each *.tar.gz must say OK; compare the .files.sha256 hash with the report

# 2. Priority 2: rsync each directory (trailing slashes matter)
cd /Users/ajaikumarn/Desktop/agri
rsync -a uzhavan_platform/rag/chroma/ "$DST/chroma/platform_chroma/"      # no process may have it open
rsync -a rag/chroma/                  "$DST/chroma/root_chroma/"
rsync -a uzhavan_ml/runs_m4/ "$DST/m4/runs_m4/"; rsync -a uzhavan_ml/packages/ "$DST/m4/packages/"
rsync -a uzhavan_ml/registry.json uzhavan_ml/model_status.json uzhavan_ml/model_registry.md "$DST/m4/"
rsync -a runs/       "$DST/sickle_checkpoints/runs/"
rsync -a uzhavan_data/ "$DST/uzhavan_data/"
rsync -a backups/    "$DST/db_dumps/"
# 3. Priority 3
rsync -a sickle_dataset/ "$DST/sickle_data/sickle_dataset/"; rsync -a sickle_toy_dataset/ "$DST/sickle_data/sickle_toy_dataset/"
rsync -a datasets/ "$DST/sickle_data/datasets/"; rsync -a tnau_crawler/knowledge_base/ "$DST/crawl/knowledge_base/"
```

### Verification (task 8)
Per-file SHA256 at source and destination, compared as sorted lists:
```
for d in chroma m4 sickle_checkpoints uzhavan_data db_dumps sickle_data crawl; do
  (cd "$DST/$d" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256) > "$DST/manifests/$d.dst.sha256"
done
# source side: same find|shasum run from the matching source dir -> manifests/<d>.src.sha256, then:
diff <(sort X.src.sha256) <(sort X.dst.sha256) && echo "X: IDENTICAL"
```
Extra checks: file counts equal (`find . -type f | wc -l`); the 4,765 / 150,631+2,150,553+897,307 counts from the catalogue match; the checksum files that already exist under `uzhavan_data/*/metadata/` and `01_sickle/checksums.txt` pass at the destination; `git fsck` clean after extracting C01 to a scratch dir; Chroma opens read-only and shows 520 embeddings (open a **copy**, never the backup itself).
Hashing about 31 GB takes a while (SICKLE has about 3.2 M files); run it in the background and do not interrupt it. Where a source file changes during the copy, re-run that directory.

### Restore inventory and verification report (task 9)
After the run I will produce `reports/UZHAVAN_EXTERNAL_BACKUP_VERIFICATION.md` with: drive identity, filesystem and encryption state, per-category file counts, byte totals, hash comparison results, any mismatches, and a restore table:
| Need | Restore from | Command pattern |
|---|---|---|
| Source tree | C01 then C03 over it | `tar -xzf` into an empty directory; check against `.files.sha256` |
| Chroma | `chroma/` | copy directory back with the app stopped |
| Models / data | `m4/`, `sickle_*`, `uzhavan_data/` | `rsync -a` back to original paths |
| Env secrets | **not in any backup** | recreate from `.env.example` + your password manager |

**Secrets note:** real `.env` files are in no archive by design. If you want them backed up, store them in a password manager, not on the SSD in plain text.

## 6. Stop conditions I will honour
- No drive, or drive not encrypted, or under 64 GB free → stop and report.
- Any hash mismatch → report, do not mark that category as verified, do not delete anything.
- No format/erase, no `--delete`, no writes to the source tree except the scratch hash lists (kept in the scratchpad and `$DST/manifests`).

## 7. Constraints confirmed this task
Nothing staged/committed/pushed; no source modified; PostgreSQL/Redis/Ollama untouched; M4/satellite checkpoints only measured (size), not read or altered; no training; no cloud upload; original and addendum archives unmodified (they are listed only).

**Next step needed from you:** attach and unlock the encrypted SSD, give me the volume name, and say "go" for the copy. I stop here.
