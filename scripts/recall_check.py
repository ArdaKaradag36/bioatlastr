"""Recall check: our marker queries vs broader term sets for a few genera. Output: logs/recall_check.txt"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import pandas as pd
from barcode_atlas.config import load_config
from barcode_atlas.ena import EnaClient, PORTAL, SEARCH_FIELDS, classify_record, parse_tsv

cfg = load_config("pipeline/config.yaml")
M = cfg["markers"]
client = EnaClient(cfg["ena"])
res = pd.read_csv("data/ena_genus_resolution.csv", keep_default_na=False).set_index("wcvp_genus")
BROAD = {
    "ITS": ["internal transcribed spacer", "ITS1", "ITS2", "5.8S", "18S-26S", "nrDNA", "ITS"],
    "matK": ["maturase K", "matK", "trnK"],
    "rbcL": ["rbcL", "ribulose", "RuBisCO", "large subunit"],
}

def fetch(tid, terms, m):
    w = " OR ".join(f'description="*{t}*"' for t in terms)
    q = f"tax_tree({tid}) AND ({w}) AND base_count>={M[m]['min_length']} AND base_count<={M[m]['max_length']}"
    return {r["accession"]: r for r in parse_tsv(client.get_text(f"{PORTAL}/search", {"result": "sequence", "query": q, "fields": "accession,description,scientific_name,base_count", "format": "tsv", "limit": 0}))}

out = []
for g in ("Salvia", "Quercus", "Rosa"):
    tid = int(res.loc[g, "ena_tax_id"])
    for m in ("ITS", "matK", "rbcL"):
        cur = fetch(tid, M[m]["ena_terms"], m)
        broad = fetch(tid, BROAD[m], m)
        valid = lambda rows: {a for a, r in rows.items() if classify_record(r["description"], int(r["base_count"]), M) == (m, None)}
        extra = {a: r for a, r in broad.items() if a not in cur}
        # extras that would be valid barcode records of marker m if the include regex were broadened
        line = (f"{g:8s} {m:5s} current_query={len(cur):5d} (valid {len(valid(cur)):5d}) broader_query={len(broad):5d} (valid {len(valid(broad)):5d}) extra={len(extra)}")
        out.append(line); print(line, flush=True)
        for a, r in list(extra.items())[:4]:
            out.append(f"      e.g. {a}: {r['description'][:95]}")
Path("logs/recall_check.txt").write_text("\n".join(out) + "\n")
print("DONE")
