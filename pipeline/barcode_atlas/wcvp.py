"""Phase 1 (default): Turkish species list from WCVP (World Checklist of Vascular Plants, Kew).

Download wcvp.zip (skipped if present), join names and distribution on plant_name_id, keep
accepted, non-hybrid species that are native and not extinct/doubtful in Turkey (WGSRPD area TUR).
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .paths import RAW, SPECIES_CSV, SPECIES_META_JSON, SYNONYMS_CSV

NAMES_FILE = "wcvp_names.csv"
DIST_FILE = "wcvp_distribution.csv"
SEP = "|"
NAME_COLS = ["plant_name_id", "taxon_rank", "taxon_status", "family", "genus_hybrid", "genus", "species_hybrid",
             "species", "infraspecific_rank", "taxon_name", "taxon_authors", "accepted_plant_name_id", "powo_id"]
DIST_COLS = ["plant_name_id", "area_code_l3", "area", "introduced", "extinct", "location_doubtful"]
SPECIES_COLUMNS = ["species", "genus", "family", "authorship", "endemic", "wcvp_id", "powo_id",
                   "common_name_tr", "common_name_en"]


def download_wcvp(url: str, dest: Path) -> None:
    """Download once. On failure tell the user which file to place by hand."""
    if dest.exists():
        print(f"[phase 1] {dest.name} already present - download skipped")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(".zip.part")
    try:
        with requests.get(url, stream=True, timeout=60, allow_redirects=True) as r:
            r.raise_for_status()
            with open(part, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        part.replace(dest)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"WCVP download failed ({exc}).\nPlease download {url} manually and place the file at:\n  {dest}\n"
            "then run the phase again.") from exc


def extract_wcvp(zip_path: Path) -> Path:
    out = zip_path.parent / "wcvp"
    if not (out / NAMES_FILE).exists() or not (out / DIST_FILE).exists():
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(out)
    return out


def build_species_table(names: pd.DataFrame, dist: pd.DataFrame, area_code: str = "TUR"):
    """Pure function: WCVP names + distribution -> (species table, synonym table, stats dict)."""
    d = dist.copy()
    for c in ("introduced", "extinct", "location_doubtful"):
        d[c] = d[c].fillna("0").astype(str)
    tur = d[d["area_code_l3"] == area_code]
    native_tur = tur[(tur["introduced"] == "0") & (tur["extinct"] == "0") & (tur["location_doubtful"] == "0")]
    stats: dict[str, Any] = {"rows_in_area": int(tur["plant_name_id"].nunique())}

    sp = names[(names["taxon_rank"] == "Species") & (names["taxon_status"] == "Accepted")]
    stats["accepted_species_total"] = int(len(sp))
    sp = sp.merge(native_tur[["plant_name_id"]].drop_duplicates(), on="plant_name_id")
    stats["native_in_area"] = int(len(sp))
    hybrid = sp["genus_hybrid"].fillna("").ne("") | sp["species_hybrid"].fillna("").ne("")
    stats["hybrids_excluded"] = int(hybrid.sum())
    sp = sp[~hybrid].copy()
    sp = sp[sp["genus"].fillna("").ne("") & sp["species"].fillna("").ne("")]

    # endemic = native areas of the species consist of the target area only
    native_all = d[(d["introduced"] == "0") & (d["extinct"] == "0") & (d["location_doubtful"] == "0")]
    n_areas = native_all.groupby("plant_name_id")["area_code_l3"].nunique()
    sp["endemic"] = sp["plant_name_id"].map(n_areas).fillna(0).astype(int).eq(1).astype(int)

    sp["species_name"] = sp["genus"] + " " + sp["species"]
    sp = sp.drop_duplicates("species_name")
    out = pd.DataFrame({
        "species": sp["species_name"], "genus": sp["genus"], "family": sp["family"],
        "authorship": sp["taxon_authors"].fillna(""), "endemic": sp["endemic"],
        "wcvp_id": sp["plant_name_id"], "powo_id": sp["powo_id"].fillna(""),
        "common_name_tr": "", "common_name_en": "",
    }).sort_values(["family", "species"]).reset_index(drop=True)
    stats["species_kept"] = int(len(out))
    stats["endemic"] = int(out["endemic"].sum())

    # synonyms (species rank) of the kept accepted species
    ids = dict(zip(sp["plant_name_id"], sp["species_name"]))
    syn = names[(names["taxon_rank"] == "Species") & names["taxon_status"].isin(["Synonym", "Orthographic", "Illegitimate", "Invalid"])
                & names["accepted_plant_name_id"].isin(ids.keys())]
    syn = syn[syn["genus"].fillna("").ne("") & syn["species"].fillna("").ne("")
              & syn["genus_hybrid"].fillna("").eq("") & syn["species_hybrid"].fillna("").eq("")]
    syn_df = pd.DataFrame({"synonym": syn["genus"] + " " + syn["species"],
                           "accepted": syn["accepted_plant_name_id"].map(ids)}).drop_duplicates()
    stats["synonyms"] = int(len(syn_df))
    return out, syn_df, stats


def run_phase1_wcvp(cfg: dict[str, Any]) -> pd.DataFrame:
    w = cfg["wcvp"]
    zip_path = RAW / "wcvp.zip"
    download_wcvp(w["url"], zip_path)
    folder = extract_wcvp(zip_path)
    names = pd.read_csv(folder / NAMES_FILE, sep=SEP, dtype=str, usecols=NAME_COLS, keep_default_na=False)
    dist = pd.read_csv(folder / DIST_FILE, sep=SEP, dtype=str, usecols=DIST_COLS, keep_default_na=False)
    code = w["area_code"]
    area_names = sorted(set(dist.loc[dist["area_code_l3"] == code, "area"]))
    print(f"[phase 1] area_code_l3 {code} = {area_names} (WGSRPD level-3 code of Turkey/Türkiye)")
    if not any(n.lower().startswith(("türkiye", "turkey")) for n in area_names):
        raise SystemExit(f"area_code_l3 '{code}' is not Turkey in this WCVP release: {area_names}")

    table, syn, stats = build_species_table(names, dist, code)
    stats["families_total"] = int(table["family"].nunique())
    fam = cfg.get("families_whitelist") or []
    if fam:
        table = table[table["family"].isin(fam)]
        missing = sorted(set(fam) - set(table["family"]))
        if missing:
            print(f"[phase 1] WARNING: families not found in WCVP/Turkey: {missing}")
    if cfg.get("max_species"):
        table = table.head(int(cfg["max_species"]))
    table = table.reset_index(drop=True)
    syn = syn[syn["accepted"].isin(set(table["species"]))]

    SPECIES_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(SPECIES_CSV, index=False, columns=SPECIES_COLUMNS)
    syn.to_csv(SYNONYMS_CSV, index=False)
    sha = hashlib.sha256()
    with open(zip_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    with zipfile.ZipFile(zip_path) as z:
        dates = {i.filename: "%04d-%02d-%02d" % i.date_time[:3] for i in z.infolist()}
    meta = {
        "source": "WCVP - World Checklist of Vascular Plants (Royal Botanic Gardens, Kew)",
        "url": w["url"], "area_code_l3": code, "area_name": area_names[0],
        "wcvp_file_date": dates.get(NAMES_FILE), "downloaded": date.fromtimestamp(zip_path.stat().st_mtime).isoformat(),
        "sha256": sha.hexdigest(), "families_whitelist": fam, "max_species": cfg.get("max_species"),
        "rules": "taxon_rank=Species, taxon_status=Accepted, area_code_l3=TUR, introduced=0, extinct=0, "
                 "location_doubtful=0, hybrids excluded; endemic = native in exactly one WGSRPD area (TUR)",
        "stats": stats, "species_in_file": int(len(table)), "endemic_in_file": int(table["endemic"].sum()),
        "synonyms_in_file": int(len(syn)),
    }
    with open(SPECIES_META_JSON, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print(f"[phase 1] {len(table)} species, {table['family'].nunique()} families, {int(table['endemic'].sum())} endemic, "
          f"{len(syn)} synonyms; stats {stats}")
    return table
