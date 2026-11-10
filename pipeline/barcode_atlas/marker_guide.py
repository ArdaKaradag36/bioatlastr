"""Paired marker guide: which barcode region works better within the same species set.

Raw success rates are NOT compared across markers (different species sets).
For each family (and each genus in split families), markers are compared only on
species evaluated under the site's strict species-level criterion in BOTH markers.

Combined-marker definition on this branch is ``mean_min_distance``, not
``strict_combined_distance`` — combinations are skipped until that lands.
"""

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from .config import load_config
from .discrimination import species_status_from
from .paths import RESULTS, ROOT, WEB_DATA

PER_SEQ = RESULTS / "discrimination_per_sequence.csv"
GROUP_SUMMARY = RESULTS / "group_summary.csv"
MARKERS = ("rbcL", "matK", "ITS")
Z95 = 1.959963984540054  # exact Φ⁻¹(0.975)


def _default_cfg() -> dict[str, Any]:
    return {
        "min_shared_species": 15,
        "wilson_z": Z95,
        "mcnemar_alpha": 0.05,
    }


def resolve_guide_cfg(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    base = _default_cfg()
    over = (cfg or {}).get("marker_guide") or {}
    out = {**base, **over}
    out["min_shared_species"] = int(out["min_shared_species"])
    out["wilson_z"] = float(out["wilson_z"])
    out["mcnemar_alpha"] = float(out["mcnemar_alpha"])
    return out


def wilson_interval(k: int, n: int, z: float = Z95) -> tuple[float | None, float | None, float | None]:
    """Wilson score 95% CI for k successes in n trials. Returns (rate, low, high)."""
    if n <= 0:
        return None, None, None
    if k < 0 or k > n:
        raise ValueError(f"k={k} outside 0..{n}")
    phat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (phat + z2 / (2.0 * n)) / denom
    half = (z * math.sqrt((phat * (1.0 - phat) + z2 / (4.0 * n)) / n)) / denom
    return phat, max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value for discordant counts b, c (no SciPy).

    Under H0, discordant pairs are Binomial(b+c, 0.5). p = 2 * P(X >= max(b,c)).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = max(b, c)
    # P(X >= k) = sum_{i=k}^{n} C(n,i) / 2^n
    # compute with recursive binomial coeffs to avoid huge factorials
    # start from C(n,0)=1
    coef = 1.0
    total = 0.0
    for i in range(0, n + 1):
        if i >= k:
            total += coef
        # C(n,i+1) = C(n,i) * (n-i)/(i+1)
        if i < n:
            coef *= (n - i) / (i + 1)
    p_one = total / (2.0 ** n)
    return min(1.0, 2.0 * p_one)


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm–Bonferroni step-down adjusted p-values (FWER control).

    Prefer Holm over Benjamini–Hochberg here: recommendations are actionable
    claims (pick marker X), so family-wise error rate control is appropriate.
    """
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [1.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        # p_(k) * (m - k + 1) with 0-based rank k
        val = min(1.0, float(p_values[idx]) * (m - rank))
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def intervals_overlap(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> bool:
    return not (a_hi < b_lo or b_hi < a_lo)


def tr_pct(rate: float | None, digits: int = 1) -> str:
    if rate is None:
        return "—"
    return "%" + f"{rate * 100:.{digits}f}".replace(".", ",")


def tr_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def load_species_status_table() -> pd.DataFrame:
    """One row per (family, genus|'', marker, species) with strict species_status."""
    ps = pd.read_csv(PER_SEQ)
    gs = pd.read_csv(GROUP_SUMMARY)
    gmeta = gs[["group", "family", "genus", "marker"]].drop_duplicates().copy()
    gmeta["genus"] = gmeta["genus"].fillna("").astype(str)
    ev = ps[ps["status"].isin(["success", "ambiguous", "fail"])].copy()
    # per_seq already has family; join genus from group_summary
    merged = ev.merge(
        gmeta[["group", "marker", "genus"]],
        on=["group", "marker"],
        how="left",
    )
    merged["genus"] = merged["genus"].fillna("").astype(str)
    if merged["family"].isna().any():
        raise ValueError("discrimination_per_sequence rows missing family after join")

    rows = []
    for keys, block in merged.groupby(["family", "genus", "marker", "species"], sort=False):
        family, genus, marker, species = keys
        status = species_status_from(block["status"].tolist())
        rows.append({
            "family": family,
            "genus": genus,
            "marker": marker,
            "species": species,
            "species_status": status,
            "success": int(status == "success"),
        })
    return pd.DataFrame(rows)


def paired_compare(
    statuses: dict[str, dict[str, int]],
    marker_a: str,
    marker_b: str,
    *,
    min_shared: int,
    z: float,
    alpha: float,
) -> dict[str, Any]:
    """statuses: species -> {marker: 0/1 success}. Compare A vs B on intersection."""
    shared = [sp for sp, m in statuses.items() if marker_a in m and marker_b in m]
    n = len(shared)
    out: dict[str, Any] = {
        "marker_a": marker_a,
        "marker_b": marker_b,
        "n_shared": n,
        "success_a": 0,
        "success_b": 0,
        "rate_a": None,
        "rate_b": None,
        "wilson_a_low": None,
        "wilson_a_high": None,
        "wilson_b_low": None,
        "wilson_b_high": None,
        "rate_diff_b_minus_a": None,
        "n_a_better": 0,
        "n_b_better": 0,
        "n_both_success": 0,
        "n_both_fail": 0,
        "mcnemar_p": None,
        "mcnemar_p_holm": None,
        "multiple_comparison": "holm",
        "ci_overlap": None,
        "recommendation": "yetersiz veri",
        "clear_difference": False,
    }
    if n == 0:
        return out
    sa = sum(statuses[sp][marker_a] for sp in shared)
    sb = sum(statuses[sp][marker_b] for sp in shared)
    a_better = b_better = both_ok = both_bad = 0
    for sp in shared:
        a, b = statuses[sp][marker_a], statuses[sp][marker_b]
        if a and b:
            both_ok += 1
        elif (not a) and (not b):
            both_bad += 1
        elif a and not b:
            a_better += 1
        else:
            b_better += 1
    ra, a_lo, a_hi = wilson_interval(sa, n, z)
    rb, b_lo, b_hi = wilson_interval(sb, n, z)
    p = mcnemar_exact_p(a_better, b_better)
    overlap = intervals_overlap(a_lo, a_hi, b_lo, b_hi)  # type: ignore[arg-type]
    out.update({
        "success_a": sa,
        "success_b": sb,
        "rate_a": ra,
        "rate_b": rb,
        "wilson_a_low": a_lo,
        "wilson_a_high": a_hi,
        "wilson_b_low": b_lo,
        "wilson_b_high": b_hi,
        "rate_diff_b_minus_a": (rb - ra) if ra is not None and rb is not None else None,
        "n_a_better": a_better,
        "n_b_better": b_better,
        "n_both_success": both_ok,
        "n_both_fail": both_bad,
        "mcnemar_p": p,
        "ci_overlap": overlap,
    })
    # Provisional (raw p); apply_holm_to_pairs overwrites after batch Holm.
    out["mcnemar_p_holm"] = None
    if n < min_shared:
        out["recommendation"] = "yetersiz veri"
        out["clear_difference"] = False
    else:
        clear = p < alpha and sa != sb
        out["clear_difference"] = bool(clear)
        if not clear:
            out["recommendation"] = "fark belirsiz"
        elif sb > sa:
            out["recommendation"] = marker_b
        elif sa > sb:
            out["recommendation"] = marker_a
        else:
            out["recommendation"] = "fark belirsiz"
            out["clear_difference"] = False
    return out


def share_label(n_shared: int, n_family: int) -> str:
    """Turkish 'compared / family total' fragment, e.g. '34 / 1.297 tür'."""
    return f"{tr_num(n_shared)} / {tr_num(n_family)} tür"


def pair_sentence(scope_label: str, row: dict[str, Any], *, genus: str = "") -> str:
    a, b = row["marker_a"], row["marker_b"]
    n = int(row["n_shared"])
    n_fam = int(row.get("n_family_species") or 0)
    rec = row["recommendation"]
    where = f"Bu cinste ({scope_label})" if genus else "Bu familyada"
    share = share_label(n, n_fam) if n_fam else tr_num(n) + " tür"
    if n == 0:
        return f"{where} {a} ile {b} ortak değerlendirilen tür yok (ailede {tr_num(n_fam)} tür)."
    base = (
        f"{where} {share} üzerinden {a} ile {b} aynı tür kümesinde karşılaştırıldı"
        f" ({a}: {tr_pct(row['rate_a'])}, {b}: {tr_pct(row['rate_b'])}"
        f"; Wilson %95 {tr_pct(row['wilson_a_low'])}–{tr_pct(row['wilson_a_high'])} ve "
        f"{tr_pct(row['wilson_b_low'])}–{tr_pct(row['wilson_b_high'])})."
    )
    if rec == "yetersiz veri":
        return base + f" Ortak tür sayısı {tr_num(n)} olduğu için öneri yok (eşik altı)."
    if rec == "fark belirsiz":
        return (
            base
            + " Fark, çoklu karşılaştırma düzeltmesi (Holm) sonrası istatistiksel olarak belirgin değil."
        )
    winner, loser = (b, a) if rec == b else (a, b)
    wr, lr = (row["rate_b"], row["rate_a"]) if winner == b else (row["rate_a"], row["rate_b"])
    return (
        base
        + f" {winner}, {loser}'den daha çok türü ayırdı ({tr_pct(wr)} ve {tr_pct(lr)}; Holm sonrası anlamlı)."
    )


def decide_recommendation(row: dict[str, Any], *, min_shared: int, alpha: float) -> None:
    """Set recommendation / clear_difference from n_shared and Holm-adjusted p (in place)."""
    n = int(row["n_shared"])
    sa, sb = int(row["success_a"]), int(row["success_b"])
    p_adj = row.get("mcnemar_p_holm")
    if n < min_shared:
        row["recommendation"] = "yetersiz veri"
        row["clear_difference"] = False
        return
    clear = (
        p_adj is not None
        and float(p_adj) < alpha
        and sa != sb
    )
    row["clear_difference"] = bool(clear)
    if not clear:
        row["recommendation"] = "fark belirsiz"
    elif sb > sa:
        row["recommendation"] = row["marker_b"]
    elif sa > sb:
        row["recommendation"] = row["marker_a"]
    else:
        row["recommendation"] = "fark belirsiz"
        row["clear_difference"] = False


def apply_holm_to_pairs(pair_rows: list[dict[str, Any]], *, min_shared: int, alpha: float) -> None:
    """Holm-adjust McNemar p across all adequate family/genus pair tests; re-decide recs."""
    tested_idx = [
        i for i, r in enumerate(pair_rows)
        if int(r["n_shared"]) >= min_shared and r.get("mcnemar_p") is not None
    ]
    raw = [float(pair_rows[i]["mcnemar_p"]) for i in tested_idx]
    adjusted = holm_adjust(raw)
    for i, r in enumerate(pair_rows):
        r["mcnemar_p_holm"] = None
        r["multiple_comparison"] = "holm"
    for i, adj in zip(tested_idx, adjusted):
        pair_rows[i]["mcnemar_p_holm"] = adj
    for r in pair_rows:
        decide_recommendation(r, min_shared=min_shared, alpha=alpha)
        r["sentence"] = pair_sentence(
            r["family"] if r["scope_level"] == "family" else f"{r['family']}/{r['genus']}",
            r,
            genus=r.get("genus") or "",
        )


def build_status_maps(table: pd.DataFrame) -> tuple[dict[str, dict[str, dict[str, int]]], dict[tuple[str, str], dict[str, dict[str, int]]]]:
    """family -> species -> marker -> 0/1; and (family,genus) for non-empty genus."""
    fam: dict[str, dict[str, dict[str, int]]] = {}
    gen: dict[tuple[str, str], dict[str, dict[str, int]]] = {}
    for _, r in table.iterrows():
        family, genus, marker, species = r["family"], r["genus"], r["marker"], r["species"]
        succ = int(r["success"])
        fam.setdefault(family, {}).setdefault(species, {})[marker] = succ
        if genus:
            gen.setdefault((family, genus), {}).setdefault(species, {})[marker] = succ
    return fam, gen


def compare_scope(
    statuses: dict[str, dict[str, int]],
    *,
    scope_level: str,
    scope_name: str,
    family: str,
    genus: str,
    n_family_species: int,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    present = [m for m in MARKERS if any(m in sp for sp in statuses.values())]
    for ma, mb in combinations(present, 2):
        cmp = paired_compare(
            statuses, ma, mb,
            min_shared=cfg["min_shared_species"],
            z=cfg["wilson_z"],
            alpha=cfg["mcnemar_alpha"],
        )
        cmp["n_family_species"] = int(n_family_species)
        label = family if scope_level == "family" else f"{family}/{genus}"
        sentence = pair_sentence(label, cmp, genus=genus)
        rows.append({
            "scope_level": scope_level,
            "scope_name": scope_name,
            "family": family,
            "genus": genus,
            **cmp,
            "sentence": sentence,
            "combinations_skipped": "strict_combined_distance not on this branch (mean_min_distance only)",
        })
    return rows


def summarize_family_fixed(
    pair_rows: list[dict[str, Any]],
    family: str,
    *,
    n_family_species: int,
) -> dict[str, Any]:
    """Family recommendation via pair-voting (çift oylaması) on family-level rows only.

    Each clear marker-pair (rbcL–matK, rbcL–ITS, matK–ITS) casts one vote for its
    winner. Genus rows are not merged in — family maps already key by species once,
    so a species cannot vote twice. Tied vote tallies → fark belirsiz.
    """
    fam_pairs = [r for r in pair_rows if r["scope_level"] == "family" and r["family"] == family]
    adequate = [r for r in fam_pairs if r["recommendation"] != "yetersiz veri"]
    clear = [r for r in fam_pairs if r["clear_difference"]]
    n_fam = int(n_family_species)

    def _base(**extra: Any) -> dict[str, Any]:
        return {
            "family": family,
            "n_family_species": n_fam,
            "n_pairs": len(fam_pairs),
            "n_pairs_adequate": len(adequate),
            "n_pairs_clear": len(clear),
            **extra,
        }

    if not fam_pairs:
        return _base(
            recommendation="yetersiz veri",
            n_species_behind=0,
            sentence=f"{family} için karşılaştırılacak marker çifti yok (ailede {tr_num(n_fam)} tür).",
            n_pairs=0, n_pairs_adequate=0, n_pairs_clear=0,
        )
    if not adequate:
        n_behind = max(int(r["n_shared"]) for r in fam_pairs)
        return _base(
            recommendation="yetersiz veri",
            n_species_behind=n_behind,
            sentence=(
                f"{family}da karşılaştırılan çiftlerin hepsinde ortak tür sayısı öneri eşiğinin altında "
                f"(en fazla {share_label(n_behind, n_fam)})."
            ),
        )
    if not clear:
        n_behind = max(int(r["n_shared"]) for r in adequate)
        return _base(
            recommendation="fark belirsiz",
            n_species_behind=n_behind,
            sentence=(
                f"{family}da en az bir çiftte {share_label(n_behind, n_fam)} ortak kümesi var ama "
                f"Holm düzeltmesi sonrası başarı farkı belirgin değil."
            ),
        )
    from collections import Counter
    votes = Counter(r["recommendation"] for r in clear)
    top = votes.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        n_behind = max(int(r["n_shared"]) for r in clear)
        return _base(
            recommendation="fark belirsiz",
            n_species_behind=n_behind,
            sentence=(
                f"{family}da farklı marker çiftleri çelişkili öneriler verdi "
                f"({share_label(n_behind, n_fam)}); fark belirsiz."
            ),
        )
    winner = top[0][0]
    supporting = [r for r in clear if r["recommendation"] == winner]
    best = max(supporting, key=lambda r: abs(r["rate_diff_b_minus_a"] or 0))
    return _base(
        recommendation=winner,
        n_species_behind=int(best["n_shared"]),
        sentence=best["sentence"],
    )


def load_family_species_counts() -> dict[str, int]:
    """Flora species counts per family (denominator for n / total).

    Prefer ``web/public/data/families.json`` (published atlas totals). Fall back to
    aggregating ``group_summary`` species counts only if that file is missing.
    """
    fam_path = WEB_DATA / "families.json"
    if fam_path.exists():
        with open(fam_path, encoding="utf-8") as fh:
            rows = json.load(fh)
        return {str(r["family"]): int(r["species"]) for r in rows}
    gs = pd.read_csv(GROUP_SUMMARY)
    # Upper bound from analysed groups (under-counts flora for unanalysed families).
    return gs.groupby("family")["species"].max().astype(int).to_dict()


def run_marker_guide(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    gcfg = resolve_guide_cfg(cfg)
    table = load_species_status_table()
    fam_maps, gen_maps = build_status_maps(table)
    family_totals = load_family_species_counts()

    pair_rows: list[dict[str, Any]] = []
    for family, statuses in sorted(fam_maps.items()):
        n_fam = int(family_totals.get(family, 0))
        pair_rows.extend(compare_scope(
            statuses, scope_level="family", scope_name=family,
            family=family, genus="", n_family_species=n_fam, cfg=gcfg,
        ))
    for (family, genus), statuses in sorted(gen_maps.items()):
        n_fam = int(family_totals.get(family, 0))
        pair_rows.extend(compare_scope(
            statuses, scope_level="genus", scope_name=f"{family}/{genus}",
            family=family, genus=genus, n_family_species=n_fam, cfg=gcfg,
        ))

    apply_holm_to_pairs(
        pair_rows,
        min_shared=gcfg["min_shared_species"],
        alpha=gcfg["mcnemar_alpha"],
    )

    pairs_df = pd.DataFrame(pair_rows)
    summaries = [
        summarize_family_fixed(pair_rows, f, n_family_species=int(family_totals.get(f, 0)))
        for f in sorted(fam_maps)
    ]
    summary_df = pd.DataFrame(summaries)

    RESULTS.mkdir(parents=True, exist_ok=True)
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    pairs_df.to_csv(RESULTS / "marker_guide.csv", index=False)
    summary_df.to_csv(RESULTS / "marker_guide_families.csv", index=False)

    n_rec = int((summary_df["recommendation"].isin(MARKERS)).sum())
    n_yetersiz = int((summary_df["recommendation"] == "yetersiz veri").sum())
    n_belirsiz = int((summary_df["recommendation"] == "fark belirsiz").sum())
    n_holm_tests = int(pairs_df["mcnemar_p_holm"].notna().sum()) if len(pairs_df) else 0

    def _jsonable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_jsonable(v) for v in obj]
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if hasattr(obj, "item"):
            try:
                return _jsonable(obj.item())
            except Exception:
                return obj
        return obj

    payload = {
        "generated_from": "pipeline/barcode_atlas/marker_guide.py",
        "criterion": "strict species-level (all evaluated sequences must succeed)",
        "pairing": "same species evaluated in both markers",
        "min_shared_species": gcfg["min_shared_species"],
        "multiple_comparison": (
            "Holm–Bonferroni across all family/genus pair tests with n ≥ min_shared_species "
            "(FWER control; preferred over BH/FDR because recommendations are actionable claims)"
        ),
        "combinations": (
            "skipped: this branch has mean_min_distance combinations only; "
            "strict_combined_distance is not merged"
        ),
        "caveat": (
            "Sonuçlar bu veri setine aittir: aile/cins içi eşiksiz en-yakın-komşu, "
            "halka açık kayıtlar, yanlış adlandırılmış kayıt olasılığı. Evrensel kural değildir."
        ),
        "counts": {
            "families": int(len(summary_df)),
            "recommended": n_rec,
            "yetersiz_veri": n_yetersiz,
            "fark_belirsiz": n_belirsiz,
            "pair_rows": int(len(pairs_df)),
            "holm_tests": n_holm_tests,
            "genus_scopes": int(pairs_df.loc[pairs_df.scope_level == "genus", "scope_name"].nunique()) if len(pairs_df) else 0,
        },
        "families": _jsonable(summary_df.to_dict(orient="records")),
        "pairs": _jsonable(pairs_df.to_dict(orient="records")),
    }
    with open(WEB_DATA / "marker_guide.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, allow_nan=False)

    return {
        "n_families": int(len(summary_df)),
        "n_recommended": n_rec,
        "n_yetersiz": n_yetersiz,
        "n_belirsiz": n_belirsiz,
        "n_holm_tests": n_holm_tests,
        "examples": summary_df.head(3).to_dict(orient="records"),
        "summary": summary_df,
        "pairs": pairs_df,
    }


def main(config_path: str | Path | None = None) -> None:
    path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "config.yaml"
    summary = run_marker_guide(load_config(path))
    print(
        f"[marker_guide] families={summary['n_families']} "
        f"recommended={summary['n_recommended']} "
        f"yetersiz={summary['n_yetersiz']} belirsiz={summary['n_belirsiz']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
