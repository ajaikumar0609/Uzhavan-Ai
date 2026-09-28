"""M6 forecast eligibility per market x commodity (sign-off 2026-09-25; rule fixed before any modelling).

Definitions:
  week coverage(year)  = ISO weeks with >=1 QC-pass modal price / weeks in that year
  complete year        = calendar year (2015..2025) with week coverage >= 0.80
  ELIGIBLE             = >= 3 complete years AND week coverage >= 0.80 in the evaluation window 2025-01-01..2026-09-24
  PREFERRED            = ELIGIBLE and >= 5 complete years
  otherwise            = CURRENT-PRICE ONLY (no forecast)
Coconut is held out until its unit issue (per quintal vs per 1000 nuts) is resolved (spec N6).
"""
import json
from pathlib import Path
import pandas as pd

P = Path.home() / "Desktop/agri/uzhavan_data/08_market/processed/tn_mandi_prices.parquet"
OUT = Path.home() / "Desktop/agri/uzhavan_data/08_market/processed/m6_eligibility_v1.csv"
d = pd.read_parquet(P, columns=["date", "market", "commodity", "modal_price", "qc_pass"])
d = d[d.qc_pass & d.modal_price.gt(0)].copy()
d["date"] = pd.to_datetime(d.date); iso = d.date.dt.isocalendar(); d["yw"] = iso.year.astype(str) + "-" + iso.week.astype(str)
d["year"] = iso.year
rows = []
for (m, c), g in d.groupby(["market", "commodity"]):
    cov = {}
    for y in range(2015, 2026):
        nweeks = pd.Timestamp(f"{y}-12-28").isocalendar().week
        cov[y] = g[g.year == y].yw.nunique() / nweeks
    ev = g[(g.date >= "2025-01-01") & (g.date <= "2026-09-24")]
    ev_weeks = pd.date_range("2025-01-01", "2026-09-24", freq="W-MON").size
    ev_cov = ev.yw.nunique() / ev_weeks
    complete = sum(v >= 0.80 for v in cov.values())
    elig = complete >= 3 and ev_cov >= 0.80
    status = ("HELD (coconut unit issue)" if c == "coconut" and elig else
              "ELIGIBLE-PREFERRED" if elig and complete >= 5 else "ELIGIBLE" if elig else "CURRENT-PRICE-ONLY")
    rows.append({"market": m, "commodity": c, "complete_years": complete, "eval_window_week_coverage": round(ev_cov, 3),
                 "first": g.date.min().date(), "last": g.date.max().date(), "n_obs": len(g), "status": status,
                 **{f"cov_{y}": round(v, 2) for y, v in cov.items()}})
r = pd.DataFrame(rows).sort_values(["commodity", "status", "market"]); r.to_csv(OUT, index=False)
s = r.groupby(["commodity", "status"]).size().unstack(fill_value=0)
print(s.to_string()); print("\ntotal pairs", len(r)); print(r.status.value_counts().to_string())
json.dump({"rule": __doc__, "pairs": len(r), "by_status": r.status.value_counts().to_dict(),
           "by_commodity": s.to_dict("index")}, open(OUT.with_suffix(".json"), "w"), indent=1, default=int)
