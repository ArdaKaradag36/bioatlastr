"""Write analysis results as website JSON (web/public/data) and CSV (results/)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from . import __version__
from .analysis import aligner_label, pool_bcm, slugify
from .paths import DATA, DROPPED_CSV, RESULTS, SPECIES_META_JSON, WEB_DATA


def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


def _nan_to_none(value: Any) -> Any:
    return None if (isinstance(value, float) and value != value) else value


def export_all(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    markers: list[str] = res["markers"]
    species_df: pd.DataFrame = res["species"]
    table: pd.DataFrame = res["table"]
    sm = res["sm"]
    fm = res["family_marker"]

    # start from a clean folder so removed species never linger on the website
    if WEB_DATA.exists():
        shutil.rmtree(WEB_DATA)
    WEB_DATA.mkdir(parents=True)
    if (RESULTS / "trees").exists():
        shutil.rmtree(RESULTS / "trees")

    # ---------------------------------------------------------------- species
    index = []
    shards: dict[str, dict[str, Any]] = {}
    any_counts0 = {name: sum(len(sm.get((name, m), {}).get("sequences", [])) for m in markers)
                   for name in species_df["species"]}
    by_genus: dict[str, list[str]] = {}
    by_family: dict[str, list[str]] = {}
    for _, r0 in species_df.iterrows():
        by_genus.setdefault(r0["genus"], []).append(r0["species"])
        by_family.setdefault(r0["family"], []).append(r0["species"])

    def related_with_data(name: str, genus: str, family: str) -> dict[str, Any]:
        """Species without sequences: show congeners (else family members) that do have data."""
        for level, pool in (("genus", by_genus[genus]), ("family", by_family[family])):
            cands = sorted((s for s in pool if s != name and any_counts0[s] > 0), key=lambda s: -any_counts0[s])[:5]
            if cands:
                return {"level": level, "species": [
                    {"name": c, "slug": slugify(c), "n_sequences": any_counts0[c],
                     "markers": [m for m in markers if sm.get((c, m))]} for c in cands]}
        return {"level": None, "species": []}

    for _, row in species_df.sort_values(["family", "species"]).iterrows():
        name = row["species"]
        slug = slugify(name)
        counts = {m: len(sm.get((name, m), {}).get("sequences", [])) for m in markers}
        index.append({
            "slug": slug, "name": name, "genus": row["genus"], "family": row["family"],
            "tr": row["common_name_tr"] or "", "en": row["common_name_en"] or "",
            "endemic": int(row["endemic"]), "counts": counts,
        })
        detail = {
            "slug": slug, "name": name, "genus": row["genus"], "family": row["family"],
            "authorship": row["authorship"], "endemic": int(row["endemic"]),
            "wcvp_id": str(row.get("wcvp_id", "")), "powo_id": str(row.get("powo_id", "")),
            "common_name_tr": row["common_name_tr"] or "", "common_name_en": row["common_name_en"] or "",
            "markers": {},
            "related_with_data": related_with_data(name, row["genus"], row["family"]) if any_counts0[name] == 0 else None,
        }
        for m in markers:
            e = sm.get((name, m))
            if not e:
                detail["markers"][m] = {"n_sequences": 0, "sequences": [], "nearest": [],
                                        "indistinguishable": [], "tree": None, "discrimination": "none"}
                continue
            detail["markers"][m] = {
                "n_sequences": len(e["sequences"]),
                "sequences": e["sequences"],
                "nearest": [{**n, "slug": slugify(n["species"])} for n in e.get("nearest", [])],
                "indistinguishable": [{"species": s, "slug": slugify(s)} for s in e.get("indistinguishable", [])],
                "tree": e.get("tree"),
                "discrimination": e.get("discrimination", "single_sequence"),
            }
        shards.setdefault(slugify(row["genus"]), {})[slug] = detail
    # one file per genus (a few thousand files instead of ten thousand: friendlier for Vercel limits)
    for shard, items in shards.items():
        _dump(WEB_DATA / "species" / f"{shard}.json", items)
    _dump(WEB_DATA / "species_index.json", index)

    # ------------------------------------------------------------------ trees
    for (group, marker), t in res["trees"].items():
        _dump(WEB_DATA / "trees" / f"{t['file']}.json", t)
        nwk = RESULTS / "trees" / f"{t['file']}.nwk"
        nwk.parent.mkdir(parents=True, exist_ok=True)
        nwk.write_text(t["newick"] + "\n", encoding="utf-8")

    # --------------------------------------------------- reference sequences
    ref_n = int(cfg["analysis"].get("reference_per_species", 2))
    for m in markers:
        refs = []
        for (s, mm), e in sm.items():
            if mm != m:
                continue
            # Turkish sequences first, then longest: at most `ref_n` per species keep the search file small
            best = sorted(e["sequences"], key=lambda x: (-x["is_turkey"], -x["length"], x["accession"]))[:ref_n]
            refs += [[x["accession"], s, x["sequence"]] for x in best]
        refs.sort(key=lambda r: (r[1], r[0]))
        _dump(WEB_DATA / "reference" / f"{m}.json", refs)

    # ------------------------------------------------------------------ stats
    cov_rows = res["coverage"]["rows"]
    cov = {(r["family"], r["marker"]): r for r in cov_rows}
    pairs: pd.DataFrame = res["pairs"]

    marker_stats = {}
    for m in markers:
        bcm = pool_bcm([v["bcm"] for (f, mm), v in fm.items() if mm == m])
        c = cov[("ALL", m)]
        sub_pairs = pairs[pairs["marker"] == m] if len(pairs) else pairs
        marker_stats[m] = {
            "sequences": c["sequences"],
            "species_total": c["species_total"],
            "species_0": c["species_0"], "species_1": c["species_1"], "species_2plus": c["species_2plus"],
            "discrimination": bcm,
            "zero_distance_pairs": int(len(sub_pairs)),
            "zero_distance_pairs_singleton": int(sub_pairs["involves_singleton"].sum()) if len(sub_pairs) else 0,
        }

    any_counts = {name: sum(len(sm.get((name, m), {}).get("sequences", [])) for m in markers)
                  for name in species_df["species"]}
    family_stats = {}
    for family, g in species_df.groupby("family"):
        fam_markers = {}
        for m in markers:
            info = fm[(family, m)]
            c = cov[(family, m)]
            fam_markers[m] = {
                "sequences": c["sequences"], "species_0": c["species_0"], "species_1": c["species_1"],
                "species_2plus": c["species_2plus"], "discrimination": info["bcm"],
                "tree": info["tree"], "trees": info["trees"],
                "tree_leaves": sum(t["leaves"] for t in info["trees"]),
                "split_by_genus": info["split_by_genus"],
                "groups_analysed": info["groups_analysed"], "groups_skipped": info["groups_skipped"],
                "alignment_method": info["method"], "alignment": aligner_label(info["method"]) if info["method"] != "none" else "none",
            }
        family_stats[family] = {
            "species": len(g),
            "species_with_any_sequence": sum(1 for s in g["species"] if any_counts[s] > 0),
            "sequences": sum(any_counts[s] for s in g["species"]),
            "markers": fam_markers,
        }

    filter_summary: list[dict[str, Any]] = []
    fs_csv = DATA / "ena_filter_summary.csv"
    if fs_csv.exists():
        filter_summary = pd.read_csv(fs_csv, keep_default_na=False).to_dict("records")
    unmatched_top: list[dict[str, Any]] = []
    um_csv = DATA / "unmatched_names.csv"
    if um_csv.exists():
        um = pd.read_csv(um_csv, keep_default_na=False)
        unmatched_top = [{"name": r["scientific_name"], "records": int(r["n_records"])} for _, r in um.head(30).iterrows()]
        unmatched_total = int(len(um))
    else:
        unmatched_total = 0

    genera = [
        {k: _nan_to_none(v) for k, v in row.items()}
        for row in res["genera"].sort_values(["species_with_any", "species"], ascending=[True, False]).to_dict("records")
    ]
    n_with_any = sum(1 for v in any_counts.values() if v > 0)
    gaps = res["gaps"]
    sp_tab = gaps["species_table"]
    endemic_all = int(sp_tab["endemic"].astype(int).sum())
    turkey_seqs = int(table["is_turkey"].astype(int).sum()) if "is_turkey" in table else 0
    combos = res["combinations"]
    stats = {
        "totals": {
            "species": len(species_df), "families": int(species_df["family"].nunique()),
            "genera": int(species_df["genus"].nunique()),
            "species_with_any_sequence": n_with_any,
            "species_without_sequences": len(species_df) - n_with_any,
            "sequences": int(len(table)),
            "sequences_from_turkey": turkey_seqs,
            "endemic_species": endemic_all,
            "endemic_with_sequence": endemic_all - int(len(gaps["endemics"])),
            "endemic_without_sequence": int(len(gaps["endemics"])),
            "genera_without_sequence": int(len(gaps["genera"])),
            "families_without_sequence": int(len(gaps["families"])),
            "species_with_3_markers": int((sp_tab["markers_with_data"] == len(markers)).sum()),
        },
        "combinations": combos[combos["scope"] == "ALL"].drop(columns="scope").to_dict("records"),
        "markers": marker_stats,
        "families": family_stats,
        "genera": genera,
        "filter_summary": filter_summary,
        "unmatched_names_total": unmatched_total,
        "unmatched_names_top": unmatched_top,
        "groups_skipped": int(len(res["skipped"])),
        "groups_skipped_timeout_or_error": int(res["skipped"]["reason"].astype(str).str.startswith("skipped:").sum()),
        "groups_subsampled": int(len(res["subsampled"])),
        "groups_analysed": int(len(res["groups"])),
    }
    _dump(WEB_DATA / "stats.json", stats)
    _dump(WEB_DATA / "gaps.json", {
        "families": gaps["families"].to_dict("records"),
        "genera": gaps["genera"].to_dict("records"),
        "species": [{"name": r["species"], "slug": slugify(r["species"]), "genus": r["genus"], "family": r["family"],
                     "endemic": int(r["endemic"])} for r in gaps["species"].to_dict("records")],
        "endemics": [{"name": r["species"], "slug": slugify(r["species"]), "genus": r["genus"], "family": r["family"]}
                     for r in gaps["endemics"].to_dict("records")],
        "coverage": res["coverage"]["rows"],
    })

    fam_list = []
    for family, fs in family_stats.items():
        trees = [
            {"marker": m, "file": t["file"], "group": t["group"], "leaves": t["leaves"], "species": t["species"]}
            for m, v in fs["markers"].items() for t in v["trees"]
        ]
        fam_list.append({"family": family, "species": fs["species"], "trees": trees,
                         "split_by_genus": any(v["split_by_genus"] for v in fs["markers"].values())})
    _dump(WEB_DATA / "families.json", fam_list)

    # ------------------------------------------------------------------- meta
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipeline_version": __version__,
        "country": "TR",
        "species_source": cfg["species_source"], "sequence_source": cfg["sequence_source"],
        "families": cfg["families"],
        "max_species": cfg["max_species"],
        "species_meta": json.loads(SPECIES_META_JSON.read_text(encoding="utf-8")) if SPECIES_META_JSON.exists() else None,
        "sequence_meta": json.loads((DATA / "sequence_source.json").read_text(encoding="utf-8"))
        if (DATA / "sequence_source.json").exists() else None,
        "markers": {
            m: {k: v for k, v in mc.items() if k in ("min_length", "max_length", "max_n_fraction", "ena_terms")}
            for m, mc in cfg["markers"].items()
        },
        "max_identical_copies": cfg["ena"]["max_identical_copies"],
        "max_group_sequences": cfg["analysis"]["max_group_sequences"],
        "min_group_sequences": cfg["analysis"]["min_group_sequences"],
        "max_sequences_per_species_marker": cfg["max_sequences_per_species_marker"],
        "allow_name_mismatch": cfg["allow_name_mismatch"],
        "min_overlap": cfg["analysis"]["min_overlap"],
        "n_nearest": cfg["analysis"]["n_nearest"],
        "aligner": res["aligner"],
        "aligner_label": res["aligner_label"],
    }
    _dump(WEB_DATA / "meta.json", meta)

    export_csv(res, markers, marker_stats)
    n_files = sum(1 for _ in WEB_DATA.rglob("*.json"))
    size_mb = sum(p.stat().st_size for p in WEB_DATA.rglob("*.json")) / 1e6
    print(f"[phase 3] wrote {n_files} JSON files ({size_mb:.1f} MB) to {WEB_DATA}")
    print(f"[phase 3] wrote CSV summaries to {RESULTS}")


def export_csv(res: dict[str, Any], markers: list[str], marker_stats: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cov = pd.DataFrame(res["coverage"]["rows"])
    cov[cov["family"] == "ALL"].drop(columns="family").to_csv(RESULTS / "coverage_by_marker.csv", index=False)
    cov[cov["family"] != "ALL"].to_csv(RESULTS / "coverage_by_family_marker.csv", index=False)

    fm_rows, marker_rows = [], []
    for (family, marker), info in res["family_marker"].items():
        fm_rows.append({"family": family, "marker": marker, "sequences": info["n_sequences"],
                        "species_with_sequences": info["n_species"],
                        "alignment": aligner_label(info["method"]) if info["method"] != "none" else "none",
                        "split_by_genus": info["split_by_genus"], "groups_analysed": info["groups_analysed"],
                        "groups_skipped": info["groups_skipped"], **info["bcm"]})
    pd.DataFrame(fm_rows).to_csv(RESULTS / "discrimination_by_family_marker.csv", index=False)
    for m in markers:
        marker_rows.append({"marker": m, **marker_stats[m]["discrimination"],
                            "zero_distance_pairs": marker_stats[m]["zero_distance_pairs"],
                            "zero_distance_pairs_with_singleton": marker_stats[m]["zero_distance_pairs_singleton"]})
    pd.DataFrame(marker_rows).to_csv(RESULTS / "discrimination_by_marker.csv", index=False)

    res["combinations"].to_csv(RESULTS / "discrimination_combinations.csv", index=False)
    res["groups"].to_csv(RESULTS / "group_summary.csv", index=False)
    res["skipped"].to_csv(RESULTS / "skipped_groups.csv", index=False)
    res["subsampled"].to_csv(RESULTS / "subsampled_groups.csv", index=False)
    g = res["gaps"]
    g["species"].to_csv(RESULTS / "data_gaps_species.csv", index=False)
    g["genera"].to_csv(RESULTS / "data_gaps_genera.csv", index=False)
    g["families"].to_csv(RESULTS / "data_gaps_families.csv", index=False)
    g["endemics"].to_csv(RESULTS / "data_gaps_endemics.csv", index=False)
    fs_csv = DATA / "ena_filter_summary.csv"
    if fs_csv.exists():
        pd.read_csv(fs_csv).to_csv(RESULTS / "filter_summary.csv", index=False)
    res["per_sequence"].to_csv(RESULTS / "discrimination_per_sequence.csv", index=False)
    res["pairs"].to_csv(RESULTS / "indistinguishable_pairs.csv", index=False)
    res["relatives"].to_csv(RESULTS / "nearest_relatives.csv", index=False)
    res["genera"].sort_values(["species_with_any", "species"], ascending=[True, False]).to_csv(
        RESULTS / "genera_data_summary.csv", index=False)

    # one row per species with its sequence counts (handy for the report)
    sm = res["sm"]
    rows = []
    for _, r in res["species"].iterrows():
        row = {"species": r["species"], "genus": r["genus"], "family": r["family"], "endemic": int(r["endemic"])}
        for m in markers:
            row[f"n_{m}"] = len(sm.get((r["species"], m), {}).get("sequences", []))
        rows.append(row)
    pd.DataFrame(rows).to_csv(RESULTS / "species_marker_counts.csv", index=False)
