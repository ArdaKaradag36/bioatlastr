"""TASK 1: Latin-name exports from the WCVP Türkiye list (full run). Read-only on runs/full and results/.
Usage: pipeline/.venv/bin/python scripts/export_taxa.py"""
import pandas as pd
sp = pd.read_csv("runs/full/data/species.csv", keep_default_na=False, usecols=["species", "genus", "family", "endemic"])
cnt = pd.read_csv("results/species_marker_counts.csv", keep_default_na=False, usecols=["species", "n_rbcL", "n_matK", "n_ITS"])
t = sp.merge(cnt, on="species", how="left").fillna(0)
for m in ("n_rbcL", "n_matK", "n_ITS"):
    t[m] = t[m].astype(int)
t["has_any_sequence"] = ((t.n_rbcL + t.n_matK + t.n_ITS) > 0).astype(int)
t["endemic"] = t["endemic"].astype(int)
t = t.sort_values(["family", "genus", "species"]).rename(columns={"endemic": "endemic_to_turkiye"})
t.to_csv("exports/turkiye_taxa.csv", index=False)
fam = t.groupby("family").agg(species=("species", "size"), genera=("genus", "nunique"), endemics=("endemic_to_turkiye", "sum"),
                              species_with_sequences=("has_any_sequence", "sum")).reset_index().sort_values("species", ascending=False)
fam.to_csv("exports/families.csv", index=False)
gen = t.groupby(["genus", "family"]).agg(species=("species", "size"), species_with_sequences=("has_any_sequence", "sum")).reset_index().sort_values(["family", "genus"])
gen.to_csv("exports/genera.csv", index=False)
print(f"species {len(t)}, genera {len(gen)}, families {len(fam)}")
print("10 largest families:", ", ".join(f"{r.family} {r.species}" for r in fam.head(10).itertuples()))
