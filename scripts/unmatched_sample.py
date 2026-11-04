"""Classify a random sample of unmatched ENA names (runs/full). Usage: python scripts/unmatched_sample.py [n]"""
import re, sys, random
import pandas as pd
n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
R = "runs/full/data/"
um = pd.read_csv(R + "unmatched_names.csv", keep_default_na=False)
sp = set(pd.read_csv(R + "species.csv", keep_default_na=False)["species"])
syn = pd.read_csv(R + "synonyms.csv", keep_default_na=False)
names = pd.read_csv("data/raw/wcvp/wcvp_names.csv", sep="|", dtype=str, keep_default_na=False,
                    usecols=["plant_name_id", "taxon_rank", "taxon_status", "genus_hybrid", "genus", "species_hybrid", "species", "accepted_plant_name_id"])
names = names[names.taxon_rank == "Species"].copy()
names["bin"] = names.genus + " " + names.species
id2bin = dict(zip(names.plant_name_id, names["bin"]))
acc = names[names.taxon_status == "Accepted"]
accepted_all = set(acc["bin"])
by_name = names.groupby("bin")
turkish_ids = set(names.loc[names["bin"].isin(sp) & (names.taxon_status == "Accepted"), "plant_name_id"])
def norm(x):
    x = re.sub(r"\b(subsp|var|f|subvar)\..*$", "", x).strip()
    return " ".join(x.split()[:2])
def classify(raw):
    b = norm(raw)
    if re.search(r"\b(sp|cf|aff)\.?\b|\bx\b|×|\d", raw):
        return "c", "sp./cf./aff./hybrid/unusual name"
    if b in sp: return "c", "is a Turkish species (should have matched)"
    rows = names[names["bin"] == b]
    if rows.empty: return "c", "name not in WCVP species names (genus/other-rank/typo)"
    if (rows.taxon_status == "Accepted").any(): return "a", "accepted species, not native to Türkiye"
    targets = {id2bin.get(i, "") for i in rows.accepted_plant_name_id if i}
    if targets & sp: return "b", f"synonym of Turkish species {sorted(targets & sp)[0]}"
    return "c", f"synonym of non-Turkish species ({sorted(t for t in targets if t)[:1]})"
def run(sample, label):
    out = [classify(r) for r in sample.scientific_name]
    c = pd.Series([o[0] for o in out]).value_counts().to_dict()
    print(label, {k: c.get(k, 0) for k in "abc"}, "of", len(sample))
    return out
random.seed(42)
s1 = um.sample(n, random_state=42)
o1 = run(s1, "unique names (unweighted)")
import os; os.makedirs("results", exist_ok=True)
pd.DataFrame({"scientific_name": s1.scientific_name.values, "n_records": s1.n_records.values, "class": [o[0] for o in o1], "why": [o[1] for o in o1]}).to_csv("results/unmatched_sample_%d.csv" % n, index=False)
for (k, why), nm in list(zip(o1, s1.scientific_name)):
    if k == "b": print("   b:", nm, "->", why)
print("   examples c:", [(nm, why[:45]) for (k, why), nm in zip(o1, s1.scientific_name) if k == "c"][:6])
s2 = um.sample(n, weights=um.n_records.astype(int), random_state=7)
run(s2, "records-weighted")
