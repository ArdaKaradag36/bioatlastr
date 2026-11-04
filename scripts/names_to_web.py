"""Add Turkish names (data/names/turkish_names.csv) to the site data: species_index.json ('tr'), species/<genus>.json
('common_name_tr', 'names_tr') and taxon_names.json (genus / family names + counts). Re-run after publish_full.sh.
Usage: pipeline/.venv/bin/python scripts/names_to_web.py [web_data_dir]"""
import json, sys
from collections import defaultdict
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from names_lib import ascii_key, source_info

ROOT = Path(__file__).resolve().parents[1]
W = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web" / "public" / "data"
df = pd.read_csv(ROOT / "data/names/turkish_names.csv", keep_default_na=False)
def label(fam: str) -> str:
    return source_info(fam)[0]
# src_family is not in the CSV: derive it from the source text
def fam(src: str) -> str:
    if src.startswith("Wikidata"): return "wikidata"
    if src.startswith("tr.wikipedia"): return "trwiki"
    if src.startswith("iNaturalist"): return "inaturalist"
    return "gbif:" + src[src.find("(") + 1:src.rfind(")")]
df["fam"] = df.source.map(fam)
store = {"species": {}, "genus": {}, "family": {}}
for (rank, latin), g in df.groupby(["rank", "latin_name"]):
    ent = []
    for _, h in g.groupby(g.turkish_name.map(ascii_key), sort=False):
        srcs = {}
        for r in h.itertuples():
            i = source_info(r.fam); srcs.setdefault(r.fam, {"l": i[0], "u": r.source_id_or_url, "t": i[1], "c": "open" if i[2] == "open" else "nc", "lic": i[3]})
        ent.append({"n": h.turkish_name.iloc[0], "a": int(h.ambiguous.any()), "src": list(srcs.values())})
    ent.sort(key=lambda e: (-len(e["src"]), e["n"]))
    store[rank][latin] = ent
# species index
idx = json.loads((W / "species_index.json").read_text())
for e in idx:
    names = store["species"].get(e["name"], [])
    e["tr"] = "; ".join(x["n"] for x in names[:3])[:70]
    rest = "; ".join(x["n"] for x in names[3:])[:200]  # further names: searchable, not displayed in lists
    e.pop("ts", None)
    if rest: e["ts"] = rest
(W / "species_index.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
# species shards
for f in (W / "species").glob("*.json"):
    d = json.loads(f.read_text()); changed = False
    for slug, v in d.items():
        names = store["species"].get(v["name"], [])
        v["names_tr"] = names; v["common_name_tr"] = "; ".join(x["n"] for x in names[:3]); changed = True
    f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
n_sp = len(idx)
meta = {"species_total": n_sp, "species_with_name": len(store["species"]), "genus_with_name": len(store["genus"]),
        "family_with_name": len(store["family"]), "ambiguous_species_names": int(df[(df["rank"] == "species") & df.ambiguous].turkish_name.map(ascii_key).nunique()),
        "sources": sorted(set(label(x) for x in df.fam)),
        "sources_info": [{"label": source_info(k)[0], "tier": source_info(k)[1], "license_class": source_info(k)[2], "license": source_info(k)[3],
                          "url": source_info(k)[4], "rows": int(len(g))} for k, g in df.groupby("fam")],
        "excluded_rows": int(pd.read_csv(ROOT / "data/names/excluded_sources_summary.csv")["rows"].sum())}
(W / "taxon_names.json").write_text(json.dumps({"genus": store["genus"], "family": store["family"], "meta": meta}, ensure_ascii=False, separators=(",", ":")))
print(meta)
