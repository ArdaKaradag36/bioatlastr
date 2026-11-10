"""Data-driven sequencing priority (v2): continuous scores, caps, robust-core sensitivity.

No IUCN / closed sources. Gap rule and weights live under ``priority`` in config.yaml.
Level-4 WCVP units are not in the distribution file; range uses level-3 areas + level-2 regions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import load_config
from .paths import DATA, RAW, RESULTS, ROOT, WEB_DATA

EXPORTS = ROOT / "exports"
DIST_FILE = RAW / "wcvp" / "wcvp_distribution.csv"
MARKER_COUNTS = RESULTS / "species_marker_counts.csv"
COMPONENT_KEYS = (
    "endemism",
    "range_restriction",
    "genus_gap",
    "phylogenetic_usefulness",
    "family_gap",
)
EMPTY_MANUAL = (
    "threat_status_manual",
    "specimen_availability",
    "collection_difficulty",
    "notes",
)
# Deterministic order after total_score (never species name).
TIEBREAK_COLS = (
    "genus_n_with_any",  # more sequenced congeners first
    "n_wcvp_areas",      # fewer areas first → ascending
    "n_wcvp_regions",
    "genus_n_gap",       # more absolute genus gaps first
    "wcvp_id",           # stable numeric id
)
TIEBREAK_ASC = {
    "genus_n_with_any": False,
    "n_wcvp_areas": True,
    "n_wcvp_regions": True,
    "genus_n_gap": False,
    "wcvp_id": True,
}

_WHY_TR = {
    "endemism": "Türkiye endemiği (WCVP)",
    "range_restriction": "WCVP’de dar yayılışlı",
    "genus_gap": "cinsinde veri açığı yüksek",
    "phylogenetic_usefulness": "dizili akrabaları olan bir cinste (ağaca eklenir)",
    "family_gap": "ailesinde barkod kapsamı düşük",
}


def _default_priority_cfg() -> dict[str, Any]:
    return {
        "gap_rule": {"required_markers": ["rbcL", "matK"]},
        "weights": {
            "endemism": 0.25,
            "range_restriction": 0.25,
            "genus_gap": 0.20,
            "phylogenetic_usefulness": 0.15,
            "family_gap": 0.15,
        },
        "sensitivity_weight_sets": {
            "equal": {k: 0.20 for k in COMPONENT_KEYS},
            "endemism_focus": {
                "endemism": 0.45,
                "range_restriction": 0.25,
                "genus_gap": 0.10,
                "phylogenetic_usefulness": 0.10,
                "family_gap": 0.10,
            },
            "coverage_focus": {
                "endemism": 0.10,
                "range_restriction": 0.10,
                "genus_gap": 0.35,
                "phylogenetic_usefulness": 0.20,
                "family_gap": 0.25,
            },
            "range_focus": {
                "endemism": 0.15,
                "range_restriction": 0.45,
                "genus_gap": 0.15,
                "phylogenetic_usefulness": 0.10,
                "family_gap": 0.15,
            },
            "phylo_focus": {
                "endemism": 0.15,
                "range_restriction": 0.15,
                "genus_gap": 0.15,
                "phylogenetic_usefulness": 0.40,
                "family_gap": 0.15,
            },
        },
        "top_n": 100,
        "max_per_genus": 3,
        "max_per_family": 12,
        "top_per_family": 3,
    }


def resolve_priority_cfg(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    base = _default_priority_cfg()
    if not cfg:
        return base
    over = cfg.get("priority") or {}
    out = dict(base)
    out["gap_rule"] = {**base["gap_rule"], **(over.get("gap_rule") or {})}
    out["weights"] = {**base["weights"], **(over.get("weights") or {})}
    sens = dict(base["sensitivity_weight_sets"])
    sens.update(over.get("sensitivity_weight_sets") or {})
    out["sensitivity_weight_sets"] = sens
    for key in ("top_n", "max_per_genus", "max_per_family", "top_per_family"):
        if key in over:
            out[key] = int(over[key])
    return out


def species_csv_path() -> Path:
    primary = DATA / "species.csv"
    full = ROOT / "runs" / "full" / "data" / "species.csv"
    markers = pd.read_csv(MARKER_COUNTS, usecols=["species"])
    n = len(markers)
    if primary.exists() and len(pd.read_csv(primary, usecols=["species"])) == n:
        return primary
    if full.exists() and len(pd.read_csv(full, usecols=["species"])) == n:
        return full
    raise FileNotFoundError(f"No species.csv with {n} rows (checked {primary} and {full}).")


def native_area_and_region_counts(wcvp_ids: pd.Series) -> pd.DataFrame:
    """plant_name_id -> n_wcvp_areas (L3) and n_wcvp_regions (L2). No L4 in WCVP export."""
    ids = set(wcvp_ids.astype(str))
    dist = pd.read_csv(
        DIST_FILE,
        sep="|",
        usecols=[
            "plant_name_id",
            "region_code_l2",
            "area_code_l3",
            "introduced",
            "extinct",
            "location_doubtful",
        ],
        dtype=str,
    )
    d = dist[dist["plant_name_id"].isin(ids)].copy()
    for c in ("introduced", "extinct", "location_doubtful"):
        d[c] = d[c].fillna("0")
    native = d[(d["introduced"] == "0") & (d["extinct"] == "0") & (d["location_doubtful"] == "0")]
    areas = native.groupby("plant_name_id")["area_code_l3"].nunique().rename("n_wcvp_areas")
    regions = native.groupby("plant_name_id")["region_code_l2"].nunique().rename("n_wcvp_regions")
    return pd.concat([areas, regions], axis=1).fillna(0).astype(int)


def is_gap_row(row: pd.Series, required_markers: list[str]) -> bool:
    return all(int(row.get(f"n_{m}", 0) or 0) == 0 for m in required_markers)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    missing = [k for k in COMPONENT_KEYS if k not in weights]
    if missing:
        raise ValueError(f"priority weights missing keys: {missing}")
    total = float(sum(float(weights[k]) for k in COMPONENT_KEYS))
    if total <= 0:
        raise ValueError("priority weights must sum to a positive number")
    return {k: float(weights[k]) / total for k in COMPONENT_KEYS}


def _pct_rank(series: pd.Series) -> pd.Series:
    """Empirical percentile rank in [0, 1]; ties get average rank. Constant series → 0.5."""
    if series.nunique(dropna=False) <= 1:
        return pd.Series(np.full(len(series), 0.5), index=series.index, dtype=float)
    return series.rank(method="average", pct=True).astype(float)


def load_species_frame(priority_cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    pcfg = resolve_priority_cfg({"priority": priority_cfg} if priority_cfg else None)
    markers_needed = list(pcfg["gap_rule"]["required_markers"])
    sp = pd.read_csv(species_csv_path())
    mc = pd.read_csv(MARKER_COUNTS)
    df = sp.merge(
        mc[["species", "n_rbcL", "n_matK", "n_ITS"]],
        on="species",
        how="inner",
        validate="one_to_one",
    )
    geo = native_area_and_region_counts(df["wcvp_id"])
    df["wcvp_id"] = df["wcvp_id"].astype(str)
    df = df.join(geo, on="wcvp_id")
    df["n_wcvp_areas"] = df["n_wcvp_areas"].fillna(0).astype(int)
    df["n_wcvp_regions"] = df["n_wcvp_regions"].fillna(0).astype(int)
    if (df["n_wcvp_areas"] <= 0).any():
        raise ValueError(f"{int((df.n_wcvp_areas <= 0).sum())} species have no native WCVP areas")
    df["n_any"] = df[["n_rbcL", "n_matK", "n_ITS"]].sum(axis=1)
    df["is_gap"] = [is_gap_row(r, markers_needed) for _, r in df.iterrows()]
    return df


def compute_components(df: pd.DataFrame) -> pd.DataFrame:
    """Continuous 0–1 components (endemism stays binary; others use ranks / logs)."""
    out = df.copy()
    g_stats = out.groupby("genus", sort=False).agg(
        genus_n=("species", "size"),
        genus_n_gap=("is_gap", "sum"),
        genus_n_with_any=("n_any", lambda s: int((s > 0).sum())),
    )
    f_stats = out.groupby("family", sort=False).agg(
        family_n=("species", "size"),
        family_n_gap=("is_gap", "sum"),
    )
    out = out.join(g_stats, on="genus").join(f_stats, on="family")
    out["genus_gap_fraction"] = (out["genus_n_gap"] / out["genus_n"]).astype(float)
    out["family_gap_fraction"] = (out["family_n_gap"] / out["family_n"]).astype(float)

    gaps = out["is_gap"]
    # Range: rarer L3 + L2 → higher; percentile among gap species only (discrimination inside pool).
    inv_areas = 1.0 / out["n_wcvp_areas"].astype(float)
    inv_regions = 1.0 / out["n_wcvp_regions"].clip(lower=1).astype(float)
    area_pct = pd.Series(0.0, index=out.index)
    region_pct = pd.Series(0.0, index=out.index)
    area_pct.loc[gaps] = _pct_rank(inv_areas.loc[gaps]).values
    region_pct.loc[gaps] = _pct_rank(inv_regions.loc[gaps]).values
    out["range_restriction"] = (0.7 * area_pct + 0.3 * region_pct).clip(0, 1)

    # Genus / family deficit: blend fraction with absolute-gap percentile (breaks saturation).
    g_frac_pct = pd.Series(0.0, index=out.index)
    g_abs_pct = pd.Series(0.0, index=out.index)
    f_frac_pct = pd.Series(0.0, index=out.index)
    f_abs_pct = pd.Series(0.0, index=out.index)
    g_frac_pct.loc[gaps] = _pct_rank(out.loc[gaps, "genus_gap_fraction"]).values
    g_abs_pct.loc[gaps] = _pct_rank(out.loc[gaps, "genus_n_gap"].astype(float)).values
    f_frac_pct.loc[gaps] = _pct_rank(out.loc[gaps, "family_gap_fraction"]).values
    f_abs_pct.loc[gaps] = _pct_rank(out.loc[gaps, "family_n_gap"].astype(float)).values
    out["genus_gap"] = (0.5 * g_frac_pct + 0.5 * g_abs_pct).clip(0, 1)
    out["family_gap"] = (0.5 * f_frac_pct + 0.5 * f_abs_pct).clip(0, 1)

    # Phylogenetic usefulness: continuous in log1p(# sequenced congeners).
    max_anch = max(int(out["genus_n_with_any"].max()), 1)
    out["phylogenetic_usefulness"] = (
        np.log1p(out["genus_n_with_any"].astype(float)) / np.log1p(float(max_anch))
    ).clip(0, 1)

    out["endemism"] = out["endemic"].astype(int).clip(0, 1).astype(float)
    return out


def score_frame(components: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    w = normalize_weights(weights)
    scored = components.copy()
    scored["total_score"] = sum(scored[k] * w[k] for k in COMPONENT_KEYS)
    return scored


def sort_by_score_and_ties(df: pd.DataFrame) -> pd.DataFrame:
    """Sort gaps by score then deterministic tie-breakers (no alphabetical species)."""
    out = df.copy()
    by = ["total_score", *TIEBREAK_COLS]
    ascending = [False, *[TIEBREAK_ASC[c] for c in TIEBREAK_COLS]]
    # Ensure numeric wcvp_id for stable order
    out["_wcvp_num"] = pd.to_numeric(out["wcvp_id"], errors="coerce").fillna(0).astype(np.int64)
    by[-1] = "_wcvp_num"
    out = out.sort_values(by, ascending=ascending, kind="mergesort").reset_index(drop=True)
    out = out.drop(columns=["_wcvp_num"])
    return out


def assign_tie_groups(df: pd.DataFrame) -> pd.Series:
    """Same tie_group when score and all tie-break keys match (before final wcvp_id)."""
    keys = ["total_score", "genus_n_with_any", "n_wcvp_areas", "n_wcvp_regions", "genus_n_gap"]
    rounded = df[keys].copy()
    rounded["total_score"] = rounded["total_score"].round(12)
    codes = rounded.astype(str).agg("|".join, axis=1)
    # Dense ids 1..n for groups that appear more than once; unique rows get their own id still
    return codes.astype("category").cat.codes.astype(int) + 1


def why_sentence(
    row: pd.Series,
    weights: dict[str, float],
    *,
    capped: bool = False,
    max_per_genus: int | None = None,
    top_k: int = 3,
) -> str:
    w = normalize_weights(weights)
    contrib = sorted(((k, float(row[k]) * w[k]) for k in COMPONENT_KEYS), key=lambda x: -x[1])
    parts: list[str] = []
    for key, val in contrib:
        if val <= 0:
            continue
        if key == "range_restriction":
            label = (
                f"WCVP’de {int(row['n_wcvp_areas'])} alan / "
                f"{int(row['n_wcvp_regions'])} bölge (dar yayılış yüzdelik)"
            )
        elif key == "genus_gap":
            label = (
                f"cins açığı yüksek (oran %{100 * float(row['genus_gap_fraction']):.0f}, "
                f"{int(row['genus_n_gap'])}/{int(row['genus_n'])} tür)"
            )
        elif key == "family_gap":
            label = (
                f"aile açığı yüksek (oran %{100 * float(row['family_gap_fraction']):.0f})"
            )
        elif key == "phylogenetic_usefulness":
            n = int(row["genus_n_with_any"])
            label = (
                f"aynı cinsten {n} dizili tür var (ağaca eklenmeye uygun)"
                if n > 0
                else "cinsinde henüz dizili tür yok"
            )
        else:
            label = _WHY_TR[key]
        parts.append(label)
        if len(parts) >= top_k:
            break
    if not parts:
        base = "Öncelik bileşenleri bu tür için zayıf; yine de veri boşluğu adayıdır."
    else:
        base = "Öncelikli çünkü " + "; ".join(parts) + "."
    if capped and max_per_genus is not None:
        base += (
            f" Listeye cins başına en fazla {max_per_genus} tür alınacak şekilde "
            "seçildi (çeşitlilik tavanı)."
        )
    return base


def select_with_caps(
    ordered: pd.DataFrame,
    top_n: int,
    max_per_genus: int,
    max_per_family: int,
) -> pd.DataFrame:
    """Greedy take next species if genus/family caps allow."""
    picked: list[int] = []
    g_count: dict[str, int] = {}
    f_count: dict[str, int] = {}
    for idx, row in ordered.iterrows():
        g, f = row["genus"], row["family"]
        if g_count.get(g, 0) >= max_per_genus:
            continue
        if f_count.get(f, 0) >= max_per_family:
            continue
        picked.append(idx)
        g_count[g] = g_count.get(g, 0) + 1
        f_count[f] = f_count.get(f, 0) + 1
        if len(picked) >= top_n:
            break
    out = ordered.loc[picked].copy().reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    return out


def rank_gaps(
    scored: pd.DataFrame,
    weights: dict[str, float],
    *,
    top_n: int | None = None,
    max_per_genus: int | None = None,
    max_per_family: int | None = None,
    apply_caps: bool = False,
) -> pd.DataFrame:
    gaps = scored[scored["is_gap"]].copy()
    gaps = sort_by_score_and_ties(gaps)
    gaps["tie_group"] = assign_tie_groups(gaps)
    # mark groups that actually have size > 1
    sizes = gaps["tie_group"].value_counts()
    gaps["tie_group_size"] = gaps["tie_group"].map(sizes).astype(int)

    if apply_caps:
        assert max_per_genus is not None and max_per_family is not None and top_n is not None
        top = select_with_caps(gaps, top_n, max_per_genus, max_per_family)
        top["neden_bu_tur"] = top.apply(
            lambda r: why_sentence(r, weights, capped=True, max_per_genus=max_per_genus),
            axis=1,
        )
    else:
        top = gaps if top_n is None else gaps.head(int(top_n)).copy()
        if "rank" not in top.columns:
            top.insert(0, "rank", np.arange(1, len(top) + 1))
        top["neden_bu_tur"] = top.apply(lambda r: why_sentence(r, weights, capped=False), axis=1)

    for col in EMPTY_MANUAL:
        top[col] = pd.Series([""] * len(top), index=top.index, dtype="string")
    return top


def list_top_per_family(ordered_gaps: pd.DataFrame, per_family: int) -> pd.DataFrame:
    rows = []
    for fam, block in ordered_gaps.groupby("family", sort=False):
        take = block.head(per_family)
        for i, (_, r) in enumerate(take.iterrows(), start=1):
            rows.append({**r.to_dict(), "family_pick_rank": i})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return sort_by_score_and_ties(out).reset_index(drop=True)


def list_first_of_empty_genera(ordered_gaps: pd.DataFrame) -> pd.DataFrame:
    """Best-scoring gap species for each genus with zero sequences (any marker)."""
    empty = ordered_gaps[ordered_gaps["genus_n_with_any"] == 0]
    first = empty.groupby("genus", sort=False, group_keys=False).head(1)
    return first.reset_index(drop=True)


def list_tree_gain(ordered_gaps: pd.DataFrame) -> pd.DataFrame:
    """Genera that already have ≥1 sequenced species: one new sequence attaches to an existing tree.

    Gain score = n_gap_species in genus (how many tips a barcoding campaign could add).
    One representative (best gap species) per genus; sorted by gain then score.
    """
    has_anchor = ordered_gaps[ordered_gaps["genus_n_with_any"] > 0].copy()
    if has_anchor.empty:
        return has_anchor
    has_anchor["tree_gain"] = has_anchor["genus_n_gap"].astype(int)
    rep = has_anchor.groupby("genus", sort=False, group_keys=False).head(1)
    rep = rep.sort_values(
        ["tree_gain", "total_score", "genus_n_with_any", "n_wcvp_areas", "wcvp_id"],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    rep.insert(0, "gain_rank", np.arange(1, len(rep) + 1))
    return rep


def spearman_corr(a: pd.Series, b: pd.Series) -> float:
    """Spearman ρ without SciPy (rank both series, then Pearson on ranks)."""
    if len(a) < 2:
        return float("nan")
    ra = a.rank(method="average")
    rb = b.rank(method="average")
    if ra.nunique() <= 1 or rb.nunique() <= 1:
        return float("nan")
    return float(np.corrcoef(ra.to_numpy(), rb.to_numpy())[0, 1])



def sensitivity_analysis(
    components: pd.DataFrame,
    default_weights: dict[str, float],
    alt_sets: dict[str, dict[str, float]],
    *,
    top_n: int,
    max_per_genus: int,
    max_per_family: int,
) -> tuple[pd.DataFrame, set[str], dict[str, set[str]]]:
    sets = {"default": default_weights, **alt_sets}
    tops: dict[str, set[str]] = {}
    full_scores: dict[str, pd.Series] = {}
    for name, weights in sets.items():
        scored = score_frame(components, weights)
        gaps = scored[scored["is_gap"]].copy()
        full_scores[name] = sort_by_score_and_ties(gaps).set_index("species")["total_score"]
        capped = rank_gaps(
            scored,
            weights,
            top_n=top_n,
            max_per_genus=max_per_genus,
            max_per_family=max_per_family,
            apply_caps=True,
        )
        tops[name] = set(capped["species"].tolist())

    robust = set.intersection(*tops.values()) if tops else set()
    rows = []
    names = list(tops)
    for i, a in enumerate(names):
        for b in names[i:]:
            inter = len(tops[a] & tops[b])
            # align full scores on shared index
            sa, sb = full_scores[a], full_scores[b]
            common = sa.index.intersection(sb.index)
            rho = spearman_corr(sa.loc[common], sb.loc[common])
            rows.append({
                "set_a": a,
                "set_b": b,
                "top_n": top_n,
                "capped_overlap_count": inter,
                "capped_overlap_fraction": round(inter / top_n, 4),
                "spearman_full_scores": None if np.isnan(rho) else round(rho, 6),
                "robust_core_size": len(robust),
            })
    return pd.DataFrame(rows), robust, tops


def component_deciles(gaps: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in COMPONENT_KEYS:
        s = gaps[c]
        tied_max = int(np.isclose(s, s.max()).sum())
        qs = s.quantile([i / 10 for i in range(11)])
        row = {
            "component": c,
            "nunique": int(s.nunique()),
            "min": float(s.min()),
            "max": float(s.max()),
            "tied_at_max": tied_max,
        }
        for i, v in qs.items():
            row[f"p{int(i * 100)}"] = float(v)
        rows.append(row)
    return pd.DataFrame(rows)


def export_columns(extra: list[str] | None = None) -> list[str]:
    cols = [
        "rank", "species", "family", "genus", "endemic",
        "n_wcvp_areas", "n_wcvp_regions",
        "n_rbcL", "n_matK", "n_ITS",
        "genus_n", "genus_n_gap", "genus_n_with_any", "genus_gap_fraction",
        "family_n", "family_n_gap", "family_gap_fraction",
        "endemism", "range_restriction", "genus_gap", "phylogenetic_usefulness", "family_gap",
        "total_score", "tie_group", "tie_group_size", "robust_core", "neden_bu_tur",
        *EMPTY_MANUAL,
    ]
    if extra:
        for e in extra:
            if e not in cols:
                cols.append(e)
    return cols


def _records(df: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    out = []
    for _, r in df.iterrows():
        item: dict[str, Any] = {}
        for c in cols:
            if c not in r.index:
                continue
            v = r[c]
            if pd.isna(v):
                item[c] = "" if c in EMPTY_MANUAL or c == "neden_bu_tur" else None
            elif isinstance(v, (np.integer,)):
                item[c] = int(v)
            elif isinstance(v, (np.floating, float)):
                item[c] = float(v)
            else:
                item[c] = v
        out.append(item)
    return out


def write_web_payload(
    top: pd.DataFrame,
    lists: dict[str, pd.DataFrame],
    pcfg: dict[str, Any],
    diagnosis: dict[str, Any],
    sens: pd.DataFrame,
) -> None:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    top_cols = [c for c in export_columns() if c in top.columns]
    top[top_cols].to_csv(WEB_DATA / "priority_species_top100.csv", index=False)
    web_cols = [
        "rank", "species", "family", "genus", "endemic",
        "n_wcvp_areas", "n_wcvp_regions", "genus_n_with_any", "genus_n_gap",
        "endemism", "range_restriction", "genus_gap", "phylogenetic_usefulness", "family_gap",
        "total_score", "tie_group", "tie_group_size", "robust_core", "neden_bu_tur",
    ]
    payload = {
        "generated_from": "pipeline/barcode_atlas/priority.py",
        "gap_rule": pcfg["gap_rule"],
        "weights": normalize_weights(pcfg["weights"]),
        "caps": {
            "max_per_genus": int(pcfg["max_per_genus"]),
            "max_per_family": int(pcfg["max_per_family"]),
            "top_n": int(pcfg["top_n"]),
        },
        "notes": {
            "range": "WCVP distribution has no level-4 units; range uses level-3 areas + level-2 regions.",
            "tree_gain": (
                "Genera with ≥1 sequenced species; gain = number of gap species in the genus "
                "(one new barcode attaches to an existing comparative set)."
            ),
            "empty_genera": "Best-scoring gap species for each genus with zero sequences in any marker.",
            "caps": "Top-100 is selected greedily by score with genus and family caps.",
        },
        "diagnosis": diagnosis,
        "sensitivity_summary": {
            "robust_core_size": int(diagnosis.get("robust_core_size", 0)),
            "pairs": sens.to_dict(orient="records"),
        },
        "lists": {
            "top100": _records(top, web_cols),
            "top_per_family": _records(
                lists["top_per_family"],
                [c for c in web_cols + ["family_pick_rank"] if c in lists["top_per_family"].columns or c in web_cols],
            ),
            "empty_genera": _records(lists["empty_genera"], web_cols),
            "tree_gain": _records(
                lists["tree_gain"],
                [c for c in ["gain_rank", "tree_gain", *web_cols] if c in lists["tree_gain"].columns or c in web_cols],
            ),
        },
    }
    with open(WEB_DATA / "priority_top100.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def run_priority(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    pcfg = resolve_priority_cfg(cfg)
    weights = pcfg["weights"]
    top_n = int(pcfg["top_n"])
    max_g = int(pcfg["max_per_genus"])
    max_f = int(pcfg["max_per_family"])

    frame = load_species_frame(pcfg)
    components = compute_components(frame)
    scored = score_frame(components, weights)
    all_ordered = rank_gaps(scored, weights, apply_caps=False)
    top = rank_gaps(
        scored,
        weights,
        top_n=top_n,
        max_per_genus=max_g,
        max_per_family=max_f,
        apply_caps=True,
    )

    sens, robust, _tops = sensitivity_analysis(
        components,
        weights,
        pcfg["sensitivity_weight_sets"],
        top_n=top_n,
        max_per_genus=max_g,
        max_per_family=max_f,
    )
    all_ordered["robust_core"] = all_ordered["species"].isin(robust).astype(int)
    top["robust_core"] = top["species"].isin(robust).astype(int)

    lists = {
        "top_per_family": list_top_per_family(all_ordered, int(pcfg["top_per_family"])),
        "empty_genera": list_first_of_empty_genera(all_ordered),
        "tree_gain": list_tree_gain(all_ordered),
    }
    for name, df in lists.items():
        if df.empty:
            continue
        df["robust_core"] = df["species"].isin(robust).astype(int) if "species" in df.columns else 0
        if "neden_bu_tur" not in df.columns:
            df["neden_bu_tur"] = df.apply(lambda r: why_sentence(r, weights), axis=1)
        for col in EMPTY_MANUAL:
            if col not in df.columns:
                df[col] = ""

    # Diagnosis
    gap_scores = all_ordered
    max_score = float(gap_scores["total_score"].max())
    tied_max = gap_scores[np.isclose(gap_scores["total_score"], max_score)]
    deciles = component_deciles(gap_scores)
    remaining_ties = int((top["tie_group_size"] > 1).sum())
    diagnosis = {
        "n_gaps": int(len(gap_scores)),
        "tied_at_max_score": int(len(tied_max)),
        "tied_at_max_genera": sorted(tied_max["genus"].unique().tolist()),
        "max_score": max_score,
        "saturating_components": [
            c for c in COMPONENT_KEYS
            if int(gap_scores[c].nunique()) <= 2 or float(gap_scores[c].quantile(0.6)) >= 0.99
        ],
        "component_deciles": deciles.to_dict(orient="records"),
        "robust_core_size": int(len(robust)),
        "top100_genera": int(top["genus"].nunique()),
        "top100_families": int(top["family"].nunique()),
        "top100_endemic": int(top["endemic"].sum()),
        "remaining_ties_in_top100": remaining_ties,
    }

    EXPORTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    all_cols = [c for c in export_columns() if c in all_ordered.columns]
    top_cols = [c for c in export_columns() if c in top.columns]
    all_ordered[all_cols].to_csv(EXPORTS / "priority_all_scored.csv", index=False)
    top[top_cols].to_csv(EXPORTS / "priority_species_top100.csv", index=False)
    lists["top_per_family"].to_csv(EXPORTS / "priority_top3_per_family.csv", index=False)
    lists["empty_genera"].to_csv(EXPORTS / "priority_empty_genera.csv", index=False)
    lists["tree_gain"].to_csv(EXPORTS / "priority_tree_gain.csv", index=False)
    sens.to_csv(RESULTS / "priority_sensitivity.csv", index=False)
    deciles.to_csv(RESULTS / "priority_component_deciles.csv", index=False)
    with open(RESULTS / "priority_diagnosis.json", "w", encoding="utf-8") as fh:
        json.dump(diagnosis, fh, ensure_ascii=False, indent=2)

    print(
        f"[priority] diagnosis: tied_at_max={diagnosis['tied_at_max_score']} "
        f"genera={diagnosis['tied_at_max_genera']} saturating={diagnosis['saturating_components']}",
        flush=True,
    )
    for _, row in deciles.iterrows():
        print(
            f"[priority] decile {row['component']}: nunique={int(row['nunique'])} "
            f"p50={row['p50']:.4f} p90={row['p90']:.4f} tied_at_max={int(row['tied_at_max'])}",
            flush=True,
        )

    write_web_payload(top, lists, pcfg, diagnosis, sens)
    path = WEB_DATA / "priority_top100.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["n_scored_gaps"] = int(len(all_ordered))
    payload["n_species_total"] = int(len(frame))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "n_species": int(len(frame)),
        "n_gaps": int(len(all_ordered)),
        "top_n": top_n,
        "top_species": top["species"].head(10).tolist(),
        "top_scores": [float(x) for x in top["total_score"].head(10)],
        "top_endemic_in_100": int(top["endemic"].sum()),
        "top_genera": int(top["genus"].nunique()),
        "top_families": int(top["family"].nunique()),
        "robust_core_size": int(len(robust)),
        "remaining_ties": remaining_ties,
        "diagnosis": diagnosis,
        "sensitivity": sens,
    }


def main(config_path: str | Path | None = None) -> None:
    cfg_path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "config.yaml"
    summary = run_priority(load_config(cfg_path))
    print(
        f"[priority] scored {summary['n_gaps']} gaps; capped top {summary['top_n']}: "
        f"{summary['top_genera']} genera / {summary['top_families']} families; "
        f"endemic={summary['top_endemic_in_100']}; robust_core={summary['robust_core_size']}",
        flush=True,
    )
    for sp, sc in zip(summary["top_species"], summary["top_scores"], strict=True):
        print(f"  {sc:.4f}  {sp}", flush=True)


if __name__ == "__main__":
    main()
