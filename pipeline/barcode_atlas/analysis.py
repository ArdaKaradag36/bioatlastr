"""Phase 3: alignment, trees, coverage and discrimination statistics.

The result of `analyse()` is a plain dict that `export.py` turns into
website JSON files and CSV summaries.
"""

from __future__ import annotations

import itertools
import time
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from Bio import SeqIO

from .align import AlignTimeout, align_sequences, find_mafft
from .discrimination import (
    best_close_match,
    combined_species_distance,
    species_level_status,
    group_by_species,
    nearest_relatives,
    species_distance_matrix,
    species_status_from,
    summarize_bcm,
    zero_distance_pairs,
)
from .distance import build_tree, encode_alignment, p_distance_matrix, tree_to_newick
from .paths import ALIGNMENTS_DIR, DATA, SEQUENCE_TABLE_CSV, SEQUENCES_DIR, SPECIES_CSV


def slugify(name: str) -> str:
    """'Quercus robur' -> 'quercus-robur' (used in URLs and file names)."""
    return re.sub(r"[^a-z-]", "", name.lower().replace(" ", "-"))


def leaf_label(species: str, accession: str) -> str:
    """Name of a tree leaf: 'Quercus_robur__KX123456.1'."""
    return f"{species.replace(' ', '_')}__{accession}"


def load_inputs(cfg: dict[str, Any]):
    """Read species.csv, sequence_table.csv and the FASTA files."""
    species = pd.read_csv(SPECIES_CSV, keep_default_na=False)
    if not SEQUENCE_TABLE_CSV.exists():
        raise SystemExit("data/sequence_table.csv not found - run phase 2 first.")
    table = pd.read_csv(SEQUENCE_TABLE_CSV, keep_default_na=False)
    seqs: dict[tuple[str, str], str] = {}
    for marker in cfg["markers"]:
        fasta = SEQUENCES_DIR / f"{marker}.fasta"
        if not fasta.exists():
            continue
        for rec in SeqIO.parse(str(fasta), "fasta"):
            seqs[(marker, rec.id)] = str(rec.seq)
    return species, table, seqs


def pool_bcm(summaries: list[dict]) -> dict:
    """Add up several summarize_bcm() dicts and recompute the rates."""
    keys = ["sequences_evaluated", "sequences_excluded", "success", "ambiguous", "fail",
            "species_evaluated", "species_success"]
    total = {k: sum(s[k] for s in summaries) for k in keys}
    n, ns = total["sequences_evaluated"], total["species_evaluated"]
    total["success_rate"] = total["success"] / n if n else None
    total["species_success_rate"] = total["species_success"] / ns if ns else None
    return total


def aligner_label(method: str) -> str:
    """Label written on every output: which aligner produced the alignment."""
    return "MAFFT" if method == "mafft" else "fallback (preliminary)"


def make_groups(table: pd.DataFrame, family: str, split: bool) -> list[tuple[str, str | None, pd.DataFrame]]:
    """(group key, genus or None, rows). Large families are analysed genus by genus."""
    if not split:
        return [(family, None, table)]
    return [(f"{family}/{genus}", genus, g) for genus, g in table.groupby("genus")]


def file_key(group_key: str, marker: str) -> str:
    return f"{group_key.replace('/', '.')}.{marker}"


def subsample_group(sub: pd.DataFrame, cap: int) -> pd.DataFrame:
    """Keep at most `cap` rows: first Turkish record of each species, then one record of every other species,
    then the remaining Turkish records, then the rest (deterministic)."""
    sub = sub.sort_values(["species", "accession"]).copy()
    sub["_t"] = sub["is_turkey"].fillna(0).astype(int) if "is_turkey" in sub else 0
    rank = sub.groupby(["species", "_t"]).cumcount()
    has_turkey = sub.groupby("species")["_t"].transform("max") == 1
    sub["_tier"] = 3
    sub.loc[(sub["_t"] == 1) & (rank > 0), "_tier"] = 2
    sub.loc[~has_turkey & (rank == 0), "_tier"] = 1
    sub.loc[(sub["_t"] == 1) & (rank == 0), "_tier"] = 0
    keep = sub.sort_values(["_tier", "species", "accession"]).head(cap)
    return keep.drop(columns=["_t", "_tier"]).sort_values(["species", "accession"])


def _read_alignment(fkey: str, accs: list[str]) -> tuple[dict[str, str], str] | None:
    """Checkpoint: reuse an alignment from an interrupted run when it contains exactly these sequences."""
    f, meta = ALIGNMENTS_DIR / f"{fkey}.aln.fasta", ALIGNMENTS_DIR / f"{fkey}.aln.method"
    if not (f.exists() and meta.exists()):
        return None
    aligned: dict[str, str] = {}
    for line in f.read_text().splitlines():
        if line.startswith(">"):
            cur = line[1:].split()[0]
            aligned[cur] = ""
        elif aligned:
            aligned[cur] += line.strip()
    if set(aligned) != set(accs) or not all(aligned.values()):
        return None
    return aligned, meta.read_text().strip()


def compute_group(job: dict[str, Any]) -> dict[str, Any]:
    """Wrapper: a failing / too slow group is returned as {"failed": reason} and never stops the run."""
    try:
        return _compute_group(job)
    except AlignTimeout as exc:
        return {"job": job, "failed": "skipped: too large/timeout", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001 - one bad group must not block the other groups
        return {"job": job, "failed": "skipped: error", "detail": f"{type(exc).__name__}: {exc}"[:200]}


def _compute_group(job: dict[str, Any]) -> dict[str, Any]:
    """Align one group (family or genus) for one marker and compute all distances, NJ tree, nearest relatives."""
    marker, key, sub = job["marker"], job["key"], job["sub"]
    accs, sp_of = list(sub["accession"]), list(sub["species"])
    fkey = file_key(key, marker)
    cached = _read_alignment(fkey, accs)
    if cached:
        aligned, method = cached
    else:
        raw = {a: job["seqs"][(marker, a)] for a in accs}
        aligned, method = align_sequences(raw, job["mafft_path"], job["threads"], job.get("timeout"))
        with open(ALIGNMENTS_DIR / f"{fkey}.aln.fasta", "w") as fh:
            for a, s in zip(accs, sp_of):
                fh.write(f">{a} {s}\n{aligned[a]}\n")
        (ALIGNMENTS_DIR / f"{fkey}.aln.method").write_text(method)
    codes = encode_alignment([aligned[a] for a in accs])
    dist = p_distance_matrix(codes, job["min_overlap"])
    bcm = best_close_match(dist, sp_of)
    groups = group_by_species(sp_of)
    sp_dist = species_distance_matrix(dist, groups)
    out: dict[str, Any] = {
        "job": job, "method": method, "accs": accs, "sp_of": sp_of, "fkey": fkey, "bcm": bcm,
        "groups": groups, "sp_dist": sp_dist,
        "relatives": nearest_relatives(sp_dist, groups.names, job["n_near"]),
        "pairs": zero_distance_pairs(sp_dist, groups.names, groups.counts),
        "tree": None,
    }
    if len(accs) >= 3:
        labels = [leaf_label(s, a) for s, a in zip(sp_of, accs)]
        out["labels"] = labels
        out["tree"] = tree_to_newick(build_tree(dist, labels))
    return out


def analyse(cfg: dict[str, Any]) -> dict[str, Any]:
    species_df, table, seqs = load_inputs(cfg)
    if "endemic" not in species_df.columns:
        species_df["endemic"] = 0
    markers: list[str] = list(cfg["markers"])
    a_cfg = cfg["analysis"]
    n_near = a_cfg["n_nearest"]
    min_n, max_n = int(a_cfg["min_group_sequences"]), int(a_cfg["max_group_sequences"])
    ALIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)

    mafft = find_mafft(a_cfg.get("mafft_path"))
    workers = int(a_cfg.get("workers", 4))
    print(f"[phase 3] aligner: {'MAFFT at ' + mafft if mafft else 'Biopython center-star fallback (MAFFT not found)'}", flush=True)

    # one dict per (species, marker) that collects everything we know
    sm: dict[tuple[str, str], dict[str, Any]] = {}
    for r in table.to_dict("records"):
        entry = sm.setdefault((r["species"], r["marker"]), {"sequences": []})
        entry["sequences"].append({
            "accession": r["accession"], "length": int(r["length"]),
            "source_title": r.get("source_title", ""), "definition": r["definition"],
            "country": r["country"], "voucher": r["voucher"],
            "is_turkey": int(r.get("is_turkey") or 0), "matched_via": r.get("matched_via", ""),
            "sequence": seqs.get((r["marker"], r["accession"]), ""),
        })

    family_marker: dict[tuple[str, str], dict[str, Any]] = {}
    jobs: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    subsampled: list[dict[str, Any]] = []
    for family in sorted(species_df["family"].unique()):
        fam_tab = table[table["family"] == family]
        split = any(int((fam_tab["marker"] == m).sum()) > max_n for m in markers)
        for marker in markers:
            sub = fam_tab[fam_tab["marker"] == marker].sort_values(["species", "accession"])
            family_marker[(family, marker)] = {
                "family": family, "marker": marker, "n_sequences": len(sub),
                "n_species": int(sub["species"].nunique()), "method": "none", "tree": None, "trees": [],
                "split_by_genus": split, "groups_analysed": 0, "groups_skipped": 0, "bcm": summarize_bcm([]),
            }
            for key, genus, g in make_groups(sub, family, split):
                if g.empty:
                    continue
                n_sp = int(g["species"].nunique())
                reason = "too_few_sequences" if len(g) < min_n else ("single_species" if n_sp < 2 else None)
                if reason:
                    skipped.append({"group": key, "family": family, "genus": genus or "", "marker": marker,
                                    "sequences": len(g), "species": n_sp, "reason": reason})
                    family_marker[(family, marker)]["groups_skipped"] += 1
                    continue
                n_available = len(g)
                if n_available > max_n:
                    g = subsample_group(g, max_n)
                    subsampled.append({"group": key, "family": family, "genus": genus or "", "marker": marker,
                                       "sequences": n_available, "species": n_sp,
                                       "reason": f"subsampled to {len(g)} (Turkish + one per species first)"})
                jobs.append({"marker": marker, "key": key, "family": family, "genus": genus, "sub": g,
                             "n_available": n_available, "timeout": a_cfg.get("mafft_timeout_s"),
                             "seqs": seqs, "mafft_path": a_cfg.get("mafft_path"),
                             "threads": 1 if workers > 1 else a_cfg["mafft_threads"],
                             "min_overlap": a_cfg["min_overlap"], "n_near": n_near})
    jobs.sort(key=lambda j: -len(j["sub"]))  # biggest first -> better load balance
    print(f"[phase 3] {len(jobs)} groups to analyse, {len(skipped)} skipped (too few sequences / one species), "
          f"{len(subsampled)} subsampled to <= {max_n} sequences; MAFFT timeout {a_cfg.get('mafft_timeout_s')} s", flush=True)

    trees: dict[tuple[str, str], dict[str, Any]] = {}
    tree_files: list[dict[str, Any]] = []
    per_sequence_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    relative_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    species_level: dict[tuple[str, str], tuple[list[str], np.ndarray]] = {}
    bcm_by_fm: dict[tuple[str, str], list[dict]] = defaultdict(list)
    methods: set[str] = set()

    done = 0
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(compute_group, jobs):
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f"  [{time.strftime('%H:%M:%S')}] analysed {done}/{len(jobs)} groups "
                      f"(failed/timeout so far: {len([x for x in skipped if x['reason'].startswith('skipped:')])})", flush=True)
            job = res["job"]
            if res.get("failed"):
                g = job["sub"]
                skipped.append({"group": job["key"], "family": job["family"], "genus": job["genus"] or "",
                                "marker": job["marker"], "sequences": len(g), "species": int(g["species"].nunique()),
                                "reason": res["failed"]})
                family_marker[(job["family"], job["marker"])]["groups_skipped"] += 1
                print(f"  ! {job['key']} {job['marker']} ({len(g)} seq): {res['failed']} - {res.get('detail', '')}", flush=True)
                continue
            family, genus, marker, key = job["family"], job["genus"], job["marker"], job["key"]
            accs, sp_of, groups, method = res["accs"], res["sp_of"], res["groups"], res["method"]
            methods.add(method)
            info = family_marker[(family, marker)]
            info["method"] = method
            info["groups_analysed"] += 1
            bcm = res["bcm"]
            bcm_by_fm[(family, marker)].append(summarize_bcm(bcm))
            species_level[(key, marker)] = (groups.names, res["sp_dist"])
            seq_status: dict[str, list[str]] = defaultdict(list)
            for r in bcm:
                per_sequence_rows.append({
                    "group": key, "family": family, "marker": marker, "species": r["species"],
                    "accession": accs[r["row"]], "status": r["status"], "reason": r["reason"],
                    "nearest_conspecific_distance": r["nearest_conspecific"],
                    "nearest_other_species": r["nearest_other_species"],
                    "nearest_other_distance": r["nearest_other"],
                })
                if r["status"] != "excluded":
                    seq_status[r["species"]].append(r["status"])
            for p in res["pairs"]:
                pair_rows.append({"group": key, "family": family, "marker": marker, **p})
            zero_with: dict[str, list[str]] = defaultdict(list)
            for p in res["pairs"]:
                zero_with[p["species_a"]].append(p["species_b"])
                zero_with[p["species_b"]].append(p["species_a"])
            for k, name in enumerate(groups.names):
                entry = sm[(name, marker)]
                rel = res["relatives"][name]
                entry["nearest"] = [
                    {"species": other, "distance": round(d, 5), "same_genus": other.split()[0] == name.split()[0]}
                    for other, d in rel
                ]
                for rank, (other, d) in enumerate(rel, start=1):
                    relative_rows.append({"group": key, "family": family, "marker": marker, "species": name,
                                          "rank": rank, "relative": other, "p_distance": round(d, 5)})
                entry["indistinguishable"] = sorted(zero_with.get(name, []))
                if groups.counts[k] < 2:
                    entry["discrimination"] = "single_sequence"
                elif name in seq_status:
                    entry["discrimination"] = species_status_from(seq_status[name])
                else:
                    entry["discrimination"] = "not_evaluable"
            if res["tree"]:
                t = {"family": family, "genus": genus, "group": key, "marker": marker, "file": res["fkey"],
                     "n_leaves": len(accs), "n_species": len(groups.names), "method": method,
                     "aligner": aligner_label(method), "newick": res["tree"]}
                trees[(key, marker)] = t
                info["trees"].append({"file": res["fkey"], "group": key, "leaves": len(accs),
                                      "species": len(groups.names)})
                for name in groups.names:
                    sm[(name, marker)]["tree"] = {
                        "file": res["fkey"],
                        "leaves": [lab for lab, s in zip(res["labels"], sp_of) if s == name],
                    }
            group_rows.append({"group": key, "family": family, "genus": genus or "", "marker": marker,
                               "sequences": len(accs), "sequences_available": job["n_available"],
                               "species": len(groups.names),
                               "alignment": aligner_label(method), "tree": bool(res["tree"]), **summarize_bcm(bcm)})

    for (family, marker), lst in bcm_by_fm.items():
        info = family_marker[(family, marker)]
        info["bcm"] = pool_bcm(lst)
        if len(info["trees"]) == 1 and not info["split_by_genus"]:
            info["tree"] = info["trees"][0]["file"]

    if len(methods) > 1:
        print("[phase 3] WARNING: mixed aligners used", methods)
    method_all = "mafft" if methods == {"mafft"} else ("center-star" if methods else ("mafft" if mafft else "center-star"))
    combos = combination_table(species_level, species_df, markers)

    return {
        "species": species_df,
        "table": table,
        "sm": sm,
        "family_marker": family_marker,
        "trees": trees,
        "per_sequence": pd.DataFrame(per_sequence_rows),
        "pairs": pd.DataFrame(pair_rows),
        "relatives": pd.DataFrame(relative_rows),
        "groups": pd.DataFrame(group_rows),
        "subsampled": pd.DataFrame(subsampled, columns=["group", "family", "genus", "marker", "sequences", "species", "reason"]),
        "skipped": pd.DataFrame(skipped, columns=["group", "family", "genus", "marker", "sequences", "species", "reason"]),
        "combinations": combos,
        "markers": markers,
        "species_info": {r["species"]: r for r in species_df.to_dict("records")},
        "aligner": "mafft" if method_all == "mafft" else "center-star",
        "aligner_label": aligner_label(method_all),
        "coverage": coverage_tables(species_df, table, markers),
        "genera": genus_table(species_df, table, markers),
        "gaps": data_gaps(species_df, table, markers),
    }


def combination_table(species_level: dict, species_df: pd.DataFrame, markers: list[str]) -> pd.DataFrame:
    """Species-level nearest-neighbour success for each marker and each marker combination."""
    family_of = dict(zip(species_df["species"], species_df["family"]))
    keys = sorted({k for k, _ in species_level})
    combos = [list(c) for n in range(1, len(markers) + 1) for c in itertools.combinations(markers, n)]
    rows: list[dict[str, Any]] = []
    for combo in combos:
        status: dict[str, str] = {}
        for key in keys:
            if not all((key, m) in species_level for m in combo):
                continue  # strict: every marker of the combination must have been analysed for this group
            mats = {m: species_level[(key, m)] for m in combo}
            names, comb = combined_species_distance(mats, combo)
            status.update(species_level_status(names, comb))
        scopes = [("ALL", status)] + [
            (fam, {s: v for s, v in status.items() if family_of.get(s) == fam})
            for fam in sorted(set(family_of.values()))
        ]
        for scope, st in scopes:
            if scope != "ALL" and not st:
                continue
            c = pd.Series(list(st.values())).value_counts().to_dict() if st else {}
            n = len(st)
            rows.append({"scope": scope, "combination": "+".join(combo), "n_markers": len(combo),
                         "species_evaluated": n, "success": c.get("success", 0),
                         "ambiguous": c.get("ambiguous", 0), "fail": c.get("fail", 0),
                         "success_rate": (c.get("success", 0) / n) if n else None})
    return pd.DataFrame(rows, columns=["scope", "combination", "n_markers", "species_evaluated", "success",
                                       "ambiguous", "fail", "success_rate"])


def data_gaps(species_df: pd.DataFrame, table: pd.DataFrame, markers: list[str]) -> dict[str, pd.DataFrame]:
    """Species / genera / families without barcode data and endemics without data (the 'data gap' findings)."""
    counts = table.groupby(["species", "marker"]).size().unstack(fill_value=0).reindex(columns=markers, fill_value=0)
    sp = species_df[["species", "genus", "family", "endemic"]].copy()
    for m in markers:
        sp[f"n_{m}"] = sp["species"].map(counts[m]).fillna(0).astype(int)
    sp["n_any"] = sp[[f"n_{m}" for m in markers]].sum(axis=1)
    sp["markers_with_data"] = (sp[[f"n_{m}" for m in markers]] > 0).sum(axis=1)
    species_gaps = sp[sp["n_any"] == 0].sort_values(["family", "species"])
    gen = sp.groupby(["family", "genus"]).agg(
        species=("species", "size"), endemic_species=("endemic", "sum"),
        species_with_data=("n_any", lambda x: int((x > 0).sum()))).reset_index()
    genus_gaps = gen[gen["species_with_data"] == 0].sort_values(["family", "genus"])
    fam = sp.groupby("family").agg(species=("species", "size"), species_with_data=("n_any", lambda x: int((x > 0).sum()))).reset_index()
    family_gaps = fam[fam["species_with_data"] == 0]
    endemics = sp[(sp["endemic"].astype(int) == 1) & (sp["n_any"] == 0)].sort_values(["family", "species"])
    return {"species": species_gaps, "genera": genus_gaps, "families": family_gaps, "endemics": endemics,
            "species_table": sp}


def coverage_tables(species_df: pd.DataFrame, table: pd.DataFrame, markers: list[str]) -> dict[str, Any]:
    """(a) How many target species have 0, 1 or 2+ sequences, per marker and per family."""
    counts = table.groupby(["species", "marker"]).size().to_dict()
    rows = []
    for family, group in [("ALL", species_df)] + list(species_df.groupby("family")):
        for marker in markers:
            n = [counts.get((s, marker), 0) for s in group["species"]]
            rows.append({
                "family": family, "marker": marker, "species_total": len(n),
                "species_0": sum(1 for x in n if x == 0),
                "species_1": sum(1 for x in n if x == 1),
                "species_2plus": sum(1 for x in n if x >= 2),
                "sequences": int(sum(n)),
            })
    return {"rows": rows}


def genus_table(species_df: pd.DataFrame, table: pd.DataFrame, markers: list[str]) -> pd.DataFrame:
    """Per genus: how much barcode data exists (for the 'data gaps' page)."""
    counts = table.groupby(["species", "marker"]).size().to_dict()
    rows = []
    for (family, genus), g in species_df.groupby(["family", "genus"]):
        row: dict[str, Any] = {"genus": genus, "family": family, "species": len(g),
                               "endemic_species": int(g["endemic"].astype(int).sum()) if "endemic" in g else 0}
        any_seq = 0
        total = 0
        for marker in markers:
            c = [counts.get((s, marker), 0) for s in g["species"]]
            row[f"species_{marker}"] = sum(1 for x in c if x > 0)
            total += sum(c)
        for s in g["species"]:
            if any(counts.get((s, m), 0) > 0 for m in markers):
                any_seq += 1
        row["endemic_without_any"] = int(sum(
            1 for s, e in zip(g["species"], g["endemic"] if "endemic" in g else [0] * len(g))
            if int(e) == 1 and not any(counts.get((s, m), 0) > 0 for m in markers)))
        row["species_with_any"] = any_seq
        row["species_without_any"] = len(g) - any_seq
        row["sequences"] = total
        rows.append(row)
    df = pd.DataFrame(rows)
    res_csv = DATA / "ena_genus_resolution.csv"
    if res_csv.exists() and len(df):  # genera that ENA taxonomy does not know are marked "no ENA taxon"
        method = dict(pd.read_csv(res_csv, keep_default_na=False)[["wcvp_genus", "method"]].itertuples(index=False))
        df["ena_taxon"] = df["genus"].map(lambda g: "no ENA taxon" if method.get(g, "none") == "none" else method[g])
    return df
