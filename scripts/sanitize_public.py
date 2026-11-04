"""Scrub personal data (voucher/collector names, localities, risky free text) from published sequence data.
Applies to web/public/data/species/*.json and data/sequence_table.csv. Idempotent; run by publish_full.sh."""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacy_lib import sanitize_sequence

ROOT = Path(__file__).resolve().parents[1]
n = 0
for f in sorted((ROOT / "web/public/data/species").glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    for sp in d.values():
        for marker, m in sp.get("markers", {}).items():
            m["sequences"] = [sanitize_sequence(q, sp["name"], marker) for q in m.get("sequences", [])]; n += len(m["sequences"])
    f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
p = ROOT / "data/sequence_table.csv"
if p.exists():
    t = pd.read_csv(p, keep_default_na=False, dtype=str)
    rows = [sanitize_sequence(r, r.get("organism", ""), r.get("marker", "")) for r in t.to_dict("records")]
    pd.DataFrame(rows, columns=t.columns).to_csv(p, index=False)
print("sanitised sequence records (site):", n)
