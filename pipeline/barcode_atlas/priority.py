"""Data-driven 'first species to sequence' priority scores (no IUCN / closed sources).

Inputs: species table + WCVP distribution area counts + per-marker sequence counts.
Gap rule and component weights live in config.yaml under ``priority`` (biologist-tunable).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

# Turkish labels for the generated "neden bu tür?" sentence (weighted contribution order).
_WHY_TR = {
    "endemism": "Türkiye endemiği (WCVP)",
    "range_restriction": "WCVP’de dar yayılışlı",
    "genus_gap": "cinsinde veri boşluğu yüksek",
    "phylogenetic_usefulness": "aynı cinsten dizisi olan akrabası var (ağaca hemen eklenir)",
    "family_gap": "ailesinde barkod kapsamı düşük",
}


def _default_priority_cfg() -> dict[str, Any]:
    """Placeholder weights — the biologist adjusts these in config.yaml."""
    return {
        "gap_rule": {
            # A species is a gap when EVERY listed marker has zero sequences.
            "required_markers": ["rbcL", "matK"],
        },
        "weights": {
            "endemism": 0.30,
            "range_restriction": 0.20,
            "genus_gap": 0.20,
            "phylogenetic_usefulness": 0.15,
            "family_gap": 0.15,
        },
        "sensitivity_weight_sets": {
            "equal": {
                "endemism": 0.20,
                "range_restriction": 0.20,
                "genus_gap": 0.20,
                "phylogenetic_usefulness": 0.20,
                "family_gap": 0.20,
            },
            "endemism_focus": {
                "endemism": 0.50,
                "range_restriction": 0.20,
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
        },
        "top_n": 100,
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
    if "top_n" in over:
        out["top_n"] = int(over["top_n"])
    return out


def species_csv_path() -> Path:
    """Prefer data/species.csv when it matches the published marker table; else runs/full."""
    primary = DATA / "species.csv"
    full = ROOT / "runs" / "full" / "data" / "species.csv"
    markers = pd.read_csv(MARKER_COUNTS, usecols=["species"])
    n = len(markers)
    if primary.exists() and len(pd.read_csv(primary, usecols=["species"])) == n:
        return primary
    if full.exists() and len(pd.read_csv(full, usecols=["species"])) == n:
        return full
    raise FileNotFoundError(
        f"No species.csv with {n} rows (checked {primary} and {full})."
    )


def native_area_counts(wcvp_ids: pd.Series) -> pd.Series:
    """plant_name_id -> number of native, non-extinct, non-doubtful WCVP level-3 areas."""
    ids = set(wcvp_ids.astype(str))
    dist = pd.read_csv(
        DIST_FILE,
        sep="|",
        usecols=["plant_name_id", "area_code_l3", "introduced", "extinct", "location_doubtful"],
        dtype=str,
    )
    d = dist[dist["plant_name_id"].isin(ids)].copy()
    for c in ("introduced", "extinct", "location_doubtful"):
        d[c] = d[c].fillna("0")
    native = d[(d["introduced"] == "0") & (d["extinct"] == "0") & (d["location_doubtful"] == "0")]
    return native.groupby("plant_name_id")["area_code_l3"].nunique()


def is_gap_row(row: pd.Series, required_markers: list[str]) -> bool:
    """True when every required marker has zero sequences."""
    return all(int(row.get(f"n_{m}", 0) or 0) == 0 for m in required_markers)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    missing = [k for k in COMPONENT_KEYS if k not in weights]
    if missing:
        raise ValueError(f"priority weights missing keys: {missing}")
    total = float(sum(float(weights[k]) for k in COMPONENT_KEYS))
    if total <= 0:
        raise ValueError("priority weights must sum to a positive number")
    return {k: float(weights[k]) / total for k in COMPONENT_KEYS}


def load_species_frame(priority_cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    """One row per Turkey species with marker counts and WCVP area count."""
    pcfg = resolve_priority_cfg({"priority": priority_cfg} if priority_cfg else None)
    markers_needed = list(pcfg["gap_rule"]["required_markers"])
    sp = pd.read_csv(species_csv_path())
    mc = pd.read_csv(MARKER_COUNTS)
    df = sp.merge(mc[["species", "n_rbcL", "n_matK", "n_ITS"]], on="species", how="inner", validate="one_to_one")
    areas = native_area_counts(df["wcvp_id"])
    df["n_wcvp_areas"] = df["wcvp_id"].astype(str).map(areas).fillna(0).astype(int)
    if (df["n_wcvp_areas"] <= 0).any():
        bad = int((df["n_wcvp_areas"] <= 0).sum())
        raise ValueError(f"{bad} species have no native WCVP areas after join")
    df["n_any"] = df[["n_rbcL", "n_matK", "n_ITS"]].sum(axis=1)
    df["is_gap"] = df.apply(lambda r: is_gap_row(r, markers_needed), axis=1)
    return df


def compute_components(df: pd.DataFrame) -> pd.DataFrame:
    """Add 0–1 component columns for every species (gap flag already on the frame)."""
    out = df.copy()
    # Genus / family coverage uses the same gap definition as the priority pool.
    g_stats = out.groupby("genus").agg(
        genus_n=("species", "size"),
        genus_n_gap=("is_gap", "sum"),
        genus_n_with_any=("n_any", lambda s: int((s > 0).sum())),
    )
    f_stats = out.groupby("family").agg(
        family_n=("species", "size"),
        family_n_gap=("is_gap", "sum"),
    )
    out = out.join(g_stats, on="genus").join(f_stats, on="family")
    out["endemism"] = out["endemic"].astype(int).clip(0, 1).astype(float)
    out["range_restriction"] = (1.0 / out["n_wcvp_areas"].astype(float)).clip(0, 1)
    out["genus_gap"] = (out["genus_n_gap"] / out["genus_n"]).astype(float)
    # Sequenced relative = at least one congener with any barcode sequence.
    out["phylogenetic_usefulness"] = (out["genus_n_with_any"] > 0).astype(float)
    out["family_gap"] = (out["family_n_gap"] / out["family_n"]).astype(float)
    return out


def score_frame(components: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    w = normalize_weights(weights)
    scored = components.copy()
    scored["total_score"] = sum(scored[k] * w[k] for k in COMPONENT_KEYS)
    scored["weight_endemism"] = w["endemism"]
    scored["weight_range_restriction"] = w["range_restriction"]
    scored["weight_genus_gap"] = w["genus_gap"]
    scored["weight_phylogenetic_usefulness"] = w["phylogenetic_usefulness"]
    scored["weight_family_gap"] = w["family_gap"]
    return scored


def why_sentence(row: pd.Series, weights: dict[str, float], top_k: int = 3) -> str:
    """Plain-Turkish sentence listing the components that drove the rank."""
    w = normalize_weights(weights)
    contrib = sorted(((k, float(row[k]) * w[k]) for k in COMPONENT_KEYS), key=lambda x: -x[1])
    parts = []
    for key, val in contrib:
        if val <= 0:
            continue
        label = _WHY_TR[key]
        if key == "range_restriction":
            label = f"WCVP’de {int(row['n_wcvp_areas'])} alanda (dar yayılış)"
        elif key == "genus_gap":
            pct = 100.0 * float(row["genus_gap"])
            label = f"cinsinde veri boşluğu yüksek (%{pct:.0f})"
        elif key == "family_gap":
            pct = 100.0 * float(row["family_gap"])
            label = f"ailesinde barkod kapsamı düşük (boşluk %{pct:.0f})"
        parts.append(label)
        if len(parts) >= top_k:
            break
    if not parts:
        return "Öncelik bileşenleri bu tür için sıfır; liste yalnızca veri boşluğu adayıdır."
    return "Öncelikli çünkü " + "; ".join(parts) + "."


def rank_gaps(scored: pd.DataFrame, weights: dict[str, float], top_n: int | None = None) -> pd.DataFrame:
    gaps = scored[scored["is_gap"]].copy()
    gaps = gaps.sort_values(
        ["total_score", "endemism", "range_restriction", "genus_gap", "species"],
        ascending=[False, False, False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    gaps.insert(0, "rank", gaps.index + 1)
    gaps["neden_bu_tur"] = gaps.apply(lambda r: why_sentence(r, weights), axis=1)
    for col in EMPTY_MANUAL:
        gaps[col] = pd.Series([""] * len(gaps), index=gaps.index, dtype="string")
    if top_n is not None:
        return gaps.head(int(top_n)).copy()
    return gaps


def sensitivity_table(
    components: pd.DataFrame,
    default_weights: dict[str, float],
    alt_sets: dict[str, dict[str, float]],
    top_n: int,
) -> pd.DataFrame:
    """Overlap of top-N species under default, equal, and other named weight sets."""
    sets = {"default": default_weights, **alt_sets}
    tops: dict[str, set[str]] = {}
    for name, weights in sets.items():
        ranked = rank_gaps(score_frame(components, weights), weights, top_n=top_n)
        tops[name] = set(ranked["species"].tolist())
    rows = []
    names = list(tops)
    for i, a in enumerate(names):
        for b in names[i:]:
            inter = len(tops[a] & tops[b])
            rows.append({
                "set_a": a,
                "set_b": b,
                "top_n": top_n,
                "overlap_count": inter,
                "overlap_fraction": round(inter / top_n, 4),
            })
    return pd.DataFrame(rows)


def export_columns() -> list[str]:
    return [
        "rank", "species", "family", "genus", "endemic", "n_wcvp_areas",
        "n_rbcL", "n_matK", "n_ITS",
        "endemism", "range_restriction", "genus_gap", "phylogenetic_usefulness", "family_gap",
        "total_score", "neden_bu_tur",
        *EMPTY_MANUAL,
    ]


def write_web_payload(top: pd.DataFrame, pcfg: dict[str, Any]) -> None:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    # Downloadable CSV next to other public data files.
    top[export_columns()].to_csv(WEB_DATA / "priority_species_top100.csv", index=False)
    payload = {
        "generated_from": "pipeline/barcode_atlas/priority.py",
        "gap_rule": pcfg["gap_rule"],
        "weights": normalize_weights(pcfg["weights"]),
        "top_n": int(pcfg["top_n"]),
        "n_scored_gaps": None,  # filled by caller if desired
        "species": [
            {
                "rank": int(r.rank),
                "species": r.species,
                "family": r.family,
                "genus": r.genus,
                "endemic": int(r.endemic),
                "n_wcvp_areas": int(r.n_wcvp_areas),
                "endemism": float(r.endemism),
                "range_restriction": float(r.range_restriction),
                "genus_gap": float(r.genus_gap),
                "phylogenetic_usefulness": float(r.phylogenetic_usefulness),
                "family_gap": float(r.family_gap),
                "total_score": float(r.total_score),
                "neden_bu_tur": r.neden_bu_tur,
            }
            for r in top.itertuples(index=False)
        ],
    }
    with open(WEB_DATA / "priority_top100.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def run_priority(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score gap species, write CSVs / web JSON, return summary stats from the files just written."""
    pcfg = resolve_priority_cfg(cfg)
    weights = pcfg["weights"]
    top_n = int(pcfg["top_n"])
    frame = load_species_frame(pcfg)
    components = compute_components(frame)
    scored = score_frame(components, weights)
    all_gaps = rank_gaps(scored, weights, top_n=None)
    top = all_gaps.head(top_n).copy()

    EXPORTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for col in EMPTY_MANUAL:
        all_gaps[col] = ""
        top[col] = ""
    all_gaps[export_columns()].to_csv(EXPORTS / "priority_all_scored.csv", index=False)
    top[export_columns()].to_csv(EXPORTS / "priority_species_top100.csv", index=False)
    sens = sensitivity_table(components, weights, pcfg["sensitivity_weight_sets"], top_n)
    sens.to_csv(RESULTS / "priority_sensitivity.csv", index=False)

    write_web_payload(top, pcfg)
    # patch n_scored into json
    path = WEB_DATA / "priority_top100.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["n_scored_gaps"] = int(len(all_gaps))
    payload["n_species_total"] = int(len(frame))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "n_species": int(len(frame)),
        "n_gaps": int(len(all_gaps)),
        "top_n": top_n,
        "top_species": top["species"].head(5).tolist(),
        "top_endemic_in_100": int(top["endemic"].sum()),
        "sensitivity": sens,
    }


def main(config_path: str | Path | None = None) -> None:
    cfg_path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "config.yaml"
    cfg = load_config(cfg_path)
    summary = run_priority(cfg)
    print(
        f"[priority] scored {summary['n_gaps']} gap species "
        f"(of {summary['n_species']}); wrote top {summary['top_n']}",
        flush=True,
    )
    print("[priority] top 5:", ", ".join(summary["top_species"]), flush=True)


if __name__ == "__main__":
    main()
