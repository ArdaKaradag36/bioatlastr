"""TASK 2: build Turkish common-name tables from the cached open sources (no names are written by hand).
Reads data/names/cache/*, runs/full/data/{species,synonyms}.csv, exports/turkiye_taxa.csv; writes data/names/turkish_names.csv and exports/*."""
import hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from names_lib import ascii_key, bad_title, clean, fold_key, is_latin_like, merge_variants, resolve_name, source_info, include_non_commercial

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "names" / "cache"
sp = pd.read_csv(ROOT / "runs/full/data/species.csv", keep_default_na=False)
syn = pd.read_csv(ROOT / "runs/full/data/synonyms.csv", keep_default_na=False)
SPECIES = set(sp.species); GENERA = set(sp.genus); FAMILIES = set(sp.family)
# synonym -> accepted (ambiguous synonyms, i.e. pointing to >1 accepted species, are not used)
smap = syn.groupby("synonym")["accepted"].agg(lambda s: sorted(set(s)))
SYN = {k: v[0] for k, v in smap.items() if len(v) == 1 and k not in SPECIES}
ALL_GENERA = set(pd.read_csv(ROOT / "data/raw/wcvp/wcvp_names.csv", sep="|", dtype=str, usecols=["genus"], keep_default_na=False)["genus"])
RANKQ = {"Q7432": "species", "Q34740": "genus", "Q35409": "family"}
BOT = re.compile(r"(aceae|eae|oideae|ineae|ales|opsida|phyta|idae)$")  # parent ranks; plants end in -aceae/-eae/-oideae ...
rows = []  # (rank, latin, name, source, family_of_source, id/url, license, via)

def resolve(name, rank):
    return resolve_name(name, rank, SPECIES, SYN, GENERA, FAMILIES)

# ---------------- Wikidata
items = defaultdict(dict)  # (name, rank, item) -> fields
for f in (CACHE / "wikidata").glob("*.json"):
    d = json.loads(f.read_text())
    for b in d["results"]["bindings"]:
        v = {k: x["value"] for k, x in b.items()}
        if "item" not in v: continue
        q = v["item"].rsplit("/", 1)[-1]
        rank = RANKQ.get(v.get("rank", "").rsplit("/", 1)[-1])
        e = items[(v["name"], q)]
        if rank: e["rank"] = rank
        for k in ("cn", "lab", "al", "wt"):
            if k in v: e.setdefault(k, set()).add(v[k])
        for k in ("inat", "gb", "par"):
            if k in v: e.setdefault(k, set()).add(v[k])
bynr = defaultdict(list)
for (name, q), e in items.items():
    if "rank" in e: bynr[(name, e["rank"])].append((q, e))
inat_to_taxa = defaultdict(set)
for (name, rank), lst in bynr.items():
    latin, via = resolve(name, rank)
    if not latin: continue
    if len(lst) > 1:  # homonyms (e.g. an animal genus with the same name): keep only items with a botanical parent
        lst = [(q, e) for q, e in lst if any(BOT.search(p) and not p.endswith("idae") or p in GENERA or p in FAMILIES for p in e.get("par", []))]
    for q, e in lst:
        url = f"https://www.wikidata.org/wiki/{q}"
        for n in e.get("cn", []): rows.append((rank, latin, n, "Wikidata (P1843 taxon common name, tr)", "wikidata", url, "CC0 1.0", via))
        for n in e.get("lab", []): rows.append((rank, latin, n, "Wikidata (Turkish label)", "wikidata", url, "CC0 1.0", via))
        for n in e.get("al", []): rows.append((rank, latin, n, "Wikidata (Turkish alias)", "wikidata", url, "CC0 1.0", via))
        for t in e.get("wt", []):
            if not bad_title(t):
                rows.append((rank, latin, t, "tr.wikipedia (article title via Wikidata sitelink)", "trwiki",
                             "https://tr.wikipedia.org/wiki/" + t.replace(" ", "_"), "CC BY-SA 4.0 (Wikipedia)", via))
        for i in e.get("inat", []): inat_to_taxa[int(i)].add((rank, latin, via))

# ---------------- GBIF (Turkish = language "tur")
def gbif_license(src):
    if "Catalogue of Life" in src: return "CC BY 4.0 (Catalogue of Life, via GBIF)"
    if "IUCN" in src: return "IUCN Red List terms of use, non-commercial (via GBIF)"
    return "licence of the original dataset, see GBIF record (via GBIF)"
def cpath(sub, key): return CACHE / sub / (hashlib.md5(key.encode()).hexdigest() + ".json")
for rank, names in (("species", SPECIES), ("genus", GENERA), ("family", FAMILIES)):
    for name in names:
        fm = cpath("gbif_match", f"{rank}:{name}")
        if not fm.exists(): continue
        m = json.loads(fm.read_text()); key = m.get("acceptedUsageKey") or m.get("usageKey")
        if not key or (m.get("rank") or "").lower() != rank: continue
        fv = cpath("gbif_vern", str(key))
        if not fv.exists(): continue
        via = "synonym" if m.get("acceptedUsageKey") and m.get("acceptedUsageKey") != m.get("usageKey") else "accepted"
        for r in json.loads(fv.read_text()).get("results", []):
            if r.get("language") == "tur" and r.get("vernacularName"):
                src = r.get("source") or "GBIF"
                short = "Catalogue of Life" if "Catalogue of Life" in src else ("IUCN Red List" if "IUCN" in src else src[:60])
                rows.append((rank, name, r["vernacularName"], f"GBIF vernacular name ({short})", "gbif:" + short,
                             f"https://www.gbif.org/species/{key}", gbif_license(src), via))

# ---------------- iNaturalist (names flagged locale "tr")
for f in (CACHE / "inat").glob("*.json"):
    for t in json.loads(f.read_text()).get("results", []):
        for n in t.get("names", []):
            if n.get("locale") == "tr" and n.get("name"):
                for rank, latin, via in inat_to_taxa.get(t["id"], ()):
                    rows.append((rank, latin, n["name"], "iNaturalist (taxon name, locale tr)", "inaturalist",
                                 f"https://www.inaturalist.org/taxa/{t['id']}", "CC BY-NC (iNaturalist user-contributed content, per iNaturalist Terms)", via))

# ---------------- cleaning
df = pd.DataFrame(rows, columns=["rank", "latin_name", "turkish_name", "source", "src_family", "source_id_or_url", "license", "matched_via"])
info = df.src_family.map(source_info)
df["source_tier"] = info.map(lambda t: t[1]); df["license_class"] = info.map(lambda t: t[2]); df["license"] = info.map(lambda t: t[3])
df["turkish_name"] = df["turkish_name"].map(clean)
n_raw = len(df)
df = df[df.turkish_name != ""]
# tier C sources are excluded from the site and the exports, kept in a separate file with the reason
exc = df[df.source_tier == "C"].copy()
exc["reason"] = exc.src_family.map(lambda f: source_info(f)[5])
PRIV = ROOT / "data/names/private"; PRIV.mkdir(parents=True, exist_ok=True)  # git-ignored: never published
exc[["rank", "latin_name", "turkish_name", "source", "source_id_or_url", "matched_via", "reason"]].sort_values(["rank", "latin_name"]) \
    .to_csv(PRIV / "excluded_names_tierC.csv", index=False)
exc.assign(source=exc.src_family.str.replace("gbif:", "GBIF · ")).groupby(["source", "reason"]).size().reset_index(name="rows") \
    .to_csv(ROOT / "data/names/excluded_sources_summary.csv", index=False)  # public: counts only, no names
df = df[df.source_tier != "C"]
df = df[~df.apply(lambda r: is_latin_like(r.turkish_name, r.latin_name, ALL_GENERA), axis=1)]
n_after_latin = len(df)

# coverage with / without non-commercial names
en_set = set(sp.loc[sp.endemic.astype(int) == 1, "species"])
cov_rows = []
for label, d in (("all licences (tier A+B)", df), ("open licences only", df[df.license_class == "open"])):
    sps = set(d[d["rank"] == "species"].latin_name)
    cov_rows.append({"scenario": label, "species": len(sps), "species_pct": round(100 * len(sps) / len(SPECIES), 1),
                     "genera": d[d["rank"] == "genus"].latin_name.nunique(), "genera_pct": round(100 * d[d["rank"] == "genus"].latin_name.nunique() / len(GENERA), 1),
                     "families": d[d["rank"] == "family"].latin_name.nunique(),
                     "endemic_species": len(sps & en_set), "endemic_pct": round(100 * len(sps & en_set) / len(en_set), 1)})
pd.DataFrame(cov_rows).to_csv(ROOT / "data/names/coverage_by_license.csv", index=False)
NONCOM = include_non_commercial()
if not NONCOM:
    # non-commercial names (tier B) are kept only in the git-ignored private folder for local expert checking
    df[df.license_class != "open"][["rank", "latin_name", "turkish_name", "source", "source_id_or_url", "license", "license_class", "source_tier", "matched_via"]] \
        .sort_values(["rank", "latin_name", "turkish_name"]).to_csv(PRIV / "noncommercial_names.csv", index=False)
    df = df[df.license_class == "open"]
print("include_non_commercial:", NONCOM)
for r in cov_rows: print("coverage", r)

# per taxon: merge case / diacritic variants to one spelling; keep one row per (spelling, source)
out = []
for (rank, latin), g in df.groupby(["rank", "latin_name"], sort=False):
    spell = {}
    for ak, grp in g.groupby(g.turkish_name.map(ascii_key)):
        spell[ak] = merge_variants(list(grp.turkish_name))[0]
    g = g.assign(turkish_name=g.turkish_name.map(lambda n: spell[ascii_key(n)]))
    out.append(g.drop_duplicates(["turkish_name", "src_family", "source_id_or_url"]))
df = pd.concat(out, ignore_index=True)
# ambiguity: same Turkish name (case/diacritic-insensitive) used for >1 accepted taxon of the same rank
amb = df.groupby(["rank", df.turkish_name.map(ascii_key)])["latin_name"].nunique()
df["ambiguous"] = [bool(amb[(r, ascii_key(n))] > 1) for r, n in zip(df["rank"], df["turkish_name"])]
df = df.sort_values(["rank", "latin_name", "turkish_name", "source"]).reset_index(drop=True)
Path(ROOT / "data/names").mkdir(parents=True, exist_ok=True)
df[["rank", "latin_name", "turkish_name", "source", "source_id_or_url", "license", "license_class", "source_tier", "matched_via", "ambiguous"]] \
    .to_csv(ROOT / "data/names/turkish_names.csv", index=False)

# ---------------- exports
taxa = pd.read_csv(ROOT / "exports/turkiye_taxa.csv", keep_default_na=False)
def per_taxon(rank):
    g = df[df["rank"] == rank]; res = {}
    for latin, h in g.groupby("latin_name"):
        cnt = h.groupby(h.turkish_name.map(ascii_key)).agg(name=("turkish_name", "first"), n=("src_family", "nunique"), amb=("ambiguous", "max"),
                                                          open_=("license_class", lambda x: (x == "open").any()))
        cnt = cnt.sort_values(["n", "name"], ascending=[False, True])
        res[latin] = ("; ".join(cnt.name), int(cnt.n.max()), "; ".join(cnt.name[cnt.amb]),
                      "open" if cnt.open_.all() else "non-commercial", "A" if (h.source_tier == "A").any() else "B")
    return res
S, G, F = per_taxon("species"), per_taxon("genus"), per_taxon("family")
taxa["turkish_names"] = taxa.species.map(lambda s: S.get(s, ("", 0, "", "", ""))[0])
taxa["n_sources_agreeing"] = taxa.species.map(lambda s: S.get(s, ("", 0, "", "", ""))[1])
taxa["ambiguous_turkish_names"] = taxa.species.map(lambda s: S.get(s, ("", 0, "", "", ""))[2])
taxa["license_class"] = taxa.species.map(lambda s: S.get(s, ("", 0, "", "", ""))[3])
taxa["best_source_tier"] = taxa.species.map(lambda s: S.get(s, ("", 0, "", "", ""))[4])
taxa["turkish_name_verified_by_biologist"] = ""
taxa.to_csv(ROOT / "exports/turkiye_taxa_with_turkish_names.csv", index=False)
taxa[taxa.turkish_names == ""][["species", "family", "genus", "endemic_to_turkiye"]].assign(turkish_name_to_fill="", source_of_name="", biologist_name="") \
    .to_csv(ROOT / "exports/species_without_turkish_name.csv", index=False)
for fn, key, M in (("families", "family", F), ("genera", "genus", G)):
    t = pd.read_csv(ROOT / f"exports/{fn}.csv", keep_default_na=False)
    t["turkish_names"] = t[key].map(lambda s: M.get(s, ("", 0, "", "", ""))[0]); t["n_sources_agreeing"] = t[key].map(lambda s: M.get(s, ("", 0, "", "", ""))[1]); t["license_class"] = t[key].map(lambda s: M.get(s, ("", 0, "", "", ""))[3])
    t.to_csv(ROOT / f"exports/{fn}_with_turkish_names.csv", index=False)

# ---------------- summary
has = taxa.turkish_names != ""
print(f"rows raw {n_raw}, after dropping Latin-equal {n_after_latin}, final {len(df)}")
print("by source:", df.groupby("src_family").size().to_dict())
for rank, tot, M in (("species", len(taxa), S), ("genus", taxa.genus.nunique(), G), ("family", taxa.family.nunique(), F)):
    print(f"{rank}: {len(M)} of {tot} have a Turkish name ({100*len(M)/tot:.1f}%)")
en = taxa.endemic_to_turkiye == 1
print(f"endemic species with a name: {int((has & en).sum())} of {int(en.sum())} ({100*(has & en).sum()/en.sum():.1f}%)")
print("ambiguous names (distinct, species):", df[(df['rank'] == 'species') & df.ambiguous].turkish_name.map(ascii_key).nunique(),
      "| genus:", df[(df['rank'] == 'genus') & df.ambiguous].turkish_name.map(ascii_key).nunique(), "| family:", df[(df['rank'] == 'family') & df.ambiguous].turkish_name.map(ascii_key).nunique())
top = taxa.assign(n=taxa.turkish_names.map(lambda s: len(s.split("; ")) if s else 0)).sort_values("n", ascending=False).head(10)
print("top10 by number of names:", "; ".join(f"{r.species} ({r.n})" for r in top.itertuples()))

# ---------------- biologist check sample (150 pairs; strata do not overlap)
import random
pairs = df[df["rank"] == "species"].assign(key=lambda d: d.latin_name + "|" + d.turkish_name.map(ascii_key))
pairs = pairs.groupby("key").agg(species=("latin_name", "first"), turkish_name=("turkish_name", "first"),
                                 sources=("source", lambda x: "; ".join(sorted(set(x)))), fams=("src_family", lambda x: set(x)),
                                 tier=("source_tier", "min"), license_class=("license_class", lambda x: "open" if (x == "open").any() else "non-commercial"),
                                 ambiguous=("ambiguous", "max")).reset_index(drop=True)
fam_of = dict(zip(sp.species, sp.family)); end_of = dict(zip(sp.species, sp.endemic))
strata = [("Vikipedi", lambda f: "trwiki" in f), ("Wikidata", lambda f: "wikidata" in f),
          ("GBIF/Catalogue of Life/Cichorieae", lambda f: any(x.startswith("gbif:") for x in f))]
used, picked = set(), []
for name, test in strata:
    pool = [i for i, r in pairs.iterrows() if test(r.fams) and i not in used]
    pick = random.Random(42).sample(pool, min(50, len(pool))); used |= set(pick)
    for i in pick:
        r = pairs.loc[i]; picked.append({"stratum": name, "species": r.species, "family": fam_of[r.species], "endemic_to_turkiye": end_of[r.species],
                                         "turkish_name": r.turkish_name, "sources": r.sources, "source_tier": r.tier, "license_class": r.license_class,
                                         "ambiguous": bool(r.ambiguous), "correct (yes/no)": "", "comment": ""})
pd.DataFrame(picked).to_csv(ROOT / "exports/turkish_names_check_sample.csv", index=False)

# ---------------- LICENSES.md
lines = ["# Turkish common names: sources and licences", "",
         "Generated by `scripts/names_build.py`. Names are never typed by hand; each row of `turkish_names.csv` links to its source record.",
         "Tier A = curated reliable source; tier B (iNaturalist, IUCN) = non-commercial, **not published** (kept only in a private local folder); tier C = excluded (counts in `excluded_sources_summary.csv`).",
         "`license_class`: **open** = free reuse with attribution (CC0 / CC BY / CC BY-SA). The `turkish_names` table as a whole is released under **CC BY-SA 4.0** because it includes Vikipedi (CC BY-SA) titles; individual rows keep their source licence in the `license` column.", "",
         "| Source | Tier | Licence class | Licence | Link | Name rows |", "|---|---|---|---|---|---|"]
for fam_key, g in df.groupby("src_family"):
    lab, tier, cls, lic, url, _ = source_info(fam_key)
    lines.append(f"| {lab} | {tier} | {cls} | {lic} | {url} | {len(g)} |")
lines += ["", "## Excluded (tier C)", "", "| Source | Rows | Reason |", "|---|---|---|"]
for fam_key, g in exc.groupby("src_family"):
    lines.append(f"| {fam_key.replace('gbif:', 'GBIF · ')} | {len(g)} | {source_info(fam_key)[5]} |")
lines += ["", "## Other data sources of the project", "",
          "- WCVP (Kew): species list, synonyms and distribution; see https://powo.science.kew.org/ ; WCVP is licensed CC BY 3.0 (README_WCVP.xlsx shipped with the download, 2026-06-04).",
          "- ENA (EMBL-EBI, INSDC): DNA sequences; INSDC policy: free and unrestricted access, no licence restrictions; credit by citing the original submission (accession numbers).",
          "- Bizim Bitkiler / Türkiye Bitkileri Listesi (NGBB): **not used** - no data licence stated; ask the garden for permission before using its Turkish names.",
          "", "## Coverage by licence class", "", "\n".join(["| " + " | ".join(cov_rows[0]) + " |", "|" + "---|" * len(cov_rows[0])] + ["| " + " | ".join(str(v) for v in r.values()) + " |" for r in cov_rows])]
(ROOT / "data/names/LICENSES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("tiers:", df.groupby("source_tier").size().to_dict(), "| excluded rows:", len(exc))
