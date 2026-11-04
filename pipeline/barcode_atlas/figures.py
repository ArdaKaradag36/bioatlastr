"""Publication-style PNG figures from the CSV summaries in results/ (no hard-coded numbers)."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .paths import RESULTS, WEB_DATA  # noqa: E402

COL = {"zero": "#b9b4ab", "one": "#e0b252", "two": "#2f7d57", "ok": "#2f7d57", "amb": "#e0b252", "fail": "#c0392b"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})


def _label() -> str:
    meta = WEB_DATA / "meta.json"
    return json.loads(meta.read_text())["aligner_label"] if meta.exists() else ""


def make_figures() -> list[str]:
    out_dir = RESULTS / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    aln = _label()
    made: list[str] = []

    # 1 coverage per marker -------------------------------------------------------------
    cov = pd.read_csv(RESULTS / "coverage_by_marker.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    left = np.zeros(len(cov))
    for col, name, c in (("species_0", "No sequence", COL["zero"]), ("species_1", "1 sequence", COL["one"]),
                         ("species_2plus", "2+ sequences", COL["two"])):
        ax.barh(cov["marker"], cov[col], left=left, color=c, label=name)
        left += cov[col].to_numpy()
    for i, r in cov.iterrows():
        ax.text(r["species_total"] * 1.01, i, f"{r['species_2plus'] + r['species_1']:,} / {r['species_total']:,}", va="center", fontsize=8)
    ax.set_xlabel("Number of Turkish species (WCVP)")
    ax.set_title("Barcode coverage of the Turkish flora by marker")
    ax.legend(loc="lower right", frameon=False)
    ax.set_xlim(0, cov["species_total"].max() * 1.18)
    fig.tight_layout()
    p = out_dir / "fig1_coverage_by_marker.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    made.append(p.name)

    # 2 discrimination: markers and combinations --------------------------------------------
    comb = pd.read_csv(RESULTS / "discrimination_combinations.csv")
    comb = comb[comb["scope"] == "ALL"].sort_values(["n_markers", "combination"])
    if len(comb):
        fig, ax = plt.subplots(figsize=(7, 4.2))
        n = comb["species_evaluated"].replace(0, np.nan)
        x = np.arange(len(comb))
        ok, amb, fail = (comb[k] / n * 100 for k in ("success", "ambiguous", "fail"))
        ax.bar(x, ok, color=COL["ok"], label="Success")
        ax.bar(x, amb, bottom=ok, color=COL["amb"], label="Ambiguous (tie)")
        ax.bar(x, fail, bottom=ok + amb, color=COL["fail"], label="Fail")
        for i, (_, r) in enumerate(comb.iterrows()):
            ax.text(i, 101, f"n={int(r['species_evaluated']):,}", ha="center", fontsize=8)
        ax.set_xticks(x, comb["combination"].str.replace("+", "+\n"), fontsize=9)
        ax.set_ylim(0, 110)
        ax.set_ylabel("% of evaluated species")
        ax.set_title(f"Species discrimination (nearest neighbour), alignment: {aln}")
        ax.legend(loc="lower left", frameon=False, ncol=3, fontsize=8)
        fig.tight_layout()
        p = out_dir / "fig2_discrimination_markers_combinations.png"
        fig.savefig(p, dpi=200)
        plt.close(fig)
        made.append(p.name)

    # 3 family-level success ----------------------------------------------------------------
    fm = pd.read_csv(RESULTS / "discrimination_by_family_marker.csv")
    fm = fm[fm["sequences_evaluated"] > 0]
    top = fm.groupby("family")["sequences_evaluated"].sum().sort_values(ascending=False).head(15).index
    pv = fm[fm["family"].isin(top)].pivot(index="family", columns="marker", values="success_rate").reindex(top) * 100
    if len(pv):
        fig, ax = plt.subplots(figsize=(7, 5.5))
        w = 0.8 / len(pv.columns)
        y = np.arange(len(pv))
        for k, m in enumerate(pv.columns):
            ax.barh(y + k * w, pv[m].fillna(0), height=w, label=m)
        ax.set_yticks(y + w * (len(pv.columns) - 1) / 2, pv.index)
        ax.invert_yaxis()
        ax.set_xlabel("Best-close-match success rate (%)")
        ax.set_title("Discrimination success in the 15 families with most evaluated sequences")
        ax.legend(frameon=False)
        fig.tight_layout()
        p = out_dir / "fig3_family_success.png"
        fig.savefig(p, dpi=200)
        plt.close(fig)
        made.append(p.name)

    # 4 data gaps by family ---------------------------------------------------------------
    sp = pd.read_csv(RESULTS / "species_marker_counts.csv")
    mcols = [c for c in sp.columns if c.startswith("n_")]
    sp["any"] = sp[mcols].sum(axis=1) > 0
    g = sp.groupby("family").agg(total=("species", "size"), with_data=("any", "sum"), endemic=("endemic", "sum"))
    g["no_data"] = g["total"] - g["with_data"]
    g = g.sort_values("total", ascending=False).head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(g.index, g["with_data"], color=COL["two"], label="With sequence")
    ax.barh(g.index, g["no_data"], left=g["with_data"], color=COL["zero"], label="No sequence (data gap)")
    ax.set_xlabel("Number of species")
    ax.set_title("Data gaps in the 20 largest families")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    p = out_dir / "fig4_data_gaps_families.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    made.append(p.name)

    # 5 nearest-relative distance distribution ----------------------------------------------
    rel_path = RESULTS / "nearest_relatives.csv"
    rel = pd.read_csv(rel_path)
    rel = rel[rel["rank"] == 1] if len(rel) else rel
    if len(rel):
        fig, ax = plt.subplots(figsize=(7, 4))
        bins = np.linspace(0, 0.2, 41)
        for m, d in rel.groupby("marker"):
            ax.hist(np.clip(d["p_distance"], 0, 0.2), bins=bins, histtype="step", linewidth=1.6, label=f"{m} (n={len(d):,}; {np.mean(d['p_distance'] == 0) * 100:.0f}% at 0)")
        ax.set_xlabel("p-distance to the nearest other species (capped at 0.2)")
        ax.set_ylabel("Number of species")
        ax.set_title("How close is the nearest relative?")
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        p = out_dir / "fig5_nearest_relative_distance.png"
        fig.savefig(p, dpi=200)
        plt.close(fig)
        made.append(p.name)
    return made
