"""Sanity checks of the full run (runs/full) before it may be published."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "runs" / "full"
errs = []
need = ["web_data/stats.json", "web_data/meta.json", "web_data/gaps.json", "results/coverage_by_marker.csv",
        "results/discrimination_by_marker.csv", "results/skipped_groups.csv", "docs/rapor_taslagi.md", "data/species.csv"]
for f in need:
    if not (R / f).exists():
        errs.append(f"missing {f}")
if not errs:
    st = json.loads((R / "web_data/stats.json").read_text())
    tot = st["totals"]
    n_species = sum(1 for _ in open(R / "data/species.csv")) - 1
    print("species:", n_species, "totals:", {k: tot[k] for k in list(tot)[:6]})
    if n_species < 8000: errs.append(f"too few species ({n_species}); WCVP TUR list expected ~10,000")
    if not (R / "web_data/species").is_dir() or len(list((R / "web_data/species").glob("*.json"))) < 500:
        errs.append("species shards missing / too few genera")
    for m, v in st["markers"].items():
        if v["sequences"] < 1000: errs.append(f"{m}: only {v['sequences']} sequences")
    n_ana, n_skip = st["groups_analysed"], st["groups_skipped"]
    print("groups analysed/skipped:", n_ana, n_skip, "timeouts/errors:", st.get("groups_skipped_timeout_or_error"), "subsampled:", st.get("groups_subsampled"))
    if n_ana < 100: errs.append("too few analysed groups")
print("ERRORS:", errs) if errs else print("validation passed")
sys.exit(1 if errs else 0)
